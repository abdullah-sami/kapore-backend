from django.urls import path
from .views import (
    # Storefront
    PaymentStatusView,
    PaymentSubmitView,
    # Admin — payments
    AdminPaymentListView,
    AdminPaymentDetailView,
    AdminPaymentVerifyView,
    AdminPaymentRejectView,
    # Admin — refunds
    AdminRefundListCreateView,
    AdminRefundDetailView,
    # Admin — expenses
    AdminExpenseCategoryView,
    AdminExpenseListCreateView,
    AdminExpenseDetailView,
)

urlpatterns = [
    # ── Storefront ───────────────────────────────────────
    path('payments/<str:order_number>/',         PaymentStatusView.as_view()),
    path('payments/<str:order_number>/submit/',  PaymentSubmitView.as_view()),

    # ── Admin — payments ─────────────────────────────────
    path('admin/payments/',                      AdminPaymentListView.as_view()),
    path('admin/payments/<uuid:pk>/',            AdminPaymentDetailView.as_view()),
    path('admin/payments/<uuid:pk>/verify/',     AdminPaymentVerifyView.as_view()),
    path('admin/payments/<uuid:pk>/reject/',     AdminPaymentRejectView.as_view()),

    # ── Admin — refunds ──────────────────────────────────
    path('admin/refunds/',                       AdminRefundListCreateView.as_view()),
    path('admin/refunds/<uuid:pk>/',             AdminRefundDetailView.as_view()),

    # ── Admin — expense categories ───────────────────────
    path('admin/expense-categories/',            AdminExpenseCategoryView.as_view()),

    # ── Admin — expenses ─────────────────────────────────
    path('admin/expenses/',                      AdminExpenseListCreateView.as_view()),
    path('admin/expenses/<uuid:pk>/',            AdminExpenseDetailView.as_view()),
]