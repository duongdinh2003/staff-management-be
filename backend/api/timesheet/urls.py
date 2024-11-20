from django.urls import path
from .views import *

approve_leave_request = ApproveLeaveRequestMVS.as_view({
    'post': 'approve_leave_request'
})
reject_leave_request = ApproveLeaveRequestMVS.as_view({
    'post': 'reject_leave_request'
})

urlpatterns = [
    path('send_leave_request/', SendLeaveRequestView.as_view(), name='send_leave_request'),
    path('list_leave_requests_employee/', ListLeaveRequestEmployeeView.as_view(), name='list_leave_requests_employee'),
    path('list_leave_requests_manager/', ListLeaveRequestManagerView.as_view(), name='list_leave_requests_manager'),
    path('approve_leave_request/', approve_leave_request, name='approve_leave_request'),
    path('reject_leave_request/', reject_leave_request, name='reject_leave_request'),
]
