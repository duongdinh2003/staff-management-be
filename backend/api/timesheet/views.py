from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.contrib.auth.models import User
from ..submodels.models_timesheet import *
from .serializers import *
from ..permissions import IsManager, IsEmployee


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

class ListLeaveRequestEmployeeView(APIView):
    serializer_class = ListLeaveRequestEmployeeSerializer
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request):
        try:
            employee = Employee.objects.get(user=request.user)
            queryset = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')
            serializer = self.serializer_class(queryset, many=True, context={'request': request})
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

class ListLeaveRequestManagerView(APIView):
    serializer_class = ListLeaveRequestManagerSerializer
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        queryset = LeaveRequest.objects.filter(status=LeaveRequest.Status.PENDING).order_by('-created_at')
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
