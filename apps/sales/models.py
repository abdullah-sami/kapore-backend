import uuid
from django.db import models
from django.utils import timezone


class Cart(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer    = models.OneToOneField(
                      'customers.Customer', on_delete=models.CASCADE,
                      null=True, blank=True, related_name='cart'
                  )
    session_key = models.UUIDField(unique=True, db_index=True, default=uuid.uuid4)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'

    def __str__(self):
        owner = self.customer or f'guest:{self.session_key}'
        return f'Cart({owner})'

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.select_related('variant'))


class CartItem(models.Model):
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart     = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant  = models.ForeignKey(
                   'inventory.ProductVariant', on_delete=models.CASCADE,
                   related_name='cart_items'
               )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table        = 'cart_items'
        unique_together = [('cart', 'variant')]

    def get_subtotal(self):
        return self.variant.price * self.quantity

    def __str__(self):
        return f'{self.variant.sku} x{self.quantity}'


class BillingInfo(models.Model):
    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name            = models.CharField(max_length=255)
    phone                = models.CharField(max_length=20)
    email                = models.EmailField(blank=True, default='')
    address_line_1       = models.CharField(max_length=255)
    address_line_2       = models.CharField(max_length=255, blank=True, default='')
    city                 = models.CharField(max_length=100)
    district             = models.CharField(max_length=100, blank=True, default='')
    postal_code          = models.CharField(max_length=20, blank=True, default='')
    delivery_instructions = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'billing_info'

    def __str__(self):
        return f'{self.full_name} — {self.phone}'


class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        FLAT    = 'flat',    'Flat'
        PERCENT = 'percent', 'Percent'

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code            = models.CharField(max_length=50, unique=True, db_index=True)
    discount_type   = models.CharField(max_length=10, choices=DiscountType.choices)
    discount_value  = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses        = models.PositiveIntegerField(null=True, blank=True)  # null = unlimited
    used_count      = models.PositiveIntegerField(default=0)
    valid_from      = models.DateTimeField()
    valid_until     = models.DateTimeField()
    is_active       = models.BooleanField(default=True)

    class Meta:
        db_table = 'coupons'

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False, 'Coupon is inactive.'
        if now < self.valid_from:
            return False, 'Coupon is not yet valid.'
        if now > self.valid_until:
            return False, 'Coupon has expired.'
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False, 'Coupon usage limit reached.'
        return True, None

    def calculate_discount(self, subtotal):
        if self.discount_type == self.DiscountType.FLAT:
            return min(self.discount_value, subtotal)
        else:  # percent
            return (subtotal * self.discount_value / 100).quantize(subtotal)


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING    = 'pending',    'Pending'
        CONFIRMED  = 'confirmed',  'Confirmed'
        PROCESSING = 'processing', 'Processing'
        SHIPPED    = 'shipped',    'Shipped'
        DELIVERED  = 'delivered',  'Delivered'
        CANCELLED  = 'cancelled',  'Cancelled'
        REFUNDED   = 'refunded',   'Refunded'

    class PaymentStatus(models.TextChoices):
        UNPAID             = 'unpaid',             'Unpaid'
        PAID               = 'paid',               'Paid'
        PARTIALLY_REFUNDED = 'partially_refunded', 'Partially Refunded'
        REFUNDED           = 'refunded',           'Refunded'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number   = models.CharField(max_length=20, unique=True, db_index=True)
    customer       = models.ForeignKey(
                         'customers.Customer', on_delete=models.SET_NULL,
                         null=True, blank=True, related_name='orders'
                     )
    billing_info   = models.OneToOneField(
                         BillingInfo, on_delete=models.PROTECT, related_name='order'
                     )
    coupon         = models.ForeignKey(
                         Coupon, on_delete=models.SET_NULL,
                         null=True, blank=True, related_name='orders'
                     )
    status         = models.CharField(
                         max_length=20, choices=Status.choices,
                         default=Status.PENDING, db_index=True
                     )
    payment_status = models.CharField(
                         max_length=25, choices=PaymentStatus.choices,
                         default=PaymentStatus.UNPAID, db_index=True
                     )
    subtotal        = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total           = models.DecimalField(max_digits=12, decimal_places=2)
    placed_at       = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-placed_at']
        indexes  = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['status', 'payment_status']),
        ]

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order         = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant       = models.ForeignKey(
                        'inventory.ProductVariant', on_delete=models.SET_NULL,
                        null=True, related_name='order_items'
                    )
    # Snapshot fields — frozen at time of order, immune to catalog changes
    product_name  = models.CharField(max_length=255)
    sku           = models.CharField(max_length=100)
    variant_label = models.CharField(max_length=255, blank=True, default='')
    unit_price    = models.DecimalField(max_digits=10, decimal_places=2)
    quantity      = models.PositiveIntegerField()
    total_price   = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f'{self.order.order_number} — {self.sku} x{self.quantity}'


class OrderStatusLog(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order       = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_logs')
    from_status = models.CharField(max_length=20, blank=True, default='')
    to_status   = models.CharField(max_length=20)
    changed_by  = models.ForeignKey(
                      'admin_panel.AdminUser', on_delete=models.SET_NULL,
                      null=True, related_name='status_changes'
                  )
    note        = models.TextField(blank=True, default='')
    timestamp   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'order_status_logs'
        ordering = ['-timestamp']