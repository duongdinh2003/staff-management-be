from django.db import models
from django.contrib.auth.models import User
from .models_employee import Employee
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime
from decimal import Decimal
import os


class WorkingShift(models.Model):
    class ShiftType(models.TextChoices):
        MORNING = 'MORNING', _('Morning Shift')
        AFTERNOON = 'AFTERNOON', _('Afternoon Shift')
    
    shift_type = models.CharField(max_length=10, choices=ShiftType.choices)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.shift_type


class TimeSheet(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', _('Present')
        LATE = 'LATE', _('Late')
        EARLY_LEAVE = 'EARLY_LEAVE', _('Early Leave')
        ABSENT = 'ABSENT', _('Absent')
        LEAVE = 'LEAVE', _('On Leave')
        INCOMPLETE = 'INCOMPLETE', _('Incomplete Check')
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(null=True, blank=True)
    shift = models.ForeignKey(WorkingShift, on_delete=models.PROTECT, null=True, blank=True)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices)
    is_overtime = models.BooleanField(default=False)
    overtime_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'date', 'shift']

    def __str__(self):
        if self.shift:
            return f"{self.shift.shift_type} {str(self.date)}: {self.employee.employee_id} - Status: {self.status}"
        return f"Overtime {str(self.date)}: {self.employee.employee_id} - Status: {self.status}"


class OvertimeRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        CANCELLED = 'CANCELLED', _('Cancelled')
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='overtime_requests')
    date = models.DateField(null=True, blank=True)
    from_time = models.TimeField(null=True, blank=True)
    to_time = models.TimeField(null=True, blank=True)
    status = models.CharField(
        max_length=10, 
        choices=Status.choices,
        default=Status.PENDING
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_overtimes'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.employee_id} - From: {str(self.from_time)} to: {str(self.to_time)} {str(self.date)} - Status: {self.status}"


def upload_to_employee_folder(instance, filename):
    employee_id = instance.employee.employee_id if instance.employee.employee_id else 'unknown'
    base_name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    new_filename = f"{base_name}_{timestamp}{ext}"
    return f"leave_attachments/employee_{employee_id}/{new_filename}"

class LeaveRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        CANCELLED = 'CANCELLED', _('Cancelled')

    class LeaveType(models.TextChoices):
        ANNUAL = 'ANNUAL', _('Annual Leave')
        SICK = 'SICK', _('Sick Leave')
        UNPAID = 'UNPAID', _('Unpaid Leave')
        OTHER = 'OTHER', _('Other')

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=10, choices=LeaveType.choices, default=LeaveType.ANNUAL)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(
        max_length=10, 
        choices=Status.choices,
        default=Status.PENDING
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    attachments = models.FileField(upload_to=upload_to_employee_folder, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.employee_id} - From date: {str(self.from_date)} to date: {str(self.to_date)} - Status: {self.status}"


class LeaveBalance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balance')
    year = models.PositiveIntegerField()
    total_leaves = models.PositiveIntegerField(default=6)
    used_leaves = models.PositiveIntegerField(default=0)
    remaining_leaves = models.PositiveIntegerField(default=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'year']
    
    def __str__(self):
        return f"{str(self.year)} - {self.employee.employee_id}: Remaining: {str(self.remaining_leaves)}"


class SalaryRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='salary')
    month = models.PositiveSmallIntegerField(validators=[
        MinValueValidator(1),
        MaxValueValidator(12)
    ])
    year = models.PositiveIntegerField()
    
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    position_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    attendance_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['employee', 'month', 'year']
    
    def __str__(self):
        return f"{self.employee.employee_id} - {str(self.month)}-{str(self.year)} - Salary: {str(self.gross_salary)}"


class EmployeeEvaluation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='evaluations')
    evaluated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluated_employees'
    )
    evaluated_at = models.DateTimeField(null=True, blank=True)
    month = models.PositiveSmallIntegerField(validators=[
        MinValueValidator(1),
        MaxValueValidator(12)
    ])
    year = models.PositiveIntegerField()
    content = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'month', 'year']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.month}/{self.year}"
