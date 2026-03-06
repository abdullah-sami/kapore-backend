from django.urls import path
from .views import (
    CustomerRegisterView,
    CustomerLoginView,
    CustomerLogoutView,
    CustomerRefreshView,
    CustomerMeView,
    CustomerAddressListCreateView,
    CustomerAddressDetailView,
)

urlpatterns = [
    # Auth
    path('auth/register/', CustomerRegisterView.as_view()),
    path('auth/login/',    CustomerLoginView.as_view()),
    path('auth/logout/',   CustomerLogoutView.as_view()),
    path('auth/refresh/',  CustomerRefreshView.as_view()),

    # Me
    path('me/',            CustomerMeView.as_view()),

    # Addresses
    path('me/addresses/',          CustomerAddressListCreateView.as_view()),
    path('me/addresses/<uuid:pk>/', CustomerAddressDetailView.as_view()),
]