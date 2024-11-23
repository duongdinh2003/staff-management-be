from django.urls import path
from .views import *

get_current_month_salary_records = MonthlySalaryRecordForManagerMVS.as_view({
    'get': 'get_current_month_salary_records'
})

urlpatterns = [
    path('get_current_month_salary_records/', get_current_month_salary_records, name='get_current_month_salary_records'),
]
