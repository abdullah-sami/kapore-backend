from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from .models import AdminUser


def get_tokens_for_admin(admin: AdminUser) -> dict:
    """
    Generate a JWT token pair for an AdminUser.
    We embed 'token_type': 'admin' so the permission layer
    can distinguish admin tokens from customer tokens.
    """
    refresh = RefreshToken()
    refresh['user_id']    = str(admin.id)
    refresh['email']      = admin.email
    refresh['role']       = admin.role
    refresh['token_type_tag'] = 'admin'   # custom claim

    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }


class AdminJWTAuthentication(JWTAuthentication):
    """
    Custom authentication class that resolves the user
    from AdminUser instead of Django's built-in User model.
    """

    def get_user(self, validated_token):
        try:
            user_id = validated_token['user_id']
            # Only accept tokens tagged as admin
            if validated_token.get('token_type_tag') != 'admin':
                raise InvalidToken('Not an admin token')
        except KeyError:
            raise InvalidToken('Token missing user_id')

        try:
            return AdminUser.objects.get(id=user_id, is_active=True)
        except AdminUser.DoesNotExist:
            raise InvalidToken('Admin user not found or inactive')