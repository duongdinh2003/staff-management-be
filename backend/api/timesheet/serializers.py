from rest_framework import serializers
from ..submodels.models_timesheet import *


# class SendLeaveRequestSerializer(serializers.ModelSerializer):
#     attachments = serializers.FileField(required=False)

#     class Meta:
#         model = LeaveRequest
#         fields = ['id', 'from_date', 'to_date', 'attachments']
    
#     def send_request(self, request):
#         try:
#             employee = Employee.objects.get(user=request.user)
#             from_date = self.validated_data['from_date']
#             to_date = self.validated_data['to_date']
#             attachments = self.validated_data['attachments']
#             leave_balance = LeaveBalance.objects.get()