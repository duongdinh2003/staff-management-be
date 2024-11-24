from rest_framework import serializers
from ..submodels.models_timesheet import SalaryRecord, TimeSheet, LeaveRequest, LeaveBalance, EmployeeEvaluation
from django.utils.timezone import localtime, now
from django.db.models import Sum, Q, F, DecimalField, Case, When, Value, ExpressionWrapper
from django.db.models.functions import Coalesce, ExtractHour, ExtractMinute, Cast
from datetime import datetime, timedelta
from decimal import Decimal
from dateutil.rrule import rrule, DAILY


def calculate_timesheet_summary():
    current_date = localtime(now()).date()
    start_of_month = current_date.replace(day=1)
    
    # Tổng hợp TimeSheet theo nhân viên
    timesheet_summary = TimeSheet.objects.filter(
        Q(employee__is_active=True) &
        Q(date__range=(start_of_month, current_date)) &
        (Q(status=TimeSheet.Status.PRESENT) |
        Q(status=TimeSheet.Status.EARLY_LEAVE))
    ).values('employee').annotate(
        total_regular_hours=Coalesce(
            Sum(
                Case(
                    When(
                        check_in_time__isnull=False,
                        check_out_time__isnull=False,
                        shift__isnull=False,
                        then=ExpressionWrapper(
                            (
                                Cast(
                                    ExpressionWrapper(
                                        ExtractHour(F('check_out_time')) * 60 + 
                                        ExtractMinute(F('check_out_time')) -
                                        (ExtractHour(F('check_in_time')) * 60 + 
                                        ExtractMinute(F('check_in_time'))),
                                        output_field=DecimalField(max_digits=10, decimal_places=2)
                                    ),
                                    DecimalField(max_digits=10, decimal_places=2)
                                ) / 60.0
                            ),
                            output_field=DecimalField(max_digits=10, decimal_places=2)
                        )
                    ),
                    default=Value(Decimal('0.00'))
                )
            ),
            Decimal('0.00'),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        ),
        total_overtime_hours=Coalesce(
            Sum('overtime_hours'),
            Decimal('0.00'),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    )

    return timesheet_summary

def get_leave_days_detailed(employee_id):
    current_date = localtime(now()).date()
    start_of_month = current_date.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    leave_requests = LeaveRequest.objects.filter(
        Q(employee_id=employee_id) &
        Q(status=LeaveRequest.Status.APPROVED) &
        Q(from_date__lte=end_of_month) & Q(to_date__gte=start_of_month)
    )
    
    weekdays_count = 0
    saturday_count = 0
    leave_days = 0
    
    for leave_request in leave_requests:
        # Xác định ngày bắt đầu và kết thúc trong khoảng tháng hiện tại
        start_date = max(leave_request.from_date, start_of_month)
        end_date = min(leave_request.to_date, end_of_month)
        
        # Lặp qua từng ngày trong khoảng thời gian này
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

def append_to_note(current: str | None, new_content: str) -> str:
    if not current:
        current = new_content
    else:
        current += f", {new_content}"
    return current

def batch_calculate_monthly_salaries():
    current_date = localtime(now()).date()
    timesheet_summary = calculate_timesheet_summary()
    
    # Lấy tất cả SalaryRecord trong tháng hiện tại
    salary_records = SalaryRecord.objects.filter(
        month=current_date.month,
        year=current_date.year
    ).select_related('employee__position')

    # Lấy tất cả EmployeeEvaluation trong tháng hiện tại
    employee_evaluations = EmployeeEvaluation.objects.filter(
        month=current_date.month,
        year=current_date.year
    )
    
    # Tính lương từng nhân viên
    for summary in timesheet_summary:
        employee_id = summary['employee']
        total_regular_hours = Decimal(str(summary['total_regular_hours']))
        total_overtime_hours = Decimal(str(summary['total_overtime_hours']))

        # Lấy EmployeeEvaluation cho nhân viên hiện tại
        employee_evaluation = employee_evaluations.filter(employee_id=employee_id).first()
        if not employee_evaluation:
            continue
        
        # Lấy SalaryRecord cho nhân viên hiện tại
        salary_record = salary_records.filter(employee_id=employee_id).first()
        if not salary_record:
            continue
        
        # Lấy thông tin từ Position
        position = salary_record.employee.position

        # Ghi chú
        note = salary_record.note
        
        # Khởi tạo các biến với Decimal
        regular_pay = Decimal('0.00')
        overtime_pay = Decimal('0.00')
        attendance_pay = Decimal('0.00')
        leave_pay = Decimal('0.00')
        annual_pay = Decimal('0.00')
        
        # Tính lương cơ bản
        if total_regular_hours < Decimal('192.00'):
            employee_evaluation.content = "Chưa tốt"
            regular_pay = position.salary_insufficient_work * total_regular_hours
        else:
            regular_pay = position.salary_base * total_regular_hours
            employee_evaluation.content = "Tốt"
        
        leave_pay = Decimal(get_leave_days_detailed(employee_id)) * Decimal('8.00') * position.salary_base * Decimal('0.85')
        salary_record.base_salary = regular_pay + leave_pay
        
        # Tính thưởng chuyên cần
        if (total_regular_hours + total_overtime_hours) > Decimal('200.00'):
            attendance_pay = position.attendance_bonus
            salary_record.attendance_bonus = attendance_pay
            employee_evaluation.content = "Tuyệt vời"
        
        # Tính lương overtime
        overtime_pay = position.salary_overtime * total_overtime_hours
        salary_record.overtime_pay = overtime_pay

        # Tính thưởng phép năm
        if current_date.day == 31 and current_date.month == 12:
            leave_balance = LeaveBalance.objects.filter(
                employee_id=employee_id,
                year=current_date.year
            ).first()
            if leave_balance.used_leaves <= 6:
                annual_pay = Decimal('1500000.00')
                salary_record.other_bonus = annual_pay
                note = append_to_note(note, "thưởng phép năm 1500000")
                salary_record.note = note
            else:
                note = append_to_note(note, "cắt thưởng phép năm")
                salary_record.note = note
        
        # Tổng lương
        gross_salary = regular_pay + overtime_pay + attendance_pay + leave_pay + annual_pay
        salary_record.gross_salary = gross_salary
        
        # Lưu SalaryRecord
        salary_record.save()

        # Lưu EmployeeEvaluation
        employee_evaluation.save()


class SalaryRecordForManagerSerializer(serializers.ModelSerializer):
    employee = serializers.SerializerMethodField()

    class Meta:
        model = SalaryRecord
        fields = [
            'id',
            'employee',
            'month',
            'year',
            'base_salary',
            'overtime_pay',
            'attendance_bonus',
            'other_bonus',
            'gross_salary',
            'note'
        ]
    
    def get_employee(self, obj):
        data = {}
        data['id'] = obj.employee.id
        data['employee_id'] = obj.employee.employee_id
        data['department'] = obj.employee.department.name
        data['full_name'] = obj.employee.full_name
        return data
