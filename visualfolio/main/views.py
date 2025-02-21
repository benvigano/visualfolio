import os
import json
import datetime
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.shortcuts import render
from django.views import View
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.contrib import messages
from django.db import transaction
from django.views.generic import TemplateView, ListView
from django.db.models import Count

from django.conf import settings

from main.utils.market_data import get_prices_daily
from main.services.stateless.visualization import (
    generate_streamgraph,
    hex_to_hsl_components,
    generate_relative_streamgraph,
    generate_assets_donut,
    generate_accounts_donut,
    generate_accounts_country_donut,
    generate_earnings_barplot,
)
from main.services.stateless.calculation import BalanceCalculationService

from .models import Transaction, Account, AccountItem, Asset, Trade, BalanceHistory, AssetClass


class CustomErrorView(View):
    def get(self, request, *args, **kwargs):
        return redirect("home")

    def post(self, request, *args, **kwargs):
        return redirect("home")


class LoginView(View):
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Render the login form with pre-filled credentials
        return render(
            request,
            "main/login.html",
        )

    def post(self, request, *args, **kwargs):
        User = get_user_model()

        # Get credentials from POST data
        username_post = request.POST.get("username")
        password_post = request.POST.get("password")

        try:
            # Get user by username
            user = User.objects.get(username=username_post)
            
            # Check password
            if user.check_password(password_post):
                # Log the user in
                login(request, user)
                return redirect("home")
            else:
                messages.error(request, "Invalid credentials")
        except User.DoesNotExist:
            messages.error(request, "Invalid credentials")
        
        return render(request, "main/login.html")


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "main/home.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get user's AccountItems
        accounts_items = (
            AccountItem.objects.filter(account__user=self.request.user)
            .select_related("asset__asset_class")
            .values("account", "asset", "balance", "asset__is_liquid")
        )
        accounts_items_df = pd.DataFrame(list(accounts_items))

        # Calculate AccountItems' current values
        accounts_items_df["current_price"] = accounts_items_df.apply(
            lambda x: get_prices_daily(
                x["asset"],
                settings.BASE_CURRENCY["code"],
                datetime.datetime.now().date(),
            ),
            axis=1,
        )
        accounts_items_df["current_value"] = (
                accounts_items_df["current_price"] * accounts_items_df["balance"]
        )

        # Calculate totals
        total_asset_value = accounts_items_df["current_value"].sum()
        liquid_asset_value = accounts_items_df[accounts_items_df["asset__is_liquid"]][
            "current_value"
        ].sum()

        # Get users BalanceHistories
        balance_histories = BalanceHistory.objects.filter(
            account_item__account__user=self.request.user
        ).values(
            "account_item__account__institution_name",
            "account_item__asset",
            "account_item__asset__asset_class__name",
            "account_item__asset__asset_class__color",
            "balance",
            "date",
        )
        balance_histories_df = pd.DataFrame(list(balance_histories))
        balance_histories_df.rename(
            columns={
                "account_item__account__institution_name": "account",
                "account_item__asset": "asset",
                "account_item__asset__asset_class__name": "asset_class",
                "account_item__asset__asset_class__color": "asset_class_color",
            },
            inplace=True,
        )

        balance_histories_df["account_item"] = (
                balance_histories_df["account"] + " - " + balance_histories_df["asset"]
        )

        # Get user's Transactions
        transactions = Transaction.objects.filter(account__user=self.request.user)

        # Calculate value history from BalanceHistory
        timespan_end = balance_histories_df["date"].max()
        timespan_start = balance_histories_df["date"].min()
        timespan = timespan_end - timespan_start

        # Collect prices by asset
        price_dfs = []
        for asset in balance_histories_df['asset'].unique():
            asset_daily_prices = get_prices_daily(
                instrument=asset,
                quote_currency=settings.BASE_CURRENCY["code"],
                timespan_end=timespan_end,
                timespan=timespan
            )
            temp_df = asset_daily_prices.reset_index().rename(columns={asset: 'price'})
            temp_df['asset'] = asset
            price_dfs.append(temp_df)

        # Combine all price dfs
        combined_prices_df = pd.concat(price_dfs, ignore_index=True)

        # Merge
        balance_histories_df = balance_histories_df.merge(combined_prices_df, on=['date', 'asset'], how='left')

        balance_histories_df["value"] = (
                balance_histories_df["price"] * balance_histories_df["balance"]
        )

        pivot_total_value = (
            balance_histories_df.groupby("date", as_index=False)["value"]
            .sum()
            .reset_index()
        )

        # Calculate relative balance history accounting for Transactions only
        transactions_by_date = {}
        for txn in transactions:
            transaction_date = txn.datetime.date()
            transactions_by_date.setdefault(transaction_date, []).append(txn)

        # Generate date range (from end to start)
        date_list = []
        current_date = min(t.datetime.date() for t in transactions)
        while current_date <= datetime.datetime.now().date():
            date_list.append(current_date)
            current_date += datetime.timedelta(days=1)

        data = list()
        value = 0

        for current_date in date_list:
            if current_date in transactions_by_date:

                unique_assets = set(
                    [t.asset for t in transactions_by_date[current_date]]
                )
                assets_price_mapping = {}
                for a in unique_assets:
                    assets_price_mapping[a] = get_prices_daily(
                        a.code, settings.BASE_CURRENCY["code"], current_date
                    )

                for txn in transactions_by_date[current_date]:
                    asset_price = assets_price_mapping[txn.asset][0]
                    transaction_value = asset_price * txn.amount
                    value += transaction_value

            data.append({"date": current_date, "rel_value_transactions_only": value})

        relative_balance_history_transactions_only = pd.DataFrame(data)

        # Group values by asset class
        grouping_field = "asset_class"
        grouped = balance_histories_df.groupby(
            ["date", grouping_field], as_index=False
        ).agg({"value": "sum"})
        pivot = grouped.pivot(
            index="date", columns=grouping_field, values="value"
        ).reset_index()

        # Generate themed color map for stramgraph
        color_map = (
            balance_histories_df[["asset_class", "asset_class_color"]]
            .drop_duplicates()
            .set_index("asset_class", drop=True)
        )
        color_map["hsl_dark_background"] = color_map["asset_class_color"].apply(
            lambda x: f"hsl({hex_to_hsl_components(x)[0]}, 75%, 45%)"
        )
        color_map["hsl_light_background"] = color_map["asset_class_color"].apply(
            lambda x: f"hsl({hex_to_hsl_components(x)[0]}, 96%, 66%)"
        )

        groups = list(filter(lambda x: x != "date", pivot.columns))

        # Set transacitonal asset (or asset class) as first to improve chart readability
        if grouping_field == "asset":
            first_group = settings.BASE_CURRENCY["code"]
            other_groups = list(filter(lambda x: x != first_group, groups))
            groups = [first_group] + other_groups

        elif grouping_field == "asset_class":
            first_group = "Fiat Currencies"
            other_groups = list(filter(lambda x: x != first_group, groups))
            
            # Sort the remaining asset classes by ascending volatility to improve plot readability
            volatility_mapping = {
                asset_class.name: asset_class.volatility_index
                for asset_class in AssetClass.objects.filter(name__in=other_groups)
            }

            other_groups = sorted(
                other_groups,
                key=lambda group: volatility_mapping.get(group)
            )
            
            groups = [first_group] + other_groups

        else:
            first_group = groups[0]
            pass

        # Calculate relative balance history accounting for investment P/L only
        # by subtracting transaction balance history from total balance history
        df = pivot_total_value.merge(
            relative_balance_history_transactions_only, on="date"
        ).merge(pivot, on="date")
        df["rel_value_capital_gain_only"] = (
                df["value"] - df["rel_value_transactions_only"]
        )

        # Invert relative balance history accounting for investment P/L only
        df["inverted_rel_value_capital_gain_only"] = -df["rel_value_capital_gain_only"]

        # Adjust y so the thickness at each x matches the tot user value at that time
        y0 = df.at[0, "inverted_rel_value_capital_gain_only"]
        tot_user_value_0 = df.at[0, "value"]
        target_y0 = df.at[0, "rel_value_transactions_only"] - tot_user_value_0
        delta_y0 = target_y0 - y0
        df["inverted_rel_value_capital_gain_only"] += delta_y0

        # Calculate internal boundaries of streamgraph
        for i in range(len(groups[:-1])):
            if i == 0:
                previous_boundary = "rel_value_transactions_only"
            else:
                previous_boundary = f"{groups[i - 1]}_{groups[i]}_internal_boundary"

            col = f"{groups[i]}_{groups[i + 1]}_internal_boundary"
            df[col] = df[previous_boundary] - df[groups[i]]

        last_group_name = groups[-1]

        # Pass context data to template
        context["graph"] = generate_streamgraph(
            df,
            self.request.theme,
            settings.BASE_CURRENCY["symbol"],
            color_map,
            last_group_name,
        )
        context["total_asset_value"] = total_asset_value
        context["liquid_asset_value"] = liquid_asset_value
        context["base_currency"] = settings.BASE_CURRENCY["symbol"]

        return context


