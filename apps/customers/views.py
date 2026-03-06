from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from common.permissions import IsCustomer
from .models import Customer, CustomerAddress
from .serializers import (
    CustomerRegisterSerializer,
    CustomerLoginSerializer,
    CustomerSerializer,
    CustomerUpdateSerializer,
    CustomerAddressSerializer,
)
from .authentication import CustomerJWTAuthentication, get_tokens_for_customer


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

class CustomerRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()
        tokens   = get_tokens_for_customer(customer)
        return Response(
            {'customer': CustomerSerializer(customer).data, **tokens},
            status=status.HTTP_201_CREATED,
        )


class CustomerLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email    = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            customer = Customer.objects.get(email=email, is_active=True)
        except Customer.DoesNotExist:
            return Response({'detail': 'Invalid credentials.'}, status=401)

        if not customer.check_password(password):
            return Response({'detail': 'Invalid credentials.'}, status=401)

        tokens = get_tokens_for_customer(customer)
        return Response({'customer': CustomerSerializer(customer).data, **tokens})


class CustomerLogoutView(APIView):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes     = [IsCustomer]

    def post(self, request):
        return Response({'detail': 'Logged out.'})


class CustomerRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError

        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'refresh token required.'}, status=400)

        try:
            token = RefreshToken(refresh_token)
            if token.get('token_type_tag') != 'customer':
                raise TokenError('Not a customer token')
            return Response({'access': str(token.access_token)})
        except TokenError as e:
            return Response({'detail': str(e)}, status=401)


# ─────────────────────────────────────────────
# Me
# ─────────────────────────────────────────────

class CustomerMeView(APIView):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes     = [IsCustomer]

    def get(self, request):
        return Response(CustomerSerializer(request.user).data)

    def patch(self, request):
        serializer = CustomerUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CustomerSerializer(request.user).data)


# ─────────────────────────────────────────────
# Addresses
# ─────────────────────────────────────────────

class CustomerAddressListCreateView(APIView):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes     = [IsCustomer]

    def get(self, request):
        # select_related not needed here (address already scoped to customer)
        addresses  = CustomerAddress.objects.filter(customer=request.user)
        serializer = CustomerAddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CustomerAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        address = serializer.save(customer=request.user)
        return Response(CustomerAddressSerializer(address).data, status=201)


class CustomerAddressDetailView(APIView):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes     = [IsCustomer]

    def get_object(self, pk, customer):
        try:
            return CustomerAddress.objects.get(pk=pk, customer=customer)
        except CustomerAddress.DoesNotExist:
            return None

    def patch(self, request, pk):
        address = self.get_object(pk, request.user)
        if not address:
            return Response({'detail': 'Not found.'}, status=404)
        serializer = CustomerAddressSerializer(address, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CustomerAddressSerializer(address).data)

    def delete(self, request, pk):
        address = self.get_object(pk, request.user)
        if not address:
            return Response({'detail': 'Not found.'}, status=404)
        address.delete()
        return Response(status=204)