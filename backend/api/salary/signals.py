from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from ..submodels.models_timesheet import TimeSheet, SalaryRecord, EmployeeEvaluation

@receiver(post_save, sender=TimeSheet)
def create_monthly_record(sender, instance, created, **kwargs):
    if not instance.date:
        return
        
    month = instance.date.month
    year = instance.date.year
    
    SalaryRecord.objects.get_or_create(
        employee=instance.employee,
        month=month,
        year=year,
        defaults={
            'base_salary': Decimal('0.00'),
            'overtime_pay': Decimal('0.00'),
            'attendance_bonus': Decimal('0.00'),
            'gross_salary': Decimal('0.00')
        }
    )

    EmployeeEvaluation.objects.get_or_create(
        employee=instance.employee,
        month=month,
        year=year
    )
