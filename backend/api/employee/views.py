from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.contrib.auth.models import User
from ..submodels.models_employee import Department, Position, Employee
from .serializers import *


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

class EmployeeManagementMVS(viewsets.ModelViewSet):
    serializer_class = EmployeeManagementSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = Employee.objects.get(user=request.user)
            serializer = self.serializer_class(profile)
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
