import os
import json
import datetime
import pandas as pd
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

from django.conf import settings

from main.utils.market_data import get_prices_daily
from main.utils.demo import generate_realistic_user
from main.services.stateless.visualization import (
    generate_streamgraph,
    hex_to_hsl_components,
)
from main.services.stateless.calculation import BalanceCalculationService

from .models import Transaction, Account, AccountItem, Asset, Trade, BalanceHistory


class Custom404View(View):
    def get(self, request, *args, **kwargs):
        return redirect("home")

    def post(self, request, *args, **kwargs):
        return redirect("home")


class DemoLoginView(View):
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        User = get_user_model()

        # Generate username and name
        username, name = generate_realistic_user()

        # Ensure the username is unique
        while User.objects.filter(username=username).exists():
            username, name = generate_realistic_user()

        # Generate a random password
        password = User.objects.make_random_password()

        # Store credentials in the session
        request.session["demo_username"] = username
        request.session["demo_password"] = password
        request.session["demo_name"] = name

        # Render the login form with pre-filled credentials
        return render(
            request,
            "main/login.html",
            {
                "username": username,
                "password": password,
            },
        )

    def post(self, request, *args, **kwargs):
        User = get_user_model()

        # Retrieve stored credentials from the session
        username = request.session.get("demo_username")
        password = request.session.get("demo_password")
        name = request.session.get("demo_name")

        if not username or not password or not name:
            # Missing credentials in session; redirect to the start demo page
            messages.error(request, "Session expired or invalid. Please try again.")
            return redirect("demo_login")

        # Get credentials from POST data
        username_post = request.POST.get("username")
        password_post = request.POST.get("password")

        # Verify that the POST data matches the stored credentials
        if username != username_post or password != password_post:
            # Credentials do not match; possible tampering
            messages.error(request, "Invalid credentials provided.")
            return redirect("demo_login")

        if User.objects.filter(username=username).exists():
            while True:
                username, name = generate_realistic_user()
                if not User.objects.filter(username=username).exists():
                    break
            password = User.objects.make_random_password()
            request.session["demo_username"] = username
            request.session["demo_password"] = password
            request.session["demo_name"] = name

        # Create the new user
        with transaction.atomic():
            user = User.objects.create_user(
                username=username, password=password, first_name=name
            )
            user.save()

        # Log the user in
        login(request, user)

        # Clear stored credentials from the session
        del request.session["demo_username"]
        del request.session["demo_password"]
        del request.session["demo_name"]

        # Initialize demo user data
        base_path = os.path.join(
            settings.BASE_DIR, "demo", "demo_static_data", "initial_user_data"
        )

        # Mapping of old Account PKs to new instances
        account_mapping = {}

        def load_json_data(filename):
            with open(os.path.join(base_path, filename), "r") as file:
                return json.load(file)

        # Load and create Account instances
        accounts_data = load_json_data("demo_accounts.json")
        for entry in accounts_data:
            old_pk = entry.get("pk")
            fields = entry.get("fields", {})
            account = Account.objects.create(
                user=user,
                institution_name=fields.get("institution_name"),
                country=fields.get("country"),
                nordigen_code=fields.get("nordigen_code"),
                color=fields.get("color"),
            )
            account_mapping[old_pk] = account

        def get_asset_instance(code):
            try:
                return Asset.objects.get(code=code)
            except Asset.DoesNotExist as exc:
                raise Exception(f"Asset with code '{code}' not supported") from exc

        # Load AccountItem data
        account_items_data = load_json_data("demo_accountitems.json")
        account_item_instances = []

        for entry in account_items_data:
            fields = entry.get("fields", {})
            old_account_pk = fields.get("account")
            account = account_mapping.get(old_account_pk)
            asset = get_asset_instance(fields.get("asset"))

            if account and asset:
                account_item_instances.append(
                    AccountItem(
                        account=account, asset=asset, balance=fields.get("balance")
                    )
                )

        # Bulk create AccountItem instances
        AccountItem.objects.bulk_create(account_item_instances)

        # Load Transaction data
        transactions_data = load_json_data("demo_transactions.json")
        transaction_instances = []

        # Extract all txn datetimes and find the last date
        transaction_datetimes = [
            parse_datetime(entry["fields"].get("datetime"))
            for entry in transactions_data
        ]
        last_transaction_date = max(transaction_datetimes)

        # Get the current date and time in UTC
        current_date = datetime.datetime.now(datetime.timezone.utc)

        # Calculate the time difference
        time_difference = current_date - last_transaction_date
        months_difference = (current_date.year - last_transaction_date.year) * 12 + (
            current_date.month - last_transaction_date.month
        )

        for entry in transactions_data:
            fields = entry.get("fields", {})
            old_account_pk = fields.get("account")
            account = account_mapping.get(old_account_pk)
            asset = get_asset_instance(fields.get("asset"))
            category = fields.get("category")

            # Check and replace DEMO_USER_FULL_NAME with user's first name
            entity = fields.get("entity")
            if entity == "FirstName LastName":
                entity = user.first_name

            original_datetime = parse_datetime(fields.get("datetime"))

            # If the txn is earnings:
            if category == "earnings":
                shifted_datetime = original_datetime + relativedelta(
                    months=months_difference
                )
            else:
                shifted_datetime = original_datetime + time_difference

            transaction_instances.append(
                Transaction(
                    account=account,
                    entity=entity,
                    amount=fields.get("amount"),
                    datetime=shifted_datetime,
                    asset=asset,
                )
            )

        # Bulk create Transaction instances
        Transaction.objects.bulk_create(transaction_instances)

        # Load Trade data
        trades_data = load_json_data("demo_trades.json")
        trade_instances = []

        # Extract all trade datetimes and find the latest date
        trade_datetimes = [
            parse_datetime(entry["fields"].get("datetime")) for entry in trades_data
        ]
        last_trade_date = max(trade_datetimes)

        # Get the current date and time in UTC
        current_date = datetime.datetime.now(datetime.timezone.utc)

        # Calculate the time difference
        time_difference = current_date - last_trade_date

        for entry in trades_data:
            fields = entry.get("fields", {})
            old_account_pk = fields.get("account")
            account = account_mapping.get(old_account_pk)
            asset = get_asset_instance(fields.get("asset"))
            counter = get_asset_instance(fields.get("counter"))

            original_datetime = parse_datetime(fields.get("datetime"))
            # Shift the datetime by the time difference
            shifted_datetime = original_datetime + time_difference

            trade_instances.append(
                Trade(
                    account=account,
                    asset=asset,
                    amount=fields.get("amount"),
                    datetime=shifted_datetime,
                    counter=counter,
                )
            )

        # Bulk create Trade instances
        Trade.objects.bulk_create(trade_instances)

        # Generate balance history

        account_items = AccountItem.objects.filter(account__user=user)
        all_transactions = Transaction.objects.filter(account__user=user)

        # Generate account item map
        account_item_map = {(ai.account_id, ai.asset_id): ai for ai in account_items}

        # Prepare AccountItems and group transactions
        transactions_by_item = {account_item: [] for account_item in account_items}
        for txn in all_transactions:
            account_item = account_item_map.get((txn.account_id, txn.asset_id))
            transactions_by_item.setdefault(account_item, []).append(txn)

        # Initialize the balance calculation service
        balance_calculator = BalanceCalculationService()

        start_date = min(
            [t.datetime.date() for txns in transactions_by_item.values() for t in txns]
        )

        with transaction.atomic():
            all_balance_history_objs = []
            items_and_dates = set()

            for item, transactions in transactions_by_item.items():
                current_balance = item.balance

                # Generate balance history
                balance_history = balance_calculator.generate_balance_history(
                    transactions,
                    current_balance,
                    start_date,
                    datetime.datetime.now().date(),
                )

                # Collect BalanceHistory objects and track (item, date) pairs
                for date, balance in balance_history.items():
                    all_balance_history_objs.append(
                        BalanceHistory(account_item=item, date=date, balance=balance)
                    )
                    items_and_dates.add((item.id, date))

            # Prepare filters for bulk deletion
            account_item_ids = {item_id for item_id, _ in items_and_dates}
            dates = {date for _, date in items_and_dates}

            # Bulk delete existing BalanceHistory entries for the items and dates
            BalanceHistory.objects.filter(
                account_item_id__in=account_item_ids, date__in=dates
            ).delete()

            # Bulk create all BalanceHistory records
            BalanceHistory.objects.bulk_create(all_balance_history_objs)

        # Update the user's last_full_refresh timestamp
        user.last_full_refresh = timezone.now()
        user.save()

        return redirect("home")


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "main/home.html"
    login_url = "demo_login"

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

        # Calculate AccountItems' value history
        balance_histories_df["price"] = balance_histories_df.apply(
            lambda x: get_prices_daily(
                instrument=x["asset"],
                quote_currency=settings.BASE_CURRENCY["code"],
                timespan_end=x["date"],
            ).iloc[-1],
            axis=1,
        )
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
            lambda x: f"hsl({hex_to_hsl_components(x)[0]}, 70%, 40%)"
        )
        color_map["hsl_light_background"] = color_map["asset_class_color"].apply(
            lambda x: f"hsl({hex_to_hsl_components(x)[0]}, 93%, 70%)"
        )

        groups = list(filter(lambda x: x != "date", pivot.columns))

        # Set transacitonal asset (or asset class) as first to improve chart readability
        if grouping_field == "asset":
            first_group = settings.BASE_CURRENCY["code"]
            groups = [first_group] + list(filter(lambda x: x != first_group, groups))

        elif grouping_field == "asset_class":
            first_group = "Fiat Currencies"
            groups = [first_group] + list(filter(lambda x: x != first_group, groups))

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
    login_url = "demo_login"


class AccountsView(LoginRequiredMixin, TemplateView):
    template_name = "main/accounts.html"
    login_url = "demo_login"


class EarningsView(LoginRequiredMixin, TemplateView):
    template_name = "main/earnings.html"
    login_url = "demo_login"


class TransactionsView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "main/transactions.html"
    login_url = "demo_login"
    context_object_name = "transactions"
