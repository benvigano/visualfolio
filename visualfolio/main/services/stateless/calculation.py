import datetime 
from collections import OrderedDict
from django.core.exceptions import ValidationError


class BalanceCalculationService:
    def generate_balance_history(self, transactions, current_balance, start_date, end_date):
        transactions_by_date = {}
        for txn in transactions:
            transaction_date = txn.datetime.date()
            transactions_by_date.setdefault(transaction_date, []).append(txn)

        # Generate date range (from end to start)
        reversed_date_list = []
        current_date = end_date
        while current_date >= start_date:
            reversed_date_list.append(current_date)
            current_date -= datetime.timedelta(days=1)

        balance_history = OrderedDict()
        balance = current_balance

        for current_date in reversed_date_list:
            
            balance_history[current_date] = balance
            
            if current_date in transactions_by_date:
                for txn in transactions_by_date[current_date]:
                    amount = txn.amount
                    balance -= amount
                    if balance < 0:
                        raise ValidationError(
                            f"Negative balance for {txn.account} - {txn.asset} on {current_date}"
                        )

        return balance_history
    