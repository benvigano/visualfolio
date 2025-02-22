from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, ValidationError
from django.conf import settings
from django.db import transaction
from django.db.models import Count


from .constants import COUNTRY_CHOICES


'''
<< Static models >>
'''

class AssetClass(models.Model):
    name = models.CharField(max_length=63, primary_key=True)
    color = models.CharField(max_length=7)
    volatility_index = models.FloatField()


class Asset(models.Model):
    code = models.CharField(max_length=15, primary_key=True)
    name = models.CharField(max_length=127)
    symbol = models.CharField(max_length=7, null=True, blank=True)
    asset_class = models.ForeignKey(AssetClass, on_delete=models.PROTECT)
    is_liquid = models.BooleanField()


'''
<< User models >>
'''

class CustomUser(AbstractUser):
    last_update = models.DateTimeField(null=True, blank=True)
    last_full_refresh = models.DateTimeField(null=True, blank=True)


class Account(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    institution_name = models.CharField(max_length=255)
    country = models.CharField(max_length=255, choices=COUNTRY_CHOICES)
    nordigen_code = models.UUIDField(blank=True, null=True)
    color = models.CharField(max_length=7, default="#4b8dd3")
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['institution_name', 'user'], name='unique_institution_name_user')
        ]


class Transaction(models.Model):
    def validate_transaction_amount(value):
        if value == 0:
            raise ValidationError("Transaction amount can't be zero.")
    
    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    entity = models.CharField(max_length=255)
    amount = models.FloatField(validators=[validate_transaction_amount])
    datetime = models.DateTimeField()
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    category = models.CharField(max_length=31, null=True, blank=True)
    

class Trade(models.Model):
    def validate_trade_amount(value):
        if value == 0:
            raise ValidationError("Trade amount can't be zero.")

    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='trade_asset')
    amount = models.FloatField(validators=[validate_trade_amount])
    counter = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='counter_asset')
    datetime = models.DateTimeField()


class BalanceHistory(models.Model):
    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    date = models.DateField()
    balance = models.FloatField(validators=[MinValueValidator(0.0)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['account', 'asset', 'date'], name='unique_account_asset_date')
        ]
        ordering = ['account', 'asset', 'date']

    @classmethod
    def get_valid_range_dates(cls, user):
        """
        Returns a tuple (start_date, end_date) representing the latest continuous period
        where all account-asset combinations have records.
        Returns (None, None) if no valid range exists.
        """
        # Get count of ALL account-asset combinations for the user
        n_all_combinations = cls.objects.filter(
            account__user=user
        ).values('account', 'asset').distinct().count()

        if not n_all_combinations:
            return None, None

        # Get all dates where every combination has a record, ordered by date ascending
        complete_dates = cls.objects.filter(
            account__user=user
        ).values('date').annotate(
            combination_count=Count('id', distinct=True, filter=models.Q(account__user=user))
        ).filter(
            combination_count=n_all_combinations
        ).order_by('date').values_list('date', flat=True)

        complete_dates = list(complete_dates)

        if not complete_dates:
            return None, None

        # Set the end of the valid range to the latest complete date
        valid_range_end = complete_dates[-1]
        valid_range_start = valid_range_end

        # Find the first discontinuity going backwards
        for i in range(len(complete_dates) - 1, 0, -1):
            if (complete_dates[i] - complete_dates[i - 1]).days > 1:  # Gap found
                break
            # Keep moving start date back as long as dates are continuous
            valid_range_start = complete_dates[i - 1]

        return valid_range_start, valid_range_end

    @classmethod
    def get_valid_range_records(cls, user):
        """
        Returns BalanceHistory records within the valid date range for a user.
        A valid range is defined as the latest continuous period where all account-asset combinations have records.
        """
        valid_range_start, valid_range_end = cls.get_valid_range_dates(user)

        if valid_range_start is None:
            return cls.objects.none()

        return cls.objects.filter(
            account__user=user,
            date__gte=valid_range_start,
            date__lte=valid_range_end
        )

    @classmethod
    def get_latest_valid_balances(cls, user):
        """
        Returns the latest BalanceHistory records within the valid date range for a user.
        Returns only one record per account-asset combination, representing the most recent balance.
        """
        valid_range_start, valid_range_end = cls.get_valid_range_dates(user)

        if valid_range_start is None:
            return cls.objects.none()

        return cls.objects.filter(
            account__user=user,
            date=valid_range_end
        )