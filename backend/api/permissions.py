from rest_framework.permissions import BasePermission
from django.contrib.auth.models import User, Group
from django.conf import settings


class IsManager(BasePermission):
    """
    Allows access only to managers.
    """
    def has_permission(self, request, view):
        is_manager = request.user.groups.filter(name=settings.GROUP_NAME['MANAGER']).exists()
        return is_manager
    
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj)

class IsEmployee(BasePermission):
    """
    Allows access only to employees.
    """
    def has_permission(self, request, view):
        is_employee = request.user.groups.filter(name=settings.GROUP_NAME['EMPLOYEE']).exists()
        return is_employee
    
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj)
