from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.utils import timezone
from ..submodels.models_timesheet import *
from ..submodels.models_employee import Employee, Department
from .serializers import *
from ..permissions import IsManager, IsEmployee
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from calendar import monthrange


class SalaryPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        next_page = previous_page = None
        if self.page.has_next():
            next_page = self.page.next_page_number()
        if self.page.has_previous():
            previous_page = self.page.previous_page_number()
        return Response({
            'totalRows': self.page.paginator.count,
            'page_size': self.page_size,
            'current_page': self.page.number,
            'next_page': next_page,
            'previous_page': previous_page,
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            },
            'results': data,
        })

class MonthlySalaryRecordForManagerMVS(viewsets.ModelViewSet):
    serializer_class = SalaryRecordForManagerSerializer
    permission_classes = [IsAuthenticated, IsManager]
    pagination_class = SalaryPagination

    @action(methods=['GET'], detail=False, url_path='get_current_month_salary_records', url_name='get_current_month_salary_records')
    def get_current_month_salary_records(self, request):
        try:
            batch_calculate_monthly_salaries()
            department = request.query_params.get('department')
            month = request.query_params.get('month')
            year = request.query_params.get('year')

            salary_records = SalaryRecord.objects.filter(
                employee__is_active=True
            ).order_by('employee__employee_id')
            if department:
                department = Department.objects.get(name=department)
                salary_records = salary_records.filter(employee__department=department)
            if month and year:
                salary_records = salary_records.filter(month=month, year=year)
            
            page = self.paginate_queryset(salary_records)
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.serializer_class(salary_records, many=True)
            return Response(serializer.data)
        except Exception as error:
            print("error_get_monthly_salary_for_manager:", error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
