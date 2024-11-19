from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.contrib.auth.models import User, Group
from .serializers import *


class RegisterView(APIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                user = serializer.save(request=request) 

                refresh = RefreshToken.for_user(user)
                
                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
                return Response({
                    "tokens": tokens
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print("register_error", error)
            return Response({"message": "An error occurred on the server.", "details": str(error)}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView): 
    serializer_class = LoginSerializer

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data['user']
                groups = Group.objects.filter(user=user)
                _groups = []
                for g in groups:
                    _groups.append(g.name)
                refresh = RefreshToken.for_user(user)
                return Response(
                    {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'groups': _groups
                    },
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print("login_error", error)
            return Response({"message": "An error occurred on the server.", "details": str(error)}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            serializer = self.serializer_class(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.update()
                return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            print("change_password_error", error)
            return Response({"message": "An error occurred on the server.", "details": str(error)}, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({
                "detail": "Refresh token is not valid or expired."
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        response_data = serializer.validated_data
        return Response(response_data, status=status.HTTP_200_OK)
