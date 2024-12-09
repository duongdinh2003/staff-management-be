from rest_framework import serializers
from django.db import transaction
from ..submodels.models_employee import Department, Position, Employee
from ..login.serializers import RegisterSerializer
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.mail import EmailMessage


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']

class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['id', 'name']

class EmployeeAccountSerializer(serializers.ModelSerializer):
    user = RegisterSerializer()
    department_id = serializers.IntegerField(required=True)
    position_id = serializers.IntegerField(required=True)

    class Meta:
        model = Employee
        fields = [
            'id',
            'user',
            'department_id',
            'position_id',
            'full_name',
            'address',
            'join_date'
        ]
    
    def validate_department_id(self, value):
        if not Department.objects.filter(id=value).exists():
            raise serializers.ValidationError({"error": "Department does not exist."})
        return value
    
    @transaction.atomic
    def save(self, request):
        try:
            user_data = self.validated_data.pop('user')
            user_serializer = RegisterSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.save(request)

            department_id = self.validated_data['department_id']
            position_id = self.validated_data['position_id']
            full_name = self.validated_data['full_name']
            address = self.validated_data['address']
            join_date = self.validated_data['join_date']
            department = Department.objects.get(id=department_id)
            position = Position.objects.get(id=position_id)

            employee = Employee.objects.create(
                user=user,
                department=department,
                position=position,
                full_name=full_name,
                address=address,
                join_date=join_date
            )
            employee_group = Group.objects.get(name=settings.GROUP_NAME['EMPLOYEE'])
            employee_group.user_set.add(user)

            email_msg = EmailMessage(
                subject=settings.EMAIL_TITLE,
                body=f'Your username is: {user.username}<br>Your password is: {user_data["password"]}',
                from_email=settings.EMAIL_HOST_USER,
                to=[user.email]
            )
            email_msg.content_subtype = "html"
            email_msg.send()
            return employee
        except Exception as error:
            print("add_employee_profile_error:", error)
            return None

class UpdateEmployeeProfileSerializer(serializers.ModelSerializer):
    gender = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)

    class Meta:
        model = Employee
        fields = ['id', 'full_name', 'date_of_birth', 'gender', 'address', 'phone_number', 'email']

    def update(self, request):
        try:
            full_name = self.validated_data['full_name']
            date_of_birth = self.validated_data['date_of_birth']
            gender = self.validated_data['gender']
            address = self.validated_data['address']
            phone_number = self.validated_data['phone_number']
            profile = Employee.objects.get(user=request.user)
            user = request.user
            profile.full_name = full_name
            profile.date_of_birth = date_of_birth
            if gender == "Nam":
                profile.gender = profile.Gender.MALE
            elif gender == "Nữ":
                profile.gender = profile.Gender.FEMALE
            else:
                profile.gender = profile.Gender.OTHER
            profile.address = address
            profile.phone_number = phone_number
            user.email = self.validated_data['email']
            profile.save()
            user.save()
            return profile
        except Exception as error:
            print("update_employee_profile_error:", error)
            return None

class EmployeeProfileSerializer(serializers.ModelSerializer):
    department = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id',
            'department',
            'position',
            'employee_id',
            'full_name',
            'date_of_birth',
            'gender',
            'address',
            'phone_number',
            'email',
            'avatar'
        ]

    def get_department(self, obj):
        return obj.department.name
    
    def get_position(self, obj):
        return obj.position.name
    
    def get_gender(self, obj):
        if obj.gender == Employee.Gender.MALE:
            return "Nam"
        if obj.gender == Employee.Gender.FEMALE:
            return "Nữ"
        return "Khác"
    
    def get_email(self, obj):
        return obj.user.email
    
    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url)
        return None

class UploadEmployeeAvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=True)

    class Meta:
        model = Employee
        fields = ['avatar']

    def update_avatar(self, request):
        try:
            avatar = self.validated_data['avatar']
            profile = Employee.objects.get(user=request.user)
            profile.avatar = avatar
            profile.save()
            return profile
        except Exception as error:
            print("upload_employee_avatar_error:", error)
            return None

class EmployeeManagementSerializer(serializers.ModelSerializer):
    department = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id',
            'department',
            'position',
            'employee_id',
            'full_name',
            'join_date',
            'gender',
            'address',
            'phone_number',
            'email'
        ]

    def get_department(self, obj):
        return obj.department.name
    
    def get_position(self, obj):
        return obj.position.name
    
    def get_gender(self, obj):
        if obj.gender == Employee.Gender.MALE:
            return "Nam"
        if obj.gender == Employee.Gender.FEMALE:
            return "Nữ"
        return "Khác"
    
    def get_email(self, obj):
        return obj.user.email
    
    def delete_account(self, request):
        try:
            employee_id = request.query_params.get('employee_id')
            employee = Employee.objects.get(employee_id=employee_id)
            employee.is_active = False
            user = employee.user
            user.is_active = False
            employee.save()
            user.save()
            return True
        except Employee.DoesNotExist:
            return False
