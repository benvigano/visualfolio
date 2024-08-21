from django.apps import AppConfig
from django.core.management import call_command
from django.db.utils import OperationalError
import os

class MainConfig(AppConfig):
    # Set all auto fields to 64-bit for scalability (espeically transactions)
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    
    def _load_static_data(self):
        try:
            print("Loading static data fixtures...")
            call_command('loaddata', 'static_data/assetclass_data.json')
            call_command('loaddata', 'static_data/asset_data.json')
            print("Static data loaded successfully.")
        except Exception as e:
            print(f"Error loading static data: {e}")

    def ready(self):
        # Check that it's the main runserver thread
        if os.environ.get('RUN_MAIN') == 'true':
            db_path = os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3')

            try:
                from main.models import AssetClass
                assert AssetClass.objects.count() != 0
            except Exception:
                # Only if the database doesn't exist or is empty, load static data
                self._load_static_data()
