from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .submodels.models_auth import User

# Register your models here.
admin.site.register(User)
