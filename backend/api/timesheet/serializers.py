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
    approved_by = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = ['id', 'from_date', 'to_date', 'status', 'approved_by', 'approved_at', 'attachments', 'note']
    
    def get_approved_by(self, obj):
        return "Manager"
    
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
        fields = ['id', 'employee', 'from_date', 'to_date', 'status', 'approved_at', 'attachments', 'note']
    
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

class SendOvertimeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = OvertimeRequest
        fields = ['id', 'date', 'from_time', 'to_time', 'note']
    
    def validate(self, attrs):
        if attrs["to_time"] < attrs["from_time"]:
            raise serializers.ValidationError({"error": "to_time cannot be after from_time"})
        return attrs
    
    def send_request(self, request):
        try:
            employee = Employee.objects.get(user=request.user)
            date = self.validated_data['date']
            from_time = self.validated_data['from_time']
            to_time = self.validated_data['to_time']
            note = self.validated_data['note']

            overtime_request = OvertimeRequest.objects.create(
                employee=employee,
                date=date,
                from_time=from_time,
                to_time=to_time,
                note=note
            )
            return overtime_request
        except Exception as error:
            print("send_overtime_request_error:", error)
            return None

class ListOvertimeRequestEmployeeSerializer(serializers.ModelSerializer):
    approved_by = serializers.SerializerMethodField()

    class Meta:
        model = OvertimeRequest
        fields = ['id', 'date', 'from_time', 'to_time', 'status', 'approved_by', 'approved_at', 'note']
    
    def get_approved_by(self, obj):
        return "Manager"

class ListOvertimeRequestManagerSerializer(serializers.ModelSerializer):
    employee = serializers.SerializerMethodField()

    class Meta:
        model = OvertimeRequest
        fields = ['id', 'employee', 'date', 'from_time', 'to_time', 'status', 'approved_at', 'note']
    
    def get_employee(self, obj):
        data = {}
        data['id'] = obj.employee.id
        data['employee_id'] = obj.employee.employee_id
        data['department'] = obj.employee.department.name
        data['full_name'] = obj.employee.full_name
        return data

class ApproveOvertimeRequestSerializer(serializers.ModelSerializer):
    overtime_request_id = serializers.IntegerField(required=True)

    class Meta:
        model = OvertimeRequest
        fields = ['overtime_request_id', 'status', 'approved_by']
    
    def approve_request(self, request):
        try:
            overtime_request_id = self.validated_data['overtime_request_id']
            overtime_request = OvertimeRequest.objects.get(id=overtime_request_id)
            overtime_request.status = OvertimeRequest.Status.APPROVED
            overtime_request.approved_by = request.user
            overtime_request.approved_at = timezone.now()
            overtime_request.save()

            return overtime_request
        except Exception as error:
            print("approve_overtime_request_error:", error)
            return None
        
    def reject_request(self, request):
        try:
            overtime_request_id = self.validated_data['overtime_request_id']
            overtime_request = OvertimeRequest.objects.get(id=overtime_request_id)
            overtime_request.status = OvertimeRequest.Status.REJECTED
            overtime_request.approved_by = request.user
            overtime_request.approved_at = timezone.now()
            overtime_request.save()
            return overtime_request
        except Exception as error:
            print("reject_overtime_request_error:", error)
            return None
