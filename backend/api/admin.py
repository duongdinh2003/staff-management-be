from django.contrib import admin
from .submodels.models_employee import *
from .submodels.models_timesheet import *

# Register your models here.
admin.site.register(Department)
admin.site.register(Position)
admin.site.register(Employee)
admin.site.register(WorkingShift)
admin.site.register(TimeSheet)
admin.site.register(OvertimeRequest)
admin.site.register(LeaveRequest)
admin.site.register(LeaveBalance)
admin.site.register(SalaryRecord)
admin.site.register(EmployeeEvaluation)
