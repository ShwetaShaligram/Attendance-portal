from rest_framework import serializers
from .models import CustomUser, Attendance, RegularizationRequest
from django.contrib.auth.password_validation import validate_password

# ✅ 1. Register Serializer
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'password', 'confirm_password', 'role', 'manager']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        if validated_data.get('manager') == '':
            validated_data['manager'] = None
        user = CustomUser.objects.create_user(**validated_data)
        return user


# ✅ 2. Manager dropdown
class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name']


# ✅ 3. Attendance Serializer
class AttendanceSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    is_late = serializers.SerializerMethodField()
    is_regularized = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'user', 'user_name', 'date', 'check_in', 'check_out', 'total_hours',
            'status', 'is_late', 'is_regularized'
        ]

    def get_status(self, obj):
        return obj.status_color()

    def get_is_late(self, obj):
        return obj.is_late()

    def get_is_regularized(self, obj):
        return obj.is_regularized()


# ✅ 4. Regularization Request Serializer
class RegularizationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True, default='---')

    class Meta:
        model = RegularizationRequest
        fields = [
            'id', 'user', 'user_name', 'date', 'reason',
            'status', 'created_at', 'approved_by', 'approved_by_name'
        ]
        read_only_fields = ['user', 'status', 'created_at', 'approved_by']


# ✅ 5. User List for HR
class UserSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.full_name', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'role', 'manager', 'manager_name']
