from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from ..submodels.models_timesheet import *
from ..submodels.models_employee import Department
from .serializers import *
from ..permissions import IsManager, IsEmployee
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from calendar import monthrange


class ListItemPagination(PageNumberPagination):
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

class TimeSheetPagination(PageNumberPagination):
    page_size = 11
    page_size_query_param = 'page_size'
    max_page_size = 50

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


# ============================================= Leave request =================================================
class SendLeaveRequestView(APIView):
    serializer_class = SendLeaveRequestSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            data = {}
            if serializer.is_valid(raise_exception=True):
                serializer.send_request(request)
                data['message'] = 'Send leave request successfully.'
                return Response(data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print("send leave request error:", error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)

class ListLeaveRequestEmployeeView(viewsets.ReadOnlyModelViewSet):
    serializer_class = ListLeaveRequestEmployeeSerializer
    permission_classes = [IsAuthenticated, IsEmployee]
    pagination_class = ListItemPagination

    @action(methods=['GET'], detail=False, url_path='list_leave_requests_employee', url_name='list_leave_requests_employee')
    def list_leave_requests_employee(self, request):
        try:
            current_date = timezone.localtime(timezone.now()).date()
            start_of_month = current_date.replace(day=1)
            end_of_month = (start_of_month + relativedelta(months=1)) - timedelta(days=1)

            employee = Employee.objects.get(user=request.user)
            queryset = LeaveRequest.objects.filter(
                employee=employee,
                from_date__lte=end_of_month,
                to_date__gte=start_of_month
            ).order_by('-created_at')

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.serializer_class(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)
            
            serializer = self.serializer_class(queryset, many=True, context={'request': request})
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
    
    @action(methods=['GET'], detail=False, url_path='get_leave_count_in_current_month', url_name='get_leave_count_in_current_month')
    def get_leave_count_in_current_month(self, request):
        try:
            current_date = timezone.localtime(timezone.now()).date()
            start_of_month = current_date.replace(day=1)
            end_of_month = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            employee = Employee.objects.get(user=request.user)
            leave_requests_count = LeaveRequest.objects.filter(
                Q(employee=employee) &
                Q(status=LeaveRequest.Status.APPROVED) &
                Q(from_date__lte=end_of_month) & Q(to_date__gte=start_of_month)
            ).count()
            return Response({"leave_requests_count": leave_requests_count})
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

class ListLeaveRequestManagerView(viewsets.ReadOnlyModelViewSet):
    serializer_class = ListLeaveRequestManagerSerializer
    permission_classes = [IsAuthenticated, IsManager]
    pagination_class = ListItemPagination

    @action(methods=['GET'], detail=False, url_path='list_leave_requests_manager', url_name='list_leave_requests_manager')
    def list_leave_requests_manager(self, request):
        queryset = LeaveRequest.objects.filter(status=LeaveRequest.Status.PENDING).order_by('-created_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(serializer.data)

class ApproveLeaveRequestMVS(viewsets.ModelViewSet):
    serializer_class = ApproveLeaveRequestSerializer
    permission_classes = [IsAuthenticated, IsManager]

    @action(methods=['POST'], detail=False, url_path='approve_leave_request', url_name='approve_leave_request')
    def approve_leave_request(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            data = {}
            if serializer.is_valid():
                serializer.approve_request(request)
                data['message'] = 'Approved leave request of employee successfully.'
                return Response(data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print('approve leave request employee error:', error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=['POST'], detail=False, url_path='reject_leave_request', url_name='reject_leave_request')
    def reject_leave_request(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            data = {}
            if serializer.is_valid():
                serializer.reject_request(request)
                data['message'] = 'Rejected leave request of employee successfully.'
                return Response(data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print('reject leave request employee error:', error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)


# ========================================= Timesheet =============================================
class CheckInAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request):
        try:
            employee = Employee.objects.get(user=request.user)
            shift_type = request.data.get('shift_type')

            current = timezone.localtime(timezone.now())
            if (shift_type == 'AFTERNOON' and current.weekday() == 5) or current.weekday() == 6:
                return Response({"message": "This is not the time to check in this shift."}, status=status.HTTP_400_BAD_REQUEST)
            
            current_time = current.time()
            current_date = current.date()

            shift = WorkingShift.objects.get(shift_type=shift_type)

            if not (current_time >= shift.start_time and current_time <= shift.end_time):
                return Response({"message": "This is not the time to check in this shift."}, status=status.HTTP_400_BAD_REQUEST)

            timesheet, created = TimeSheet.objects.get_or_create(
                employee=employee,
                date=current_date,
                shift=shift,
                defaults={
                    'check_in_time': current_time,
                    'status': TimeSheet.Status.INCOMPLETE
                }
            )

            if not created:
                if timesheet.check_in_time:
                    return Response({'message': 'You already checked in for this shift!'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                start_time = timezone.datetime.combine(current_date, shift.start_time)
                start_time = timezone.make_aware(start_time)
                if current > (start_time + timedelta(minutes=15)):
                    timesheet.status = TimeSheet.Status.LATE
                timesheet.save()

            return Response({'message': 'Check in successfully!', 'data': TimeSheetSerializer(timesheet).data})
        except Employee.DoesNotExist:
            return Response({'message': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)
        except WorkingShift.DoesNotExist:
            return Response({'message': 'Working shift not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            print("check in error:", error)
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)


class CheckOutAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request):
        try:
            employee = Employee.objects.get(user=request.user)
            shift_type = request.data.get('shift_type')
            current_time = timezone.localtime(timezone.now()).time()
            current_date = timezone.localtime(timezone.now()).date()

            shift = WorkingShift.objects.get(shift_type=shift_type)

            timesheet = TimeSheet.objects.filter(
                employee=employee,
                date=current_date,
                shift=shift
            ).first()

            if not timesheet:
                return Response({'message': 'You have not check in for this shift!'}, status=status.HTTP_400_BAD_REQUEST)

            if not timesheet.check_in_time:
                return Response({'message': 'You have not check in for this shift!'}, status=status.HTTP_400_BAD_REQUEST)
            
            if timesheet.check_out_time:
                return Response({'message': 'You already checked out for this shift!'}, status=status.HTTP_400_BAD_REQUEST)

            shift_end_time = timezone.datetime.combine(current_date, shift.end_time)
            check_out_time = timezone.datetime.combine(current_date, current_time)
            minutes_early = (shift_end_time - check_out_time).total_seconds() / 60

            if minutes_early > 30:
                return Response({"message": "You are only allowed to leave 30 minutes early."}, status=status.HTTP_400_BAD_REQUEST)
            
            start_of_month = current_date.replace(day=1)
            end_of_month = (start_of_month + relativedelta(months=1)) - timedelta(days=1)

            early_leave_count = TimeSheet.objects.filter(
                employee=employee,
                date__range=(start_of_month, end_of_month),
                status=TimeSheet.Status.EARLY_LEAVE
            ).count()

            if early_leave_count >= 2:
                return Response({"message": "You are only allowed to leave early a maximum of 2 times a month!"}, status=status.HTTP_400_BAD_REQUEST)
            
            timesheet.check_out_time = current_time

            if not timesheet.status == TimeSheet.Status.LATE:
                if minutes_early > 0:
                    timesheet.status = TimeSheet.Status.EARLY_LEAVE
                else:
                    timesheet.status = TimeSheet.Status.PRESENT

            timesheet.save()
            data = {}
            data['timesheet'] = TimeSheetSerializer(timesheet).data
            data['early_leave_count'] = early_leave_count
            return Response({'message': 'Check out successfully!', 'data': data})
        except Employee.DoesNotExist:
            return Response({'message': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)
        except WorkingShift.DoesNotExist:
            return Response({'message': 'Working shift not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            print("check in error:", error)
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

class TimeSheetEmployeeMVS(viewsets.ModelViewSet):
    serializer_class = ShiftDetailSerializer
    permission_classes = [IsAuthenticated, IsEmployee]
    pagination_class = TimeSheetPagination

    @action(methods=['GET'], detail=False, url_path='get_current_month_timesheet_employee', url_name='get_current_month_timesheet_employee')
    def get_current_month_timesheet_employee(self, request):
        try:
            employee = Employee.objects.get(user=request.user)
            current_date = timezone.localtime(timezone.now()).date()
            start_date = current_date.replace(day=1)
            _, last_day = monthrange(current_date.year, current_date.month)
            end_date = current_date.replace(day=last_day)

            timesheets = TimeSheet.objects.filter(employee=employee, date__range=(start_date, end_date))

            all_days = [
                start_date + timedelta(days=n)
                for n in range((end_date - start_date).days + 1)
            ]

            grouped_data = []
            for single_date in all_days:
                day_timesheets = timesheets.filter(date=single_date)
                morning_shift = day_timesheets.filter(shift__shift_type=WorkingShift.ShiftType.MORNING).first()
                afternoon_shift = day_timesheets.filter(shift__shift_type=WorkingShift.ShiftType.AFTERNOON).first()
                overtime_shift = day_timesheets.filter(is_overtime=True).first()

                grouped_data.append({
                    "date": single_date,
                    "morning_shift": self.serializer_class(morning_shift).data if morning_shift else None,
                    "afternoon_shift": self.serializer_class(afternoon_shift).data if afternoon_shift else None,
                    "overtime_shift": self.serializer_class(overtime_shift).data if overtime_shift else None,
                })

            paginator = self.pagination_class()
            paginated_data = paginator.paginate_queryset(grouped_data, request)

            return paginator.get_paginated_response(paginated_data)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
    
    @action(methods=['GET'], detail=False, url_path='get_daily_timesheet_employee', url_name='get_daily_timesheet_employee')
    def get_daily_timesheet_employee(self, request):
        try:
            employee = Employee.objects.get(user=request.user)
            current_date = timezone.localtime(timezone.now()).date()
            timesheets = TimeSheet.objects.filter(employee=employee, date=current_date)

            morning_shift = timesheets.filter(shift__shift_type=WorkingShift.ShiftType.MORNING).first()
            afternoon_shift = timesheets.filter(shift__shift_type=WorkingShift.ShiftType.AFTERNOON).first()
            overtime_shift = timesheets.filter(is_overtime=True).first()

            start_of_month = current_date.replace(day=1)
            end_of_month = (start_of_month + relativedelta(months=1)) - timedelta(days=1)

            early_leave_count = TimeSheet.objects.filter(
                employee=employee,
                date__range=(start_of_month, end_of_month),
                status=TimeSheet.Status.EARLY_LEAVE
            ).count()

            data = {
                "date": current_date,
                "early_leave_count": early_leave_count,
                "morning_shift": self.serializer_class(morning_shift).data if morning_shift else None,
                "afternoon_shift": self.serializer_class(afternoon_shift).data if afternoon_shift else None,
                "overtime_shift": self.serializer_class(overtime_shift).data if overtime_shift else None,
            }

            return Response(data)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)


# ============================================== Overtime request ===================================================
class SendOvertimeRequestView(APIView):
    serializer_class = SendOvertimeRequestSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            data = {}
            if serializer.is_valid(raise_exception=True):
                serializer.send_request(request)
                data['message'] = 'Send overtime request successfully.'
                return Response(data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print("send overtime request error:", error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)

class ListOvertimeRequestEmployeeView(viewsets.ReadOnlyModelViewSet):
    serializer_class = ListOvertimeRequestEmployeeSerializer
    permission_classes = [IsAuthenticated, IsEmployee]
    pagination_class = ListItemPagination

    @action(methods=['GET'], detail=False, url_path='list_overtime_requests_employee', url_name='list_overtime_requests_employee')
    def list_overtime_requests_employee(self, request):
        try:
            current_date = timezone.localtime(timezone.now()).date()
            start_of_month = current_date.replace(day=1)
            end_of_month = (start_of_month + relativedelta(months=1)) - timedelta(days=1)
            
            employee = Employee.objects.get(user=request.user)
            queryset = OvertimeRequest.objects.filter(
                employee=employee,
                date__range=(start_of_month, end_of_month)
            ).order_by('-created_at')

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.serializer_class(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)
            
            serializer = self.serializer_class(queryset, many=True, context={'request': request})
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

class ListOvertimeRequestManagerView(viewsets.ReadOnlyModelViewSet):
    serializer_class = ListOvertimeRequestManagerSerializer
    permission_classes = [IsAuthenticated, IsManager]
    pagination_class = ListItemPagination

    @action(methods=['GET'], detail=False, url_path='list_overtime_requests_manager', url_name='list_overtime_requests_manager')
    def list_overtime_requests_manager(self, request):
        queryset = OvertimeRequest.objects.filter(status=OvertimeRequest.Status.PENDING).order_by('-created_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(serializer.data)

class ApproveOvertimeRequestMVS(viewsets.ModelViewSet):
    serializer_class = ApproveOvertimeRequestSerializer
    permission_classes = [IsAuthenticated, IsManager]

    @action(methods=['POST'], detail=False, url_path='approve_overtime_request', url_name='approve_overtime_request')
    def approve_overtime_request(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            data = {}
            if serializer.is_valid():
                serializer.approve_request(request)
                data['message'] = 'Approved overtime request of employee successfully.'
                return Response(data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print('approve overtime request employee error:', error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=['POST'], detail=False, url_path='reject_overtime_request', url_name='reject_overtime_request')
    def reject_overtime_request(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            data = {}
            if serializer.is_valid():
                serializer.reject_request(request)
                data['message'] = 'Rejected overtime request of employee successfully.'
                return Response(data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print('reject overtime request employee error:', error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================ Timesheet overtime ===============================================
class OvertimeCheckInAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request):
        try:
            employee = Employee.objects.get(user=request.user)
            current_time = timezone.localtime(timezone.now()).time()
            current_date = timezone.localtime(timezone.now()).date()

            overtime_request = OvertimeRequest.objects.filter(
                employee=employee,
                date=current_date,
                status=OvertimeRequest.Status.APPROVED
            ).first()
            if not overtime_request:
                return Response({"message": "Cannot check in with unregistered overtime."}, status=status.HTTP_400_BAD_REQUEST)

            timesheet, created = TimeSheet.objects.get_or_create(
                employee=employee,
                date=current_date,
                is_overtime=True
            )

            if timesheet.check_in_time:
                return Response({'message': 'You already checked in for overtime!'}, status=status.HTTP_400_BAD_REQUEST)
            
            timesheet.check_in_time = current_time
            timesheet.status = TimeSheet.Status.INCOMPLETE
            timesheet.save()

            return Response({'message': 'Check in overtime successfully!', 'data': TimeSheetSerializer(timesheet).data})
        except Employee.DoesNotExist:
            return Response({'message': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            print("check in overtime error:", error)
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)


class OvertimeCheckOutAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request):
        try:
            employee = Employee.objects.get(user=request.user)
            current_time = timezone.localtime(timezone.now()).time()
            current_date = timezone.localtime(timezone.now()).date()

            timesheet = TimeSheet.objects.filter(
                employee=employee,
                date=current_date,
                is_overtime=True
            ).first()

            if not timesheet:
                return Response({'message': 'You have not checked in overtime today!'}, status=status.HTTP_400_BAD_REQUEST)
            
            if timesheet.check_out_time:
                return Response({'message': 'You have checked out overtime today!'}, status=status.HTTP_400_BAD_REQUEST)
            
            timesheet.check_out_time = current_time

            start_time = datetime.combine(current_date, timesheet.check_in_time)
            end_time = datetime.combine(current_date, current_time)
            delta = end_time - start_time
            overtime_hours = delta.total_seconds() / 3600

            timesheet.overtime_hours = round(overtime_hours, 2)
            timesheet.status = TimeSheet.Status.PRESENT
            timesheet.save()

            return Response({'message': 'Check out overtime successfully!', 'data': TimeSheetSerializer(timesheet).data})
        except Employee.DoesNotExist:
            return Response({'message': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            print("check out overtime error:", error)
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)


class TrackingTimeEmployeeManagementMVS(viewsets.ModelViewSet):
    serializer_class = TrackingTimeEmployeeManagementSerializer
    permission_classes = [IsAuthenticated, IsManager]
    pagination_class = ListItemPagination

    @action(methods=['GET'], detail=False, url_path='get_tracking_time_employee', url_name='get_tracking_time_employee')
    def get_tracking_time_employee(self, request):
        try:
            department = request.query_params.get('department')
            month = request.query_params.get('month')
            year = request.query_params.get('year')
            queryset = EmployeeEvaluation.objects.filter(
                employee__is_active=True
            ).order_by('employee_id')
            if department:
                department = Department.objects.get(name=department)
                queryset = queryset.filter(employee__department=department)
            if month and year:
                queryset = queryset.filter(month=month, year=year)

            current_date = timezone.localtime(timezone.now()).date()
            context = {
                'month': int(month) if month else current_date.month,
                'year': int(year) if year else current_date.year
            }
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.serializer_class(page, many=True, context=context)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.serializer_class(queryset, many=True, context=context)
            return Response(serializer.data)
        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(methods=['POST'], detail=False, url_path='manager_evaluate_employee', url_name='manager_evaluate_employee')
    def manager_evaluate_employee(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.evaluate_employee(request)
                return Response({"message": "Evaluated employee successfully."})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print("error evaluate employee:", error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
