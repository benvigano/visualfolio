from django.apps import AppConfig
from django.core.management import call_command
from django.db.utils import OperationalError
from django.db.models.signals import post_migrate
import os

def load_static_data(sender, **kwargs):
    try:
        print("Loading static data fixtures...")
        call_command('loaddata', 'static_data/assetclass_data.json')
        call_command('loaddata', 'static_data/asset_data.json')
        print("Static data loaded successfully.")
    except Exception as e:
        print(f"Error loading static data: {e}")

class MainConfig(AppConfig):
    # Set all auto fields to 64-bit for scalability (espeically transactions)
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    
    def ready(self):
        # Connect the post_migrate signal to load static data
        post_migrate.connect(load_static_data, sender=self)