class AssetsView(LoginRequiredMixin, TemplateView):
    template_name = "main/assets.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get user's BalanceHistory
        balance_histories = BalanceHistory.objects.filter(
            account_item__account__user=self.request.user
        ).values(
            "account_item__account",
            "account_item__asset",
            "account_item__asset__asset_class__name",
            "account_item__asset__asset_class__color",
            "balance",
            "date",
        )
        balance_histories_df = pd.DataFrame(list(balance_histories))
        balance_histories_df.rename(
            columns={
                "account_item__account": "account",
                "account_item__asset": "asset",
                "account_item__asset__asset_class__name": "asset_class",
                "account_item__asset__asset_class__color": "asset_class_color",
            },
            inplace=True,
        )

        # Calculate value history from BalanceHistory
        timespan_end = balance_histories_df["date"].max()
        timespan_start = balance_histories_df["date"].min()
        timespan = timespan_end - timespan_start

        # Collect prices by asset
        price_dfs = []
        for asset in balance_histories_df['asset'].unique():
            asset_daily_prices = get_prices_daily(
                instrument=asset,
                quote_currency=settings.BASE_CURRENCY["code"],
                timespan_end=timespan_end,
                timespan=timespan
            )
            temp_df = asset_daily_prices.reset_index().rename(columns={asset: 'price'})
            temp_df['asset'] = asset
            price_dfs.append(temp_df)

        # Combine all price dfs
        combined_prices_df = pd.concat(price_dfs, ignore_index=True)

        # Merge
        balance_histories_df = balance_histories_df.merge(combined_prices_df, on=['date', 'asset'], how='left')

        balance_histories_df["value"] = (
                balance_histories_df["price"] * balance_histories_df["balance"]
        )

        # Sum values of items of the same asset class
        grouping_field = "asset_class"
        grouped = balance_histories_df.groupby(
            ["date", grouping_field], as_index=False
        ).agg({"value": "sum"})
        pivot = grouped.pivot(
            index="date", columns=grouping_field, values="value"
        ).reset_index()

        # Get user's AccountItems
        accounts_items = (
            AccountItem.objects.filter(account__user=self.request.user)
            .select_related("asset__asset_class")
            .values(
                "account",
                "asset",
                "asset__name",
                "balance",
                "asset__asset_class__name",
                "asset__asset_class__color",
            )
        )
        accounts_items_df = pd.DataFrame(list(accounts_items))
        accounts_items_df.rename(
            columns={
                "asset__asset_class__name": "asset_class",
                "asset__asset_class__color": "color",
                "asset__name": "name",
            },
            inplace=True,
        )

        # Calculate current values
        accounts_items_df["current_price"] = accounts_items_df.apply(
            lambda x: get_prices_daily(
                x["asset"],
                settings.BASE_CURRENCY["code"],
                datetime.datetime.now().date(),
            ),
            axis=1,
        )
        accounts_items_df["current_value"] = (
                accounts_items_df["current_price"] * accounts_items_df["balance"]
        )
        accounts_items_df.sort_values("asset_class", inplace=True)

        # Group by asset class
        d = {
            "asset_class_tot_value": ("current_value", "sum"),
            "color": ("color", "first"),
        }
        asset_class_sums = (
            accounts_items_df.groupby(["asset_class"]).agg(**d).reset_index()
        )
        accounts_items_df = accounts_items_df.merge(
            asset_class_sums.drop(columns=["color"]), on="asset_class"
        )
        asset_class_sums["allocation"] = (
                                                 asset_class_sums["asset_class_tot_value"]
                                                 / asset_class_sums["asset_class_tot_value"].sum()
                                         ) * 100

        # Generate themed colors for each asset class
        asset_class_sums["hsl_dark_background"] = asset_class_sums["color"].apply(
            lambda x: f"hsl({hex_to_hsl_components(x)[0]}, 75%, 45%)"
        )
        asset_class_sums["hsl_light_background"] = asset_class_sums["color"].apply(
            lambda x: f"hsl({hex_to_hsl_components(x)[0]}, 96%, 66%)"
        )

        d = {
            "asset_class_tot_value": ("asset_class_tot_value", "first"),
            "asset_class": ("asset_class", "first"),
            "color": ("color", "first"),
            "tot_current_value": ("current_value", "sum"),
            "tot_balance": ("balance", "sum"),
        }
        assets = accounts_items_df.groupby(["asset", "name"]).agg(**d).reset_index()

        # Generate themed colors for each asset
        assets["hsl_dark_background"] = assets["color"].apply(
            lambda x: f"hsl({hex_to_hsl_components(x)[0]}, 75%, 45%)"
        )
        assets["hsl_light_background"] = assets["color"].apply(
            lambda x: f"hsl({hex_to_hsl_components(x)[0]}, 96%, 66%)"
        )
        assets["allocation"] = (
                                       assets["tot_current_value"] / assets["tot_current_value"].sum()
                               ) * 100

        tot_value = assets["tot_current_value"].sum()

        # Pass data to template
        context["donut"] = generate_assets_donut(
            assets, self.request.theme, tot_value, settings.BASE_CURRENCY["symbol"]
        )
        context["assets"] = (
            assets.sort_values("tot_current_value", ascending=False)
            .drop(columns=["asset_class_tot_value"])
            .to_dict("records")
        )
        context["asset_classes"] = asset_class_sums.sort_values(
            "asset_class_tot_value", ascending=False
        ).to_dict("records")
        context["relative_streamgraph"] = generate_relative_streamgraph(
            pivot, asset_class_sums, self.request.theme
        )
        context["base_currency"] = settings.BASE_CURRENCY["symbol"]

        return context


