from django.urls import path
from .views import *

# Leave request
approve_leave_request = ApproveLeaveRequestMVS.as_view({
    'post': 'approve_leave_request'
})
reject_leave_request = ApproveLeaveRequestMVS.as_view({
    'post': 'reject_leave_request'
})
list_leave_requests_employee = ListLeaveRequestEmployeeView.as_view({
    'get': 'list_leave_requests_employee'
})
get_leave_count_in_current_month = ListLeaveRequestEmployeeView.as_view({
    'get': 'get_leave_count_in_current_month'
})
list_leave_requests_manager = ListLeaveRequestManagerView.as_view({
    'get': 'list_leave_requests_manager'
})

# Overtime request
approve_overtime_request = ApproveOvertimeRequestMVS.as_view({
    'post': 'approve_overtime_request'
})
reject_overtime_request = ApproveOvertimeRequestMVS.as_view({
    'post': 'reject_overtime_request'
})
list_overtime_requests_employee = ListOvertimeRequestEmployeeView.as_view({
    'get': 'list_overtime_requests_employee'
})
list_overtime_requests_manager = ListOvertimeRequestManagerView.as_view({
    'get': 'list_overtime_requests_manager'
})

# Timesheet
get_current_month_timesheet_employee = TimeSheetEmployeeMVS.as_view({
    'get': 'get_current_month_timesheet_employee'
})
get_daily_timesheet_employee = TimeSheetEmployeeMVS.as_view({
    'get': 'get_daily_timesheet_employee'
})
get_tracking_time_employee = TrackingTimeEmployeeManagementMVS.as_view({
    'get': 'get_tracking_time_employee'
})
manager_evaluate_employee = TrackingTimeEmployeeManagementMVS.as_view({
    'post': 'manager_evaluate_employee'
})

urlpatterns = [
    # Leave request
    path('send_leave_request/', SendLeaveRequestView.as_view(), name='send_leave_request'),
    path('list_leave_requests_employee/', list_leave_requests_employee, name='list_leave_requests_employee'),
    path('get_leave_count_in_current_month/', get_leave_count_in_current_month, name='get_leave_count_in_current_month'),
    path('list_leave_requests_manager/', list_leave_requests_manager, name='list_leave_requests_manager'),
    path('approve_leave_request/', approve_leave_request, name='approve_leave_request'),
    path('reject_leave_request/', reject_leave_request, name='reject_leave_request'),

    # Timesheet
    path('check_in/', CheckInAPIView.as_view(), name='check_in'),
    path('check_out/', CheckOutAPIView.as_view(), name='check_out'),
    path('check_in_overtime/', OvertimeCheckInAPIView.as_view(), name='check_in_overtime'),
    path('check_out_overtime/', OvertimeCheckOutAPIView.as_view(), name='check_out_overtime'),
    path('get_daily_timesheet_employee/', get_daily_timesheet_employee, name='get_daily_timesheet_employee'),
    path('get_current_month_timesheet_employee/', get_current_month_timesheet_employee, name='get_current_month_timesheet_employee'),
    path('get_tracking_time_employee/', get_tracking_time_employee, name='get_tracking_time_employee'),
    path('manager_evaluate_employee/', manager_evaluate_employee, name='manager_evaluate_employee'),

    # Overtime request
    path('send_overtime_request/', SendOvertimeRequestView.as_view(), name='send_overtime_request'),
    path('list_overtime_requests_employee/', list_overtime_requests_employee, name='list_overtime_requests_employee'),
    path('list_overtime_requests_manager/', list_overtime_requests_manager, name='list_overtime_requests_manager'),
    path('approve_overtime_request/', approve_overtime_request, name='approve_overtime_request'),
    path('reject_overtime_request/', reject_overtime_request, name='reject_overtime_request'),
]
