from django.urls import path, include

urlpatterns = [
    path('user/', include('api.login.urls')),
    path('employee/', include('api.employee.urls')),
    path('timesheet/', include('api.timesheet.urls')),
    path('salary/', include('api.salary.urls')),
]
