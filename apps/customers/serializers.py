from rest_framework import serializers
from .models import Customer, CustomerAddress


class CustomerRegisterSerializer(serializers.Serializer):
    email     = serializers.EmailField()
    phone     = serializers.CharField(max_length=20)
    full_name = serializers.CharField(max_length=255)
    password  = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if Customer.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate_phone(self, value):
        if Customer.objects.filter(phone=value).exists():
            raise serializers.ValidationError('An account with this phone already exists.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        customer = Customer(**validated_data)
        customer.set_password(password)
        customer.save()
        return customer


class CustomerLoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Customer
        fields = [
            'id', 'email', 'phone', 'full_name',
            'avatar_url', 'is_verified', 'created_at',
        ]
        read_only_fields = ['id', 'is_verified', 'created_at']


class CustomerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Customer
        fields = ['full_name', 'phone', 'avatar_url']

    def validate_phone(self, value):
        qs = Customer.objects.filter(phone=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('This phone is already in use.')
        return value


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CustomerAddress
        fields = [
            'id', 'label', 'address_line_1', 'address_line_2',
            'city', 'district', 'postal_code', 'country', 'is_default',
        ]
        read_only_fields = ['id']