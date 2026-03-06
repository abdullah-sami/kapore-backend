from django.urls import path
from .views import (
    # Cart
    CartSessionView,
    CartView,
    CartItemCreateView,
    CartItemDetailView,
    CartMergeView,
    # Checkout & coupons
    ApplyCouponView,
    CheckoutView,
    # Customer orders
    CustomerOrderListView,
    CustomerOrderDetailView,
    GuestOrderTrackView,
    # Admin orders
    AdminOrderListView,
    AdminOrderDetailView,
    AdminOrderStatusView,
    # Admin coupons
    AdminCouponListCreateView,
    AdminCouponDetailView,
)

urlpatterns = [
    # ── Cart ─────────────────────────────────────────────
    path('cart/session/',            CartSessionView.as_view()),
    path('cart/',                    CartView.as_view()),
    path('cart/items/',              CartItemCreateView.as_view()),
    path('cart/items/<uuid:pk>/',    CartItemDetailView.as_view()),
    path('cart/merge/',              CartMergeView.as_view()),

    # ── Checkout ─────────────────────────────────────────
    path('checkout/',                CheckoutView.as_view()),
    path('checkout/apply-coupon/',   ApplyCouponView.as_view()),

    # ── Customer orders ──────────────────────────────────
    path('orders/',                              CustomerOrderListView.as_view()),
    path('orders/<str:order_number>/',           CustomerOrderDetailView.as_view()),
    path('orders/track/',                        GuestOrderTrackView.as_view()),

    # ── Admin orders ─────────────────────────────────────
    path('admin/orders/',                        AdminOrderListView.as_view()),
    path('admin/orders/<uuid:pk>/',              AdminOrderDetailView.as_view()),
    path('admin/orders/<uuid:pk>/status/',       AdminOrderStatusView.as_view()),

    # ── Admin coupons ────────────────────────────────────
    path('admin/coupons/',                       AdminCouponListCreateView.as_view()),
    path('admin/coupons/<uuid:pk>/',             AdminCouponDetailView.as_view()),
]