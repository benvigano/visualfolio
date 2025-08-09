from __future__ import annotations

import os
import json
import datetime
import logging


from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.cache import cache
from django.db import transaction, connection
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from main.models import (
    Account,
    Asset,
    BalanceHistory,
    Trade,
    Transaction,
)
from main.services.stateless.calculation import BalanceCalculationService


logger = logging.getLogger(__name__)


def initialize_demo_user(user, *, progress_key: str) -> None:
    """
    Populates demo user account with mock data.
    progress_key: used to track the initialization status and provide live updates on the initialize screen.
    """

    def _set_progress(step_key: str) -> None:
        cache.set(progress_key, {"step_key": step_key}, None)

    def _set_error(msg: str) -> None:
        cache.set(progress_key, {"step_key": "error", "message": msg}, None)

    try:
        _set_progress("starting")

        base_path = os.path.join(
            settings.BASE_DIR, "demo", "demo_static_data", "initial_user_data"
        )

        # ------------------------------------------------------------------
        # 1) Accounts and initial balances
        # ------------------------------------------------------------------
        def load_json_data(filename: str):
            with open(os.path.join(base_path, filename), "r", encoding="utf-8") as file:
                return json.load(file)

        accounts_data = load_json_data("demo_accounts.json")
        _set_progress("accounts")
        account_mapping: dict[int, Account] = {}
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

        initial_balances_data = load_json_data("demo_initial_balances.json")
        latest_balances: list[dict] = []

        for entry in initial_balances_data:
            fields = entry.get("fields", {})
            old_account_pk = fields.get("account")
            account = account_mapping.get(old_account_pk)
            asset = get_asset_instance(fields.get("asset"))
            if account and asset:
                latest_balances.append({
                    "account": account,
                    "asset": asset,
                    "balance": fields.get("balance"),
                })

        # ------------------------------------------------------------------
        # 2) Transactions
        # ------------------------------------------------------------------
        transactions_data = load_json_data("demo_transactions.json")
        _set_progress("transactions")
        transaction_instances: list[Transaction] = []

        transaction_datetimes = [
            parse_datetime(entry["fields"].get("datetime")) for entry in transactions_data
        ]
        last_transaction_date = max(transaction_datetimes)
        current_date_utc = datetime.datetime.now(datetime.timezone.utc)
        time_difference = current_date_utc - last_transaction_date
        months_difference = (
            (current_date_utc.year - last_transaction_date.year) * 12
            + (current_date_utc.month - last_transaction_date.month)
        )

        for entry in transactions_data:
            fields = entry.get("fields", {})
            old_account_pk = fields.get("account")
            account = account_mapping.get(old_account_pk)
            asset = get_asset_instance(fields.get("asset"))
            category = fields.get("category")

            entity = fields.get("entity")
            if entity == "FirstName LastName":
                entity = user.first_name

            original_datetime = parse_datetime(fields.get("datetime"))
            shifted_datetime = (
                original_datetime + relativedelta(months=months_difference)
                if category == "earnings"
                else original_datetime + time_difference
            )

            transaction_instances.append(
                Transaction(
                    account=account,
                    entity=entity,
                    amount=fields.get("amount"),
                    datetime=shifted_datetime,
                    asset=asset,
                )
            )

        Transaction.objects.bulk_create(transaction_instances)

        # ------------------------------------------------------------------
        # 3) Trades
        # ------------------------------------------------------------------
        trades_data = load_json_data("demo_trades.json")
        _set_progress("trades")
        trade_instances: list[Trade] = []

        trade_datetimes = [
            parse_datetime(entry["fields"].get("datetime")) for entry in trades_data
        ]
        last_trade_date = max(trade_datetimes)
        time_difference = datetime.datetime.now(datetime.timezone.utc) - last_trade_date

        for entry in trades_data:
            fields = entry.get("fields", {})
            old_account_pk = fields.get("account")
            account = account_mapping.get(old_account_pk)
            asset = get_asset_instance(fields.get("asset"))
            counter = get_asset_instance(fields.get("counter"))
            original_datetime = parse_datetime(fields.get("datetime"))
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

        Trade.objects.bulk_create(trade_instances)

        # ------------------------------------------------------------------
        # 4) Balance history
        # ------------------------------------------------------------------
        _set_progress("balance_history")
        all_transactions = Transaction.objects.filter(account__user=user)
        balance_calculator = BalanceCalculationService()
        start_date = min([t.datetime.date() for t in all_transactions])

        with transaction.atomic():
            all_balance_history_objs: list[BalanceHistory] = []
            items_and_dates: set[tuple] = set()

            current_date = datetime.datetime.now().date()
            for balance_data in latest_balances:
                all_balance_history_objs.append(
                    BalanceHistory(
                        account=balance_data["account"],
                        asset=balance_data["asset"],
                        date=current_date,
                        balance=balance_data["balance"],
                    )
                )
                items_and_dates.add(
                    (
                        balance_data["account"].id,
                        balance_data["asset"].code,
                        current_date,
                    )
                )

            transactions_by_item: dict[tuple, list] = {}
            for balance_data in latest_balances:
                key = (balance_data["account"], balance_data["asset"])
                transactions_by_item[key] = []

            for txn in all_transactions:
                key = (txn.account, txn.asset)
                if key not in transactions_by_item:
                    raise Exception(
                        "Found transaction for account-asset pair that has no initial balance: {key}"
                    )
                transactions_by_item[key].append(txn)

            for (account, asset), transactions in transactions_by_item.items():
                current_balance = next(
                    b["balance"]
                    for b in latest_balances
                    if b["account"] == account and b["asset"] == asset
                )
                balance_history = balance_calculator.generate_balance_history(
                    transactions,
                    current_balance,
                    start_date,
                    datetime.datetime.now().date(),
                )
                for date, balance in balance_history.items():
                    if date != current_date:
                        all_balance_history_objs.append(
                            BalanceHistory(
                                account=account, asset=asset, date=date, balance=balance
                            )
                        )
                        items_and_dates.add((account.id, asset.code, date))

            account_ids = {account_id for account_id, _, _ in items_and_dates}
            asset_codes = {asset_code for _, asset_code, _ in items_and_dates}
            dates = {date for _, _, date in items_and_dates}

            BalanceHistory.objects.filter(
                account_id__in=account_ids,
                asset__code__in=asset_codes,
                date__in=dates,
            ).delete()
            BalanceHistory.objects.bulk_create(all_balance_history_objs)

        # ------------------------------------------------------------------
        # 5) Finalize
        # ------------------------------------------------------------------
        user.last_full_refresh = timezone.now()
        user.save(update_fields=["last_full_refresh"])

        _set_progress("complete")

    except Exception as exc:
        _set_error(str(exc))
        raise

    finally:
        connection.close()
