import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger("visualfolio_scheduled_tasks")


def cleanup_demo_users():
    cutoff = settings.DEMO_ACCOUNT_CUTOFF

    User = get_user_model()
    cutoff_date = timezone.now() - cutoff
    demo_users = User.objects.filter(last_login__lt=cutoff_date)

    if not demo_users.exists():
        logger.info(f"No users present.")
        return

    logger.info(f"Deleting {demo_users.count()} demo users older than cutoff date ({cutoff_date}):")
    for user in demo_users:
        logger.info(f"User ID: {user.id}, Username: {user.username}, Last Login: {user.last_login}")

    # Perform deletion
    deleted_count, _ = demo_users.delete()
    logger.info("Successfully deleted users")
