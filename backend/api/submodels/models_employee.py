from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from datetime import datetime
from decimal import Decimal
import os


class Department(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_department')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Position(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    salary_base = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    salary_insufficient_work = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    salary_overtime = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    attendance_bonus = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


def upload_to_avatars_folder(instance, filename):
    employee_id = instance.employee_id if instance.employee_id else 'unknown'
    base_name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    new_filename = f"{base_name}_{timestamp}{ext}"
    return f"avatars/employee_{employee_id}/{new_filename}"

class Employee(models.Model):
    class Gender(models.TextChoices):
        MALE = 'M', _('Male')
        FEMALE = 'F', _('Female')
        OTHER = 'O', _('Other')
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    position = models.ForeignKey(Position, on_delete=models.PROTECT)
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, default=Gender.MALE)
    address = models.CharField(max_length=150, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    avatar = models.ImageField(upload_to=upload_to_avatars_folder, null=True, blank=True)
    join_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.employee_id:
            department_code = self.department.code
            last_employee = Employee.objects.filter(
                department=self.department,
                employee_id__startswith=department_code
            ).order_by('-employee_id').first()

            if last_employee and last_employee.employee_id:
                last_number = int(last_employee.employee_id[len(department_code):])
            else:
                last_number = 0
            
            new_number = last_number + 1
            self.employee_id = f"{department_code}{new_number:03d}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.full_name} - Department: {self.department.name}"
