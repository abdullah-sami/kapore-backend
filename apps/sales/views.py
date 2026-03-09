from django.shortcuts import render

# Create your views here.
from decimal import Decimal
from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from common.permissions import IsAdminUser, IsCustomer
from common.pagination import StandardPagination
from apps.admin_panel.authentication import AdminJWTAuthentication
from apps.customers.authentication import CustomerJWTAuthentication
from apps.inventory.models import ProductVariant

from .models import Cart, CartItem, BillingInfo, Coupon, Order, OrderItem, OrderStatusLog
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    CartItemCreateSerializer,
    CartItemUpdateSerializer,
    CheckoutSerializer,
    ApplyCouponSerializer,
    CouponSerializer,
    OrderSerializer,
    OrderListSerializer,
    OrderStatusUpdateSerializer,
    GuestOrderTrackSerializer,
)
from .utils import generate_order_number, build_variant_label


# ─────────────────────────────────────────────
# Cart helpers
# ─────────────────────────────────────────────

def get_cart(request):
    """
    Resolve the cart for either a logged-in customer or a guest.
    - Logged-in: uses customer FK
    - Guest: uses X-Cart-Session header
    Returns (cart | None, session_key | None)
    """
    if request.user and request.user.is_authenticated and not hasattr(request.user, 'role'):
        cart, _ = Cart.objects.get_or_create(customer=request.user)
        return cart, str(cart.session_key)

    session_key = request.headers.get('X-Cart-Session')
    if not session_key:
        return None, None
    try:
        cart = Cart.objects.get(session_key=session_key)
        return cart, session_key
    except Cart.DoesNotExist:
        return None, session_key


# ─────────────────────────────────────────────
# Cart session (guest init)
# ─────────────────────────────────────────────

