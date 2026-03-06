from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from common.permissions import IsAdminUser, IsSuperAdmin
from .models import AdminUser, ActivityLog
from .serializers import (
    AdminLoginSerializer,
    AdminUserSerializer,
    AdminUserCreateSerializer,
    AdminUserUpdateSerializer,
    ActivityLogSerializer,
)
from .authentication import AdminJWTAuthentication, get_tokens_for_admin


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email    = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            admin = AdminUser.objects.get(email=email, is_active=True)
        except AdminUser.DoesNotExist:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not admin.check_password(password):
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        admin.last_login = timezone.now()
        admin.save(update_fields=['last_login'])

        tokens = get_tokens_for_admin(admin)
        return Response({
            'admin': AdminUserSerializer(admin).data,
            **tokens,
        })


class AdminLogoutView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def post(self, request):
        # Client should discard the token — stateless JWT
        # If blacklisting is needed, add simplejwt blacklist app and blacklist here
        return Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)


class AdminRefreshView(APIView):
    """Thin wrapper — in production use simplejwt's TokenRefreshView directly."""
    permission_classes = [AllowAny]

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError

        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'refresh token required.'}, status=400)

        try:
            token  = RefreshToken(refresh_token)
            # Validate this is an admin token
            if token.get('token_type_tag') != 'admin':
                raise TokenError('Not an admin token')
            return Response({'access': str(token.access_token)})
        except TokenError as e:
            return Response({'detail': str(e)}, status=401)


# ─────────────────────────────────────────────
# Me
# ─────────────────────────────────────────────

class AdminMeView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        return Response(AdminUserSerializer(request.user).data)

    def patch(self, request):
        serializer = AdminUserUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        # Staff cannot change their own role
        if request.user.role == AdminUser.Role.STAFF:
            serializer.validated_data.pop('role', None)
        serializer.save()
        return Response(AdminUserSerializer(request.user).data)


# ─────────────────────────────────────────────
# User management (superadmin only)
# ─────────────────────────────────────────────

class AdminUserListCreateView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsSuperAdmin]

    def get(self, request):
        admins = AdminUser.objects.all().order_by('-created_at')
        return Response(AdminUserSerializer(admins, many=True).data)

    def post(self, request):
        serializer = AdminUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()
        return Response(AdminUserSerializer(admin).data, status=status.HTTP_201_CREATED)


class AdminUserDetailView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsSuperAdmin]

    def get_object(self, pk):
        try:
            return AdminUser.objects.get(pk=pk)
        except AdminUser.DoesNotExist:
            return None

    def patch(self, request, pk):
        admin = self.get_object(pk)
        if not admin:
            return Response({'detail': 'Not found.'}, status=404)
        serializer = AdminUserUpdateSerializer(admin, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AdminUserSerializer(admin).data)


# ─────────────────────────────────────────────
# Activity logs
# ─────────────────────────────────────────────

class ActivityLogListView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        from common.pagination import StandardPagination
        logs      = ActivityLog.objects.select_related('admin').order_by('-timestamp')
        paginator = StandardPagination()
        page      = paginator.paginate_queryset(logs, request)
        serializer = ActivityLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)