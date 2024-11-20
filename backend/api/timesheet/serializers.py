from rest_framework import serializers
from ..submodels.models_timesheet import *
from django.utils import timezone
from datetime import datetime, timedelta


class SendLeaveRequestSerializer(serializers.ModelSerializer):
    attachments = serializers.FileField(required=False)

    class Meta:
        model = LeaveRequest
        fields = ['id', 'from_date', 'to_date', 'attachments', 'note']

    def validate(self, attrs):
        if attrs["to_date"] < attrs["from_date"]:
            raise serializers.ValidationError({"error": "to_date cannot be after from_date"})
        return attrs
    
    def send_request(self, request):
        try:
            employee = Employee.objects.get(user=request.user)
            from_date = self.validated_data['from_date']
            to_date = self.validated_data['to_date']
            attachments = self.validated_data['attachments']
            note = self.validated_data['note']
            
            leave_request = LeaveRequest.objects.create(
                employee=employee,
                from_date=from_date,
                to_date=to_date,
                attachments=attachments,
                note=note
            )
            return leave_request
        except Exception as error:
            print("send_leave_request_error:", error)
            return None

class ListLeaveRequestEmployeeSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = ['id', 'from_date', 'to_date', 'status', 'attachments', 'note']
    
    def get_attachments(self, obj):
        request = self.context.get('request')
        if obj.attachments:
            return request.build_absolute_uri(obj.attachments.url)
        return None

class ListLeaveRequestManagerSerializer(serializers.ModelSerializer):
    employee = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = ['id', 'employee', 'from_date', 'to_date', 'status', 'attachments', 'note']
    
    def get_employee(self, obj):
        data = {}
        data['id'] = obj.employee.id
        data['employee_id'] = obj.employee.employee_id
        data['department'] = obj.employee.department.name
        data['full_name'] = obj.employee.full_name
        return data
    
    def get_attachments(self, obj):
        request = self.context.get('request')
        if obj.attachments:
            return request.build_absolute_uri(obj.attachments.url)
        return None

class ApproveLeaveRequestSerializer(serializers.ModelSerializer):
    leave_request_id = serializers.IntegerField(required=True)

    class Meta:
        model = LeaveRequest
        fields = ['leave_request_id', 'status', 'approved_by']
    
    def approve_request(self, request):
        try:
            leave_request_id = self.validated_data['leave_request_id']
            leave_request = LeaveRequest.objects.get(id=leave_request_id)
            leave_request.status = LeaveRequest.Status.APPROVED
            leave_request.approved_by = request.user
            leave_request.approved_at = timezone.now()
            leave_request.save()

            leave_balance = LeaveBalance.objects.get(employee=leave_request.employee)
            delta = leave_request.to_date - leave_request.from_date
            leave_balance.used_leaves += (delta.days + 1)
            if leave_balance.remaining_leaves >= (delta.days + 1):
                leave_balance.remaining_leaves -= (delta.days + 1)
            else:
                leave_balance.remaining_leaves = 0
            leave_balance.save()
            return leave_request
        except Exception as error:
            print("approve_leave_request_error:", error)
            return None
        
    def reject_request(self, request):
        try:
            leave_request_id = self.validated_data['leave_request_id']
            leave_request = LeaveRequest.objects.get(id=leave_request_id)
            leave_request.status = LeaveRequest.Status.REJECTED
            leave_request.approved_by = request.user
            leave_request.approved_at = timezone.now()
            leave_request.save()
            return leave_request
        except Exception as error:
            print("reject_leave_request_error:", error)
            return None

class TimeSheetSerializer(serializers.ModelSerializer):
    shift = serializers.SerializerMethodField()
    class Meta:
        model = TimeSheet
        fields = ['id','date','shift','check_in_time','check_out_time','status','is_overtime','overtime_hours','note']

    def get_shift(self, obj):
        if obj.shift:
            return obj.shift.shift_type
        return "OVERTIME"
