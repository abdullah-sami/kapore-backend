from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Customer


def get_tokens_for_customer(customer: Customer) -> dict:
    refresh = RefreshToken()
    refresh['user_id']        = str(customer.id)
    refresh['email']          = customer.email
    refresh['token_type_tag'] = 'customer'

    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }


class CustomerJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token['user_id']
            if validated_token.get('token_type_tag') != 'customer':
                raise InvalidToken('Not a customer token')
        except KeyError:
            raise InvalidToken('Token missing user_id')

        try:
            return Customer.objects.get(id=user_id, is_active=True)
        except Customer.DoesNotExist:
            raise InvalidToken('Customer not found or inactive')