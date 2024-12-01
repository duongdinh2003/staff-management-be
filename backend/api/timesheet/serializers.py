from rest_framework import serializers
from ..submodels.models_timesheet import *
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from dateutil.rrule import rrule, DAILY
import calendar


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
        if obj.approved_by:
            return "Manager"
        return None
    
    def get_attachments(self, obj):
        request = self.context.get('request')
        if obj.attachments:
            return request.build_absolute_uri(obj.attachments.url)
        return None

class ListLeaveRequestManagerSerializer(serializers.ModelSerializer):
    employee = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    leave_request_count = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = ['id','employee','from_date','to_date','status','approved_at','attachments','note','leave_request_count']
    
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
    
    def get_leave_request_count(self, obj):
        current_date = timezone.localtime(timezone.now()).date()
        start_of_month = current_date.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        count = LeaveRequest.objects.filter(
            Q(employee=obj.employee) &
            Q(status=LeaveRequest.Status.APPROVED) &
            Q(from_date__lte=end_of_month) & Q(to_date__gte=start_of_month)
        ).count()
        return count

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

class ShiftDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSheet
        fields = ['check_in_time','check_out_time','status','is_overtime','overtime_hours','note']

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
        if obj.approved_by:
            return "Manager"
        return None

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


# ============================================== Working hours Statistics =========================================
def calculate_working_hours(check_in_time, check_out_time):
    if check_in_time and check_out_time:
        datetime_in = datetime.combine(datetime.today().date(), check_in_time)
        datetime_out = datetime.combine(datetime.today().date(), check_out_time)
        total_time = datetime_out - datetime_in
        return total_time.total_seconds() / 3600
    return 0

def calculate_working_days(employee, month, year):
    start_of_month = datetime(year, month, 1).date()
    _, last_day_num = calendar.monthrange(year, month)
    end_of_month = datetime(year, month, last_day_num).date()
    working_days = TimeSheet.objects.filter(
        Q(employee=employee) &
        Q(date__range=(start_of_month, end_of_month)) &
        Q(shift__isnull=False) &
        (Q(status=TimeSheet.Status.PRESENT) |
        Q(status=TimeSheet.Status.EARLY_LEAVE))
    ).count()
    return working_days / 2

class TrackingTimeEmployeeManagementSerializer(serializers.ModelSerializer):
    employee = serializers.SerializerMethodField()
    working_days = serializers.SerializerMethodField()
    regular_hours = serializers.SerializerMethodField()
    overtime_hours = serializers.SerializerMethodField()
    leave_days = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeEvaluation
        fields = ['id','employee','working_days','regular_hours','overtime_hours','leave_days','content']
    
    def get_employee(self, obj):
        data = {}
        data['id'] = obj.employee.id
        data['employee_id'] = obj.employee.employee_id
        data['department'] = obj.employee.department.name
        data['full_name'] = obj.employee.full_name
        return data
    
    def get_working_days(self, obj):
        current_date = timezone.localtime(timezone.now()).date()
        month = self.context.get('month', current_date.month)
        year = self.context.get('year', current_date.year)
        working_days = calculate_working_days(obj.employee, month, year)
        return working_days
    
    def get_regular_hours(self, obj):
        current_date = timezone.localtime(timezone.now()).date()
        month = self.context.get('month', current_date.month)
        year = self.context.get('year', current_date.year)
        start_of_month = datetime(year, month, 1).date()
        _, last_day_num = calendar.monthrange(year, month)
        end_of_month = datetime(year, month, last_day_num).date()
        timesheets = TimeSheet.objects.filter(
            Q(employee=obj.employee) &
            Q(date__range=(start_of_month, end_of_month)) &
            (Q(status=TimeSheet.Status.PRESENT) |
            Q(status=TimeSheet.Status.EARLY_LEAVE))
        )
        regular_hours = Decimal(0)
        for timesheet in timesheets:
            shift_hours = Decimal(calculate_working_hours(timesheet.check_in_time, timesheet.check_out_time))
            regular_hours += shift_hours
        
        return round(regular_hours, 2)
    
    def get_overtime_hours(self, obj):
        current_date = timezone.localtime(timezone.now()).date()
        month = self.context.get('month', current_date.month)
        year = self.context.get('year', current_date.year)
        start_of_month = datetime(year, month, 1).date()
        _, last_day_num = calendar.monthrange(year, month)
        end_of_month = datetime(year, month, last_day_num).date()
        timesheets = TimeSheet.objects.filter(
            employee=obj.employee,
            shift__isnull=True,
            date__range=(start_of_month, end_of_month),
            status=TimeSheet.Status.PRESENT
        )
        overtime_hours = Decimal(0)
        for timesheet in timesheets:
            overtime_hours += timesheet.overtime_hours
        
        return overtime_hours
    
    def get_leave_days(self, obj):
        current_date = timezone.localtime(timezone.now()).date()
        month = self.context.get('month', current_date.month)
        year = self.context.get('year', current_date.year)
        start_of_month = datetime(year, month, 1).date()
        _, last_day_num = calendar.monthrange(year, month)
        end_of_month = datetime(year, month, last_day_num).date()
        leave_requests = LeaveRequest.objects.filter(
            Q(employee=obj.employee) &
            Q(status=LeaveRequest.Status.APPROVED) &
            Q(from_date__lte=end_of_month) & Q(to_date__gte=start_of_month)
        )
        leave_days = 0
        weekdays_count = 0
        saturday_count = 0
        for leave_request in leave_requests:
            start_date = max(leave_request.from_date, start_of_month)
            end_date = min(leave_request.to_date, end_of_month)

            for single_date in rrule(DAILY, dtstart=start_date, until=end_date):
                weekday = single_date.weekday()
                if weekday == 6:
                    continue
                elif weekday == 5:
                    saturday_count += 1
                else:
                    weekdays_count += 1

        leave_days += weekdays_count + saturday_count / 2
        return leave_days
    
    def get_content(self, obj):
        current_date = timezone.localtime(timezone.now()).date()
        start_of_month = current_date.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        if current_date == end_of_month:
            return obj.content
        return None
    
    def evaluate_employee(self, request):
        try:
            evaluation_id = request.data.get('evaluation_id')
            content = request.data.get('content')
            evaluation = EmployeeEvaluation.objects.get(id=evaluation_id)
            evaluation.evaluated_by = request.user
            evaluation.evaluated_at = timezone.localtime(timezone.now())
            evaluation.content = content
            evaluation.save()
            return evaluation
        except EmployeeEvaluation.DoesNotExist:
            print("evaluation not found.")
            return None
