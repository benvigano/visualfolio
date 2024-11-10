from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from main.services.stateful.background_tasks.scheduled import delete_old_demo_accounts


class Command(BaseCommand):
    help = 'Deletes demo users generated earlier than the specified cutoff duration'

    def handle(self, *args, **kwargs):
        cutoff = settings.DEMO_ACCOUNT_CUTOFF
        delete_old_demo_accounts(cutoff)