class CartSessionView(APIView):
    """
    POST /cart/session/
    Issues a new session_key for guest carts.
    Frontend stores this in localStorage and sends it as X-Cart-Session header.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        cart = Cart.objects.create()
        return Response({'session_key': str(cart.session_key)}, status=201)


# ─────────────────────────────────────────────
# Cart — view & manage items
# ─────────────────────────────────────────────

class CartView(APIView):
    permission_classes = [AllowAny]

    def get_authenticators(self):
        # Try customer JWT but don't fail — guests have no token
        return [CustomerJWTAuthentication()]

    def get(self, request):
        cart, _ = get_cart(request)
        if not cart:
            return Response({'detail': 'No cart found. POST /cart/session/ to start.'}, status=404)
        cart_qs = (
            Cart.objects
            .prefetch_related(
                'items__variant__stock',
                'items__variant__product__images',
            )
            .get(pk=cart.pk)
        )
        return Response(CartSerializer(cart_qs).data)


class CartItemCreateView(APIView):
    permission_classes = [AllowAny]

    def get_authenticators(self):
        return [CustomerJWTAuthentication()]

    def post(self, request):
        cart, _ = get_cart(request)
        if not cart:
            return Response({'detail': 'Cart session required.'}, status=400)

        serializer = CartItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variant_id = serializer.validated_data['variant']
        quantity   = serializer.validated_data['quantity']
        variant    = serializer._variant

        item, created = CartItem.objects.get_or_create(
            cart=cart, variant=variant,
            defaults={'quantity': quantity},
        )
        if not created:
            # Validate combined quantity doesn't exceed stock
            new_qty = item.quantity + quantity
            if new_qty > variant.stock.quantity:
                return Response(
                    {'detail': f'Only {variant.stock.quantity} units available.'},
                    status=400
                )
            item.quantity = new_qty
            item.save(update_fields=['quantity'])

        return Response(CartItemSerializer(item).data, status=201 if created else 200)


class CartItemDetailView(APIView):
    permission_classes = [AllowAny]

    def get_authenticators(self):
        return [CustomerJWTAuthentication()]

    def get_item(self, pk, cart):
        try:
            return CartItem.objects.select_related('variant__stock').get(pk=pk, cart=cart)
        except CartItem.DoesNotExist:
            return None

    def patch(self, request, pk):
        cart, _ = get_cart(request)
        if not cart:
            return Response({'detail': 'Cart session required.'}, status=400)

        item = self.get_item(pk, cart)
        if not item:
            return Response({'detail': 'Item not found.'}, status=404)

        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        qty = serializer.validated_data['quantity']

        if qty > item.variant.stock.quantity:
            return Response(
                {'detail': f'Only {item.variant.stock.quantity} units available.'},
                status=400
            )
        item.quantity = qty
        item.save(update_fields=['quantity'])
        return Response(CartItemSerializer(item).data)

    def delete(self, request, pk):
        cart, _ = get_cart(request)
        if not cart:
            return Response({'detail': 'Cart session required.'}, status=400)

        item = self.get_item(pk, cart)
        if not item:
            return Response({'detail': 'Item not found.'}, status=404)
        item.delete()
        return Response(status=204)


# ─────────────────────────────────────────────
# Cart merge (guest → customer on login)
# ─────────────────────────────────────────────

class CartMergeView(APIView):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes     = [IsCustomer]

    def post(self, request):
        session_key = request.data.get('session_key')
        if not session_key:
            return Response({'detail': 'session_key required.'}, status=400)

        try:
            guest_cart = Cart.objects.prefetch_related('items').get(session_key=session_key)
        except Cart.DoesNotExist:
            return Response({'detail': 'Guest cart not found.'}, status=404)

        customer_cart, _ = Cart.objects.get_or_create(customer=request.user)

        for guest_item in guest_cart.items.all():
            existing = customer_cart.items.filter(variant=guest_item.variant).first()
            if existing:
                existing.quantity += guest_item.quantity
                existing.save(update_fields=['quantity'])
            else:
                guest_item.cart = customer_cart
                guest_item.save(update_fields=['cart'])

        guest_cart.delete()
        return Response(CartSerializer(customer_cart).data)


# ─────────────────────────────────────────────
# Coupon — apply
# ─────────────────────────────────────────────

class ApplyCouponView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ApplyCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code     = serializer.validated_data['code'].upper()
        subtotal = serializer.validated_data['subtotal']

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response({'detail': 'Invalid coupon code.'}, status=400)

        valid, error = coupon.is_valid()
        if not valid:
            return Response({'detail': error}, status=400)

        if subtotal < coupon.min_order_value:
            return Response(
                {'detail': f'Minimum order value is {coupon.min_order_value}.'},
                status=400
            )

        discount = coupon.calculate_discount(subtotal)
        return Response({
            'code':            coupon.code,
            'discount_type':   coupon.discount_type,
            'discount_value':  coupon.discount_value,
            'discount_amount': discount,
        })


# ─────────────────────────────────────────────
# Checkout
# ─────────────────────────────────────────────

class CheckoutView(APIView):
    permission_classes = [AllowAny]

    def get_authenticators(self):
        return [CustomerJWTAuthentication()]

    def post(self, request):
        cart, _ = get_cart(request)
        if not cart:
            return Response({'detail': 'Cart session required.'}, status=400)

        cart_items = list(
            cart.items.select_related(
                'variant__stock', 'variant__product'
            ).all()
        )
        if not cart_items:
            return Response({'detail': 'Cart is empty.'}, status=400)

        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # ── Coupon ──────────────────────────────────────────
        coupon          = None
        discount_amount = Decimal('0')
        coupon_code     = data.get('coupon_code', '').strip().upper()

        subtotal = sum(item.get_subtotal() for item in cart_items)

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                valid, error = coupon.is_valid()
                if not valid:
                    return Response({'detail': error}, status=400)
                if subtotal < coupon.min_order_value:
                    return Response(
                        {'detail': f'Minimum order value is {coupon.min_order_value}.'},
                        status=400
                    )
                discount_amount = coupon.calculate_discount(subtotal)
            except Coupon.DoesNotExist:
                return Response({'detail': 'Invalid coupon code.'}, status=400)

        shipping_cost = data.get('shipping_cost', Decimal('0'))
        total         = subtotal - discount_amount + shipping_cost

        # ── Atomic: stock check + decrement + order creation ─
        with transaction.atomic():
            # Lock stock rows for all variants in this cart
            variant_pks = [item.variant_id for item in cart_items]
            stocks = {
                s.variant_id: s
                for s in (
                    __import__(
                        'apps.inventory.models', fromlist=['Stock']
                    ).Stock.objects
                    .select_for_update()
                    .filter(variant_id__in=variant_pks)
                )
            }

            # Validate stock for all items before touching anything
            for item in cart_items:
                stock = stocks.get(item.variant_id)
                if not stock or stock.quantity < item.quantity:
                    return Response(
                        {'detail': f'Insufficient stock for {item.variant.sku}.'},
                        status=400
                    )

            # Decrement stock
            for item in cart_items:
                stock = stocks[item.variant_id]
                stock.quantity -= item.quantity
                stock.save(update_fields=['quantity'])

            # Create BillingInfo snapshot
            billing_data = data['billing_info']
            billing_info = BillingInfo.objects.create(**billing_data)

            # Create Order
            order_number = generate_order_number()
            order = Order(
                order_number    = order_number,
                customer        = request.user if (
                                      request.user and
                                      request.user.is_authenticated and
                                      not hasattr(request.user, 'role')
                                  ) else None,
                billing_info    = billing_info,
                coupon          = coupon,
                subtotal        = subtotal,
                discount_amount = discount_amount,
                shipping_cost   = shipping_cost,
                total           = total,
            )
            # Attach payment method as transient attr — finance signal reads this
            order._payment_method = data['payment_method']
            order.save()

            # Snapshot order items
            order_items = []
            for item in cart_items:
                variant = item.variant
                label   = build_variant_label(variant)
                order_items.append(OrderItem(
                    order        = order,
                    variant      = variant,
                    product_name = variant.product.name,
                    sku          = variant.sku,
                    variant_label = label,
                    unit_price   = variant.price,
                    quantity     = item.quantity,
                    total_price  = item.get_subtotal(),
                ))
            OrderItem.objects.bulk_create(order_items)

            # Increment coupon usage
            if coupon:
                Coupon.objects.filter(pk=coupon.pk).update(
                    used_count=coupon.used_count + 1
                )

            # Clear cart
            cart.items.all().delete()

        # ── Trigger payment record creation via signal (see signals.py) ──
        # Signal fires on Order post_save when created=True

        return Response(OrderSerializer(order).data, status=201)


# ─────────────────────────────────────────────
# Customer — Order history
# ─────────────────────────────────────────────

class CustomerOrderListView(APIView):
    authentication_classes = []
    permission_classes     = [AllowAny]

    def get(self, request):
        orders = (
            Order.objects
            .filter(customer=request.user)
            .select_related('billing_info')
            .order_by('-placed_at')
        )
        paginator  = StandardPagination()
        page       = paginator.paginate_queryset(orders, request)
        return paginator.get_paginated_response(OrderListSerializer(page, many=True).data)


class CustomerOrderDetailView(APIView):
    authentication_classes = [CustomerJWTAuthentication]
    permission_classes     = [IsCustomer]

    def get(self, request, order_number):
        try:
            order = (
                Order.objects
                .select_related('billing_info', 'coupon')
                .prefetch_related('items', 'status_logs__changed_by')
                .get(order_number=order_number, customer=request.user)
            )
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=404)
        return Response(OrderSerializer(order).data)


# ─────────────────────────────────────────────
# Guest — Order tracking (no auth)
# ─────────────────────────────────────────────

class GuestOrderTrackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GuestOrderTrackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_number = serializer.validated_data['order_number']
        phone        = serializer.validated_data['phone']

        try:
            order = (
                Order.objects
                .select_related('billing_info', 'coupon')
                .prefetch_related('items', 'status_logs')
                .get(
                    order_number=order_number,
                    billing_info__phone=phone,
                )
            )
        except Order.DoesNotExist:
            return Response({'detail': 'No order found with these details.'}, status=404)

        return Response(OrderSerializer(order).data)


# ─────────────────────────────────────────────
# Admin — Orders
# ─────────────────────────────────────────────

class AdminOrderListView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        qs = (
            Order.objects
            .select_related('billing_info', 'customer')
            .order_by('-placed_at')
        )

        # Filters
        order_status   = request.query_params.get('status')
        payment_status = request.query_params.get('payment_status')
        date_from      = request.query_params.get('date_from')
        date_to        = request.query_params.get('date_to')
        search         = request.query_params.get('search')

        if order_status:
            qs = qs.filter(status=order_status)
        if payment_status:
            qs = qs.filter(payment_status=payment_status)
        if date_from:
            qs = qs.filter(placed_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(placed_at__date__lte=date_to)
        if search:
            qs = qs.filter(order_number__icontains=search) | qs.filter(
                billing_info__phone__icontains=search
            )

        paginator = StandardPagination()
        page      = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(OrderListSerializer(page, many=True).data)


class AdminOrderDetailView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request, pk):
        try:
            order = (
                Order.objects
                .select_related('billing_info', 'customer', 'coupon')
                .prefetch_related('items', 'status_logs__changed_by')
                .get(pk=pk)
            )
        except Order.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        return Response(OrderSerializer(order).data)


class AdminOrderStatusView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status  = serializer.validated_data['status']
        note        = serializer.validated_data.get('note', '')
        old_status  = order.status

        if new_status == old_status:
            return Response({'detail': 'Status unchanged.'}, status=400)

        order.status = new_status
        order.save(update_fields=['status'])

        # Log the transition
        OrderStatusLog.objects.create(
            order       = order,
            from_status = old_status,
            to_status   = new_status,
            changed_by  = request.user,
            note        = note,
        )

        # Auto-verify COD payment when order is marked delivered
        if new_status == Order.Status.DELIVERED:
            try:
                payment = order.payment
                if payment.method == 'cod' and payment.status == 'pending':
                    from django.utils import timezone
                    payment.status      = 'verified'
                    payment.verified_at = timezone.now()
                    payment.verified_by = request.user
                    payment.save(update_fields=['status', 'verified_at', 'verified_by'])
                    order.payment_status = Order.PaymentStatus.PAID
                    order.save(update_fields=['payment_status'])
            except Exception:
                pass  # finance app not yet wired — safe to skip in isolation

        return Response(OrderSerializer(order).data)


# ─────────────────────────────────────────────
# Admin — Coupons
# ─────────────────────────────────────────────

class AdminCouponListCreateView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        coupons = Coupon.objects.order_by('-valid_until')
        return Response(CouponSerializer(coupons, many=True).data)

    def post(self, request):
        serializer = CouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        coupon = serializer.save()
        return Response(CouponSerializer(coupon).data, status=201)


class AdminCouponDetailView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def patch(self, request, pk):
        try:
            coupon = Coupon.objects.get(pk=pk)
        except Coupon.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        serializer = CouponSerializer(coupon, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CouponSerializer(coupon).data)