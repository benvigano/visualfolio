from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, ValidationError
from django.conf import settings
from django.db import transaction


from .constants import COUNTRY_CHOICES


'''
<< Static models >>
'''

class AssetClass(models.Model):
    name = models.CharField(max_length=63, primary_key=True)
    color = models.CharField(max_length=7)


class Asset(models.Model):
    code = models.CharField(max_length=15, primary_key=True)
    name = models.CharField(max_length=127)
    symbol = models.CharField(max_length=7, null=True, blank=True)
    asset_class = models.ForeignKey(AssetClass, on_delete=models.PROTECT)
    is_liquid = models.BooleanField()


'''
<< User models - Base >>
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
    

class AccountItem(models.Model):
    id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    balance = models.FloatField(
        validators=[MinValueValidator(0.0)],
        default=0.0
    )
        
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['account', 'asset'], name='unique_account_asset_user')
        ]
        
    @classmethod
    def update_balance(cls, account, asset, amount):
        """
        If the AccountItem doesn't exist, it's created (balance set to 0).
        """
        with transaction.atomic():
            account_item, created = cls.objects.get_or_create(
                account=account,
                asset=asset,
                defaults={'balance': 0.0}
            )
            account_item.balance += amount
            account_item.full_clean()
            account_item.save()
            return account_item

    @classmethod
    def get_balance(cls, account, asset):
        """
        If the AccountItem doesn't exist, returns 0.
        """
        try:
            return cls.objects.get(
                account=account,
                asset=asset
            ).balance
        except cls.DoesNotExist:
            return 0.0
        

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
    
    
'''
<< User models - Derived >>
'''

class BalanceHistory(models.Model):
    id = models.AutoField(primary_key=True)
    account_item = models.ForeignKey(AccountItem, on_delete=models.CASCADE)
    date = models.DateField()
    balance = models.FloatField(validators=[MinValueValidator(0.0)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['account_item', 'date'], name='unique_accountitem_date')
        ]
        ordering = ['account_item', 'date']
