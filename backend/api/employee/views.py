from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from ..submodels.models_employee import Department, Position, Employee
from .serializers import *
from ..permissions import IsManager, IsEmployee


class EmployeeListPagination(PageNumberPagination):
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

class DepartmentDropdownView(APIView):
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Department.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

class PositionDropDownView(APIView):
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Position.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

class EmployeeAccountMVS(viewsets.ModelViewSet):
    serializer_class = EmployeeAccountSerializer
    permission_classes = [IsAuthenticated, IsManager]

    @action(methods=['POST'], detail=False, url_path='create_employee_account', url_name='create_employee_account')
    def create_employee_account(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save(request)
                return Response({"message": "Create employee account successfully."}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print("create_employee_account_error:", error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)

class UpdateEmployeeProfileView(APIView):
    serializer_class = UpdateEmployeeProfileSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.update(request)
                return Response({"message": "Update profile successfully."})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print("update_employee_profile_error:", error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)

class EmployeeProfileView(APIView):
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request):
        try:
            profile = Employee.objects.get(user=request.user)
            serializer = self.serializer_class(profile, context={'request': request})
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

class UploadEmployeeAvatarView(APIView):
    serializer_class = UploadEmployeeAvatarSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            data = {}
            if serializer.is_valid():
                serializer.update_avatar(request)
                data['message'] = 'Upload avatar successfully.'
                return Response(data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print("upload avatar error:", error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)


class EmployeeManagementMVS(viewsets.ModelViewSet):
    serializer_class = EmployeeManagementSerializer
    permission_classes = [IsAuthenticated, IsManager]
    pagination_class = EmployeeListPagination

    @action(methods=['GET'], detail=False, url_path='get_all_employees_of_deparment', url_name='get_all_employees_of_deparment')
    def get_all_employees_of_deparment(self, request):
        try:
            department = request.query_params.get('department')
            queryset = Employee.objects.filter(is_active=True).order_by('employee_id')

            if department:
                department = Department.objects.get(name=department)
                queryset = queryset.filter(department=department)
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.serializer_class(queryset, many=True)
            return Response(serializer.data)
        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(methods=['DELETE'], detail=False, url_path='delete_employee_account', url_name='delete_employee_account')
    def delete_employee_account(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                if serializer.delete_account(request):
                    return Response({"message": "Delete employee account successfully."})
                return Response({"message": "Delete employee account failed."}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print("delete account error:", error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
