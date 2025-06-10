from django.apps import AppConfig
from django.core.management import call_command
from django.db.utils import OperationalError, ProgrammingError
from django.db.models.signals import post_migrate
import os
import sys

def load_static_data(sender, **kwargs):
    try:
        print("Loading static data fixtures...")
        call_command('loaddata', 'static_data/assetclass_data.json')
        call_command('loaddata', 'static_data/asset_data.json')
        print("Static data loaded successfully.")
    except Exception as e:
        print(f"Error loading static data: {e}")


def initialize_scheduler():
    """
    Initialize and start the background scheduler.
    This should only be called when running the actual web server,
    not during migrations or other management commands.
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    from django_apscheduler.jobstores import DjangoJobStore
    from main.services.stateful.background_tasks.scheduled import cleanup_demo_users
    import django

    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Run every day at 2 AM
    scheduler.add_job(
        cleanup_demo_users,
        trigger='cron',
        hour='2',
        minute='0',
        id='cleanup_demo_users',
        replace_existing=True,
        misfire_grace_time=None,  # Always run any missed jobs when restarting the server.
    )
    
    scheduler.start()

    if django.conf.settings.DEPLOYMENT_MODE == 'local':
        print("Scheduler started successfully in local mode.")
    else:
        print("Scheduler started successfully in cloud mode.")
    
    return scheduler


class MainConfig(AppConfig):
    # Set all auto fields to 64-bit for scalability (espeically transactions)
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    
    def ready(self):
        # Connect the post_migrate signal to load static data
        post_migrate.connect(load_static_data, sender=self)

        is_running_server = 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]
        is_management_command = any(cmd in sys.argv for cmd in ['makemigrations', 'migrate', 'collectstatic', 'shell'])

        if is_running_server and not is_management_command:
            initialize_scheduler()
