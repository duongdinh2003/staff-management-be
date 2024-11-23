from rest_framework import serializers
from ..submodels.models_timesheet import SalaryRecord, TimeSheet
from django.utils.timezone import localtime, now
from django.db.models import Sum, F, DecimalField, Case, When, Value, ExpressionWrapper
from django.db.models.functions import Coalesce, ExtractHour, ExtractMinute, Cast
from datetime import datetime, timedelta
from decimal import Decimal


def calculate_timesheet_summary():
    current_date = localtime(now()).date()
    start_of_month = current_date.replace(day=1)
    
    # Tổng hợp TimeSheet theo nhân viên
    timesheet_summary = TimeSheet.objects.filter(
        employee__is_active=True,
        date__range=(start_of_month, current_date),
        status=TimeSheet.Status.PRESENT
    ).values('employee').annotate(
        total_regular_hours=Coalesce(
            Sum(
                Case(
                    When(
                        check_in_time__isnull=False,
                        check_out_time__isnull=False,
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

def batch_calculate_monthly_salaries():
    current_date = localtime(now()).date()
    timesheet_summary = calculate_timesheet_summary()
    
    # Lấy tất cả SalaryRecord trong tháng hiện tại
    salary_records = SalaryRecord.objects.filter(
        month=current_date.month,
        year=current_date.year
    ).select_related('employee__position')
    
    # Tính lương từng nhân viên
    for summary in timesheet_summary:
        employee_id = summary['employee']
        total_regular_hours = Decimal(str(summary['total_regular_hours']))
        total_overtime_hours = Decimal(str(summary['total_overtime_hours']))
        
        # Lấy SalaryRecord cho nhân viên hiện tại
        salary_record = salary_records.filter(employee_id=employee_id).first()
        if not salary_record:
            continue
        
        # Lấy thông tin từ Position
        position = salary_record.employee.position
        
        # Khởi tạo các biến với Decimal
        regular_pay = Decimal('0.00')
        overtime_pay = Decimal('0.00')
        attendance_pay = Decimal('0.00')
        
        # Tính lương cơ bản
        if total_regular_hours < Decimal('192.00'):
            regular_pay = position.salary_insufficient_work * total_regular_hours
        else:
            regular_pay = position.salary_base * total_regular_hours
        
        salary_record.base_salary = regular_pay
        
        # Tính thưởng chuyên cần
        if (total_regular_hours + total_overtime_hours) > Decimal('200.00'):
            attendance_pay = position.attendance_bonus
            salary_record.attendance_bonus = attendance_pay
        
        # Tính lương overtime
        overtime_pay = position.salary_overtime * total_overtime_hours
        salary_record.overtime_pay = overtime_pay
        
        # Tổng lương
        gross_salary = regular_pay + overtime_pay + attendance_pay
        salary_record.gross_salary = gross_salary
        
        # Lưu SalaryRecord
        salary_record.save()


class SalaryRecordForManagerSerializer(serializers.ModelSerializer):
    employee = serializers.SerializerMethodField()

    class Meta:
        model = SalaryRecord
        fields = ['id','employee','month','year','base_salary','overtime_pay','attendance_bonus','gross_salary']
    
    def get_employee(self, obj):
        data = {}
        data['id'] = obj.employee.id
        data['employee_id'] = obj.employee.employee_id
        data['department'] = obj.employee.department.name
        data['full_name'] = obj.employee.full_name
        return data