class AccountsView(LoginRequiredMixin, TemplateView):
    template_name = "main/accounts.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        def theme_account_color(hex_color, s_change, l_change):
            """
            Style account color to match theme
            """
            h, s, l = hex_to_hsl_components(hex_color)
            s = max(0, min(100, s + (s_change * 100)))
            l = max(0, min(100, l + (l_change * 100)))
            return f"hsl({h}, {s}%, {l}%)"

        # Get user's AccountItems
        accounts_items = AccountItem.objects.filter(
            account__user=self.request.user
        ).values(
            "account__institution_name",
            "account__color",
            "account__country",
            "balance",
            "asset",
        )
        accounts_items_df = pd.DataFrame(list(accounts_items))
        accounts_items_df.rename(
            columns={
                "account__institution_name": "account",
                "account__color": "account_color",
                "account__country": "account_country",
            },
            inplace=True,
        )

        # Calculate current value of AccountItems
        accounts_items_df["current_price"] = accounts_items_df.apply(
            lambda x: get_prices_daily(
                x["asset"],
                settings.BASE_CURRENCY["code"],
                datetime.datetime.now().date(),
            ),
            axis=1,
        )
        accounts_items_df["current_value"] = (
                accounts_items_df["current_price"] * accounts_items_df["balance"]
        )

        # Style colors based on theme
        accounts_items_df["hsl_dark_background"] = accounts_items_df[
            "account_color"
        ].apply(lambda x: theme_account_color(x, -0.05, -0.10))
        accounts_items_df["hsl_light_background"] = accounts_items_df[
            "account_color"
        ].apply(lambda x: theme_account_color(x, 0.05, 0.10))

        # Calculate total asset value for each account
        d = {
            "account_tot_value": ("current_value", "sum"),
            "account_country": ("account_country", "first"),
            "hsl_dark_background": ("hsl_dark_background", "first"),
            "hsl_light_background": ("hsl_light_background", "first"),
        }
        account_sums = accounts_items_df.groupby(["account"]).agg(**d).reset_index()
        account_sums["account_value_perc"] = (
                                                     account_sums["account_tot_value"] / account_sums[
                                                 "account_tot_value"].sum()
                                             ) * 100

        # Calculate transaction volume data

        # Get user's Transactions
        transactions = Transaction.objects.filter(
            account__user=self.request.user
        ).values("account__institution_name", "amount", "datetime")
        transactions_df = pd.DataFrame(list(transactions))

        if not transactions_df.empty:
            transactions_df["date"] = pd.to_datetime(
                transactions_df["datetime"]
            ).dt.date

            grouped = (
                transactions_df.groupby(["account__institution_name", "date"])
                .agg(
                    total_vol=("amount", lambda x: x.abs().sum()),
                    total_incoming=("amount", lambda x: x[x > 0].sum()),
                    total_outgoing=("amount", lambda x: -x[x < 0].sum()),
                )
                .reset_index()
            )

            # Calculate monthly averages
            daily_agg = (
                grouped.groupby("account__institution_name")
                .agg(
                    avg_daily_volume=("total_vol", "mean"),
                    avg_daily_incoming=("total_incoming", "mean"),
                    avg_daily_outgoing=("total_outgoing", "mean"),
                )
                .reset_index()
            )
            daily_agg["avg_monthly_volume"] = daily_agg["avg_daily_volume"] * 30
            daily_agg["avg_monthly_incoming"] = daily_agg["avg_daily_incoming"] * 30
            daily_agg["avg_monthly_outgoing"] = daily_agg["avg_daily_outgoing"] * 30

            account_sums = (
                account_sums.merge(
                    daily_agg[
                        [
                            "account__institution_name",
                            "avg_monthly_volume",
                            "avg_monthly_incoming",
                            "avg_monthly_outgoing",
                        ]
                    ],
                    left_on="account",
                    right_on="account__institution_name",
                    how="left",
                )
                .drop("account__institution_name", axis=1)
                .fillna(0)  # If no transactions are linked to the account, fill with 0
            )

        # If the user has no transactions at all, set all to 0
        else:
            account_sums["avg_monthly_volume"] = 0
            account_sums["avg_monthly_incoming"] = 0
            account_sums["avg_monthly_outgoing"] = 0

        # Sort by volume
        account_sums.sort_values("account_tot_value", ascending=False, inplace=True)

        accounts_items_df.drop(
            columns=["balance", "asset", "current_price"], inplace=True
        )

        # Generate accounts donut plot
        d = {
            "account_total_value": ("current_value", "sum"),
            "hsl_dark_background": ("hsl_dark_background", "first"),
            "hsl_light_background": ("hsl_light_background", "first"),
            "country": ("account_country", "first"),
        }
        accounts_df = accounts_items_df.groupby(["account"]).agg(**d).reset_index()
        accounts_donut = generate_accounts_donut(
            accounts_df, self.request.theme, settings.BASE_CURRENCY["symbol"]
        )

        # Generate account countries donut plot
        d = {"account_total_value": ("current_value", "sum")}
        accounts_country_df = (
            accounts_items_df.groupby(["account_country"]).agg(**d).reset_index()
        )
        accounts_country_donut = generate_accounts_country_donut(
            accounts_country_df, self.request.theme, settings.BASE_CURRENCY["symbol"]
        )

        context["accounts_donut"] = accounts_donut
        context["accounts_country_donut"] = accounts_country_donut
        context["accounts_table"] = account_sums.to_dict("records")
        context["base_currency"] = settings.BASE_CURRENCY["symbol"]

        return context


