from rest_framework import serializers
from .models import AdminUser, ActivityLog


class AdminLoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AdminUser
        fields = ['id', 'email', 'full_name', 'role', 'is_active', 'last_login', 'created_at']
        read_only_fields = ['id', 'last_login', 'created_at']


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model  = AdminUser
        fields = ['email', 'full_name', 'role', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        admin    = AdminUser(**validated_data)
        admin.set_password(password)
        admin.save()
        return admin


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AdminUser
        fields = ['full_name', 'role', 'is_active']


class ActivityLogSerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='admin.full_name', read_only=True)

    class Meta:
        model  = ActivityLog
        fields = ['id', 'admin_name', 'action', 'ip_address', 'timestamp']