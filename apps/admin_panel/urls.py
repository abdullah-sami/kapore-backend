from django.urls import path
from .views import (
    AdminLoginView,
    AdminLogoutView,
    AdminRefreshView,
    AdminMeView,
    AdminUserListCreateView,
    AdminUserDetailView,
    ActivityLogListView,
)

urlpatterns = [
    # Auth
    path('auth/login/',   AdminLoginView.as_view()),
    path('auth/logout/',  AdminLogoutView.as_view()),
    path('auth/refresh/', AdminRefreshView.as_view()),

    # Me
    path('me/', AdminMeView.as_view()),

    # User management (superadmin only)
    path('users/',        AdminUserListCreateView.as_view()),
    path('users/<uuid:pk>/', AdminUserDetailView.as_view()),

    # Logs
    path('activity-logs/', ActivityLogListView.as_view()),
]