from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime
from ..submodels.models_employee import Employee
from ..submodels.models_timesheet import LeaveBalance

@receiver(post_save, sender=Employee)
def create_leave_balance(sender, instance, created, **kwargs):
    if created:
        current_year = datetime.now().year
        LeaveBalance.objects.get_or_create(
            employee=instance,
            year=current_year,
            defaults={
                'total_leaves': 6,
                'used_leaves': 0,
                'remaining_leaves': 6,
            }
        )
