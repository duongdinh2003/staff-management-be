from rest_framework import serializers
from ..submodels.models_auth import User
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already exists.')
        return value
    
    def save(self, request):
        username = self.validated_data['username']
        password = self.validated_data['password']
        user = User.objects.create_user(username=username, password=password)
        return user

class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise AuthenticationFailed('User account is disabled.')
                user.last_login = timezone.localtime(timezone.now())
                user.save()
                return {'user': user}
            else:
                raise AuthenticationFailed('Invalid credentials.')
        else:
            raise serializers.ValidationError('Must include "username" and "password".')

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({'message': 'Old password is incorrect.'})
        return data
    
    def update(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user