class TransactionsView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "main/transactions.html"
    login_url = "login"
    context_object_name = "transactions"

    def get_queryset(self):
        # Get user's transactions (prefetch related fields)
        return (
            Transaction.objects.filter(account__user=self.request.user)
            .select_related("asset", "account")
            .order_by("-datetime")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = context["transactions"]

        # Get all assets that appear in transactions, sorted by descending txn count
        context["assets"] = (
            Asset.objects.filter(transaction__account__user=self.request.user)
            .annotate(transaction_count=Count("transaction"))
            .order_by("-transaction_count")
            .distinct()
        )

        # Get all accounts sorted by descending txn count
        context["accounts"] = (
            Account.objects.filter(user=self.request.user)
            .annotate(transaction_count=Count("transaction"))
            .order_by("-transaction_count")
            .distinct()
        )

        # Format transactions account badge color and string
        formatted_transactions = []
        for txn in transactions:
            txn.formatted_amount = "{:,.2f}".format(abs(txn.amount))
            txn.asset.symbol = getattr(txn.asset, "symbol", txn.asset.name)

            h, s, l = hex_to_hsl_components(txn.account.color)
            txn.hsl_dark_background = f"hsl({h}, 50%, 29%)"
            txn.hsl_dark_text = f"hsl({h}, 100%, 85%)"
            txn.hsl_light_background = f"hsl({h}, 93%, 85%)"
            txn.hsl_light_text = f"hsl({h}, 68%, 37%)"

            formatted_transactions.append(txn)

        context["transactions"] = formatted_transactions
        context["today"] = datetime.datetime.now().date()
        context["base_currency"] = settings.BASE_CURRENCY["symbol"]

        return context


class EarningsView(LoginRequiredMixin, TemplateView):
    template_name = "main/earnings.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        transactions = Transaction.objects.filter(
            amount__gt=0, account__user=self.request.user
        )

        # Convert transactions to DataFrame
        data = transactions.values("datetime", "entity", "amount")
        df = pd.DataFrame(data)

        # Generate colors for each unique entity
        unique_entities = df["entity"].unique()
        colors_map = {
            "light": {},
            "dark": {}
        }
        
        # Generate a different hue for each entity, evenly distributed
        hue_step = 360 / (len(unique_entities) or 1)  # Avoid division by zero
        for idx, entity in enumerate(unique_entities):
            hue = int(idx * hue_step)
            # Light theme: high saturation and lightness
            colors_map["light"][entity] = f"hsl({hue}, 88%, 60%)"
            # Dark theme: lower saturation and lightness for better contrast
            colors_map["dark"][entity] = f"hsl({hue}, 55%, 45%)"

        df["color"] = df["entity"].map(colors_map[self.request.theme])

        # Ensure 'datetime' is a datetime object
        df["datetime"] = pd.to_datetime(df["datetime"])

        # Extract the month from datetime
        df["month"] = df["datetime"].dt.to_period("M").dt.to_timestamp()

        # Group by 'month' and 'entity' with sum of 'amount'
        grouped_df = (
            df.groupby(["month", "entity", "color"])["amount"].sum().reset_index()
        )

        # Calculate the start_month for x-axis alignment
        start_month = grouped_df["month"].min()

        # Initialize a list to store trend data
        trend_data = []
        entities = grouped_df["entity"].unique()
        total_volume = grouped_df["amount"].sum()

        for entity in entities:
            df_entity = grouped_df[grouped_df["entity"] == entity].copy()

            color = df_entity["color"].tolist()[0]

            # Compute 'x' as months since start_month
            df_entity["x"] = (df_entity["month"].dt.year - start_month.year) * 12 + (
                    df_entity["month"].dt.month - start_month.month
            )

            x = df_entity["x"].values
            y = df_entity["amount"].values

            # Linear regression to find m
            if len(x) > 1:
                m, _ = np.polyfit(x, y, 1)
            else:
                m, _ = 0, y[0]  # Default values if not enough data points

            total_volume_entity = df_entity["amount"].sum()
            mean_y = y.mean() if len(y) > 0 else 0

            monthly_percentage_increase = (m / mean_y) * 100 if mean_y > 0 else 0
            yearly_percentage_increase = monthly_percentage_increase * 12

            trend_data.append(
                {
                    "entity": entity,
                    "delta_monthly": m,
                    "delta_yearly": m * 12,
                    "delta_monthly_percentage": monthly_percentage_increase,
                    "delta_yearly_percentage": yearly_percentage_increase,
                    "total_volume_entity": total_volume_entity,
                    "total_volume_entity_percentage": (
                                                              total_volume_entity / total_volume
                                                      )
                                                      * 100,
                    "color": color,
                }
            )

        # Create DataFrame for trend data
        df_trends = pd.DataFrame(trend_data).sort_values(
            "total_volume_entity_percentage", ascending=False
        )
        context["earnings_sources"] = df_trends.to_dict("records")
        context["graph"] = generate_earnings_barplot(
            grouped_df, self.request.theme, settings.BASE_CURRENCY["symbol"]
        )
        context["base_currency"] = settings.BASE_CURRENCY["symbol"]

        return context
