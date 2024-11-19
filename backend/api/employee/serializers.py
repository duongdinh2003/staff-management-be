from rest_framework import serializers
from django.db import transaction
from ..submodels.models_employee import Department, Position, Employee
from ..login.serializers import RegisterSerializer
from django.contrib.auth.models import User, Group
from django.conf import settings


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']

class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['id', 'name']

class EmployeeManagementSerializer(serializers.ModelSerializer):
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
            'join_date',
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
            if gender == "Nữ":
                profile.gender = profile.Gender.FEMALE
            if gender == "Khác":
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

    class Meta:
        model = Employee
        fields = ['id','department','position','employee_id','full_name','date_of_birth','gender','address','phone_number','email']

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
