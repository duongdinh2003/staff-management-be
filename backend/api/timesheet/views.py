from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.utils import timezone
from ..submodels.models_timesheet import *
from .serializers import *
from ..permissions import IsManager, IsEmployee
from datetime import time, timedelta
from dateutil.relativedelta import relativedelta


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
            employee = Employee.objects.get(user=request.user)
            queryset = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.serializer_class(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)
            
            serializer = self.serializer_class(queryset, many=True, context={'request': request})
            return Response(serializer.data)
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
            current_time = timezone.now().time()
            current_date = timezone.now().date()

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

                timesheet.check_in_time = current_time
                timesheet.status = TimeSheet.Status.INCOMPLETE
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
            current_time = timezone.now().time()
            current_date = timezone.now().date()

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

            if minutes_early > 0:
                timesheet.status = TimeSheet.Status.EARLY_LEAVE
            else:
                timesheet.status = TimeSheet.Status.PRESENT

            timesheet.save()
            return Response({'message': 'Check out successfully!', 'data': TimeSheetSerializer(timesheet).data})
        except Employee.DoesNotExist:
            return Response({'message': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)
        except WorkingShift.DoesNotExist:
            return Response({'message': 'Working shift not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            print("check in error:", error)
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

class TimeSheetEmployeeMVS(viewsets.ModelViewSet):
    serializer_class = TimeSheetSerializer
    permission_classes = [IsAuthenticated, IsEmployee]
    pagination_class = TimeSheetPagination

    @action(methods=['GET'], detail=False, url_path='get_current_month_timesheet_employee', url_name='get_current_month_timesheet_employee')
    def get_current_month_timesheet_employee(self, request):
        try:
            employee = Employee.objects.get(user=request.user)
            current_time = timezone.now()
            queryset = TimeSheet.objects.filter(
                employee=employee,
                date__year=current_time.year,
                date__month=current_time.month,
            ).order_by('date')

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.serializer_class(queryset, many=True)
            return Response(serializer.data)
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
            employee = Employee.objects.get(user=request.user)
            queryset = OvertimeRequest.objects.filter(employee=employee).order_by('-created_at')

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
