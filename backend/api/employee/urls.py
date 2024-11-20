from django.urls import path
from .views import *

create_employee_account = EmployeeAccountMVS.as_view({
    'post': 'create_employee_account'
})

urlpatterns = [
    path('department_list_dropdown/', DepartmentDropdownView.as_view(), name='department_list_dropdown'),
    path('position_list_dropdown/', PositionDropDownView.as_view(), name='position_list_dropdown'),
    path('create_employee_account/', create_employee_account, name='create_employee_account'),
    path('update_employee_profile/', UpdateEmployeeProfileView.as_view(), name='update_employee_profile'),
    path('get_employee_profile/', EmployeeProfileView.as_view(), name='get_employee_profile'),
    path('upload_employee_avatar/', UploadEmployeeAvatarView.as_view(), name='upload_employee_avatar'),
]
