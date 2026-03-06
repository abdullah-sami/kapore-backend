from rest_framework import serializers
from .models import Cart, CartItem, BillingInfo, Order, OrderItem, OrderStatusLog, Coupon


# ─────────────────────────────────────────────
# Cart
# ─────────────────────────────────────────────

class CartItemSerializer(serializers.ModelSerializer):
    variant_sku   = serializers.CharField(source='variant.sku', read_only=True)
    product_name  = serializers.CharField(source='variant.product.name', read_only=True)
    variant_label = serializers.SerializerMethodField()
    unit_price    = serializers.DecimalField(
                        source='variant.price', max_digits=10,
                        decimal_places=2, read_only=True
                    )
    subtotal      = serializers.SerializerMethodField()
    image_url     = serializers.SerializerMethodField()

    class Meta:
        model  = CartItem
        fields = [
            'id', 'variant', 'variant_sku', 'product_name',
            'variant_label', 'unit_price', 'quantity', 'subtotal', 'image_url',
        ]
        read_only_fields = ['id']

    def get_variant_label(self, obj):
        from .utils import build_variant_label
        return build_variant_label(obj.variant)

    def get_subtotal(self, obj):
        return obj.get_subtotal()

    def get_image_url(self, obj):
        primary = obj.variant.product.images.filter(is_primary=True).first()
        if not primary:
            primary = obj.variant.product.images.first()
        return primary.image_url if primary else None


class CartItemCreateSerializer(serializers.Serializer):
    variant  = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=100)

    def validate_variant(self, value):
        from apps.inventory.models import ProductVariant
        try:
            variant = ProductVariant.objects.select_related('stock').get(
                pk=value, is_active=True
            )
        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError('Variant not found or inactive.')
        if not variant.stock.is_in_stock:
            raise serializers.ValidationError('This variant is out of stock.')
        self._variant = variant
        return value

    def validate(self, data):
        variant  = self._variant
        quantity = data['quantity']
        if quantity > variant.stock.quantity:
            raise serializers.ValidationError(
                f'Only {variant.stock.quantity} units available.'
            )
        return data


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=100)


class CartSerializer(serializers.ModelSerializer):
    items       = CartItemSerializer(many=True, read_only=True)
    total       = serializers.SerializerMethodField()
    item_count  = serializers.SerializerMethodField()

    class Meta:
        model  = Cart
        fields = ['id', 'session_key', 'items', 'total', 'item_count']

    def get_total(self, obj):
        return sum(item.get_subtotal() for item in obj.items.all())

    def get_item_count(self, obj):
        return obj.items.count()


# ─────────────────────────────────────────────
# Billing info
# ─────────────────────────────────────────────

class BillingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BillingInfo
        fields = [
            'full_name', 'phone', 'email',
            'address_line_1', 'address_line_2',
            'city', 'district', 'postal_code',
            'delivery_instructions',
        ]


# ─────────────────────────────────────────────
# Coupon
# ─────────────────────────────────────────────

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Coupon
        fields = [
            'id', 'code', 'discount_type', 'discount_value',
            'min_order_value', 'max_uses', 'used_count',
            'valid_from', 'valid_until', 'is_active',
        ]
        read_only_fields = ['id', 'used_count']


class ApplyCouponSerializer(serializers.Serializer):
    code     = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)


# ─────────────────────────────────────────────
# Checkout
# ─────────────────────────────────────────────

class CheckoutSerializer(serializers.Serializer):
    billing_info   = BillingInfoSerializer()
    payment_method = serializers.ChoiceField(choices=['cod', 'bkash', 'nagad'])
    coupon_code    = serializers.CharField(required=False, allow_blank=True)
    shipping_cost  = serializers.DecimalField(
                         max_digits=10, decimal_places=2,
                         required=False, default=0
                     )


# ─────────────────────────────────────────────
# Order
# ─────────────────────────────────────────────

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OrderItem
        fields = [
            'id', 'product_name', 'sku', 'variant_label',
            'unit_price', 'quantity', 'total_price',
        ]


class OrderStatusLogSerializer(serializers.ModelSerializer):
    changed_by = serializers.CharField(source='changed_by.full_name', read_only=True)

    class Meta:
        model  = OrderStatusLog
        fields = ['from_status', 'to_status', 'changed_by', 'note', 'timestamp']


class OrderSerializer(serializers.ModelSerializer):
    items        = OrderItemSerializer(many=True, read_only=True)
    billing_info = BillingInfoSerializer(read_only=True)
    status_logs  = OrderStatusLogSerializer(many=True, read_only=True)

    class Meta:
        model  = Order
        fields = [
            'id', 'order_number', 'status', 'payment_status',
            'subtotal', 'discount_amount', 'shipping_cost', 'total',
            'billing_info', 'items', 'status_logs', 'placed_at',
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight — used in list views to avoid loading items."""
    class Meta:
        model  = Order
        fields = [
            'id', 'order_number', 'status', 'payment_status',
            'total', 'placed_at',
        ]


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
    note   = serializers.CharField(required=False, allow_blank=True)


class GuestOrderTrackSerializer(serializers.Serializer):
    order_number = serializers.CharField()
    phone        = serializers.CharField()