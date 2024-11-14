from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Custom User model used to authenticate."""
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        MANAGER = 'MANAGER', _('Manager')
        HR = 'HR', _('HR Staff')
        ACCOUNTANT = 'ACCOUNTANT', _('Accountant')
        EMPLOYEE = 'EMPLOYEE', _('Employee')
    
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.EMPLOYEE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username
    
