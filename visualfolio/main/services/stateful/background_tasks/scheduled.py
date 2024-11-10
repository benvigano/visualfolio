import logging
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger("visualfolio_scheduled_tasks")

def delete_old_demo_accounts(cutoff):
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
