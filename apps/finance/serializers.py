from rest_framework import serializers
from .models import Payment, Refund, ExpenseCategory, Expense


# ─────────────────────────────────────────────
# Payment
# ─────────────────────────────────────────────

class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model  = Payment
        fields = [
            'id', 'order_number', 'method', 'amount', 'status',
            'transaction_id', 'sender_number', 'payment_screenshot_url',
            'submitted_at', 'verified_at', 'admin_note', 'created_at',
        ]
        read_only_fields = [
            'id', 'order_number', 'amount', 'status',
            'submitted_at', 'verified_at', 'admin_note', 'created_at',
        ]


class PaymentSubmitSerializer(serializers.Serializer):
    """
    Customer submits payment proof for bKash / Nagad.
    All three fields required for mobile banking; irrelevant for COD.
    """
    transaction_id         = serializers.CharField(max_length=100)
    sender_number          = serializers.CharField(max_length=20)
    payment_screenshot_url = serializers.URLField()

    def validate(self, data):
        # All three fields must be non-empty
        for field in ['transaction_id', 'sender_number', 'payment_screenshot_url']:
            if not data.get(field, '').strip():
                raise serializers.ValidationError(
                    {field: 'This field is required for mobile banking payments.'}
                )
        return data


class PaymentVerifySerializer(serializers.Serializer):
    admin_note = serializers.CharField(required=False, allow_blank=True, default='')


class PaymentRejectSerializer(serializers.Serializer):
    admin_note = serializers.CharField()   # rejection note is mandatory


# Admin-facing payment detail includes verified_by name
class PaymentAdminSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    verified_by  = serializers.CharField(source='verified_by.full_name', read_only=True)
    billing_phone = serializers.CharField(
        source='order.billing_info.phone', read_only=True
    )
    billing_name  = serializers.CharField(
        source='order.billing_info.full_name', read_only=True
    )

    class Meta:
        model  = Payment
        fields = [
            'id', 'order_number', 'billing_name', 'billing_phone',
            'method', 'amount', 'status',
            'transaction_id', 'sender_number', 'payment_screenshot_url',
            'submitted_at', 'verified_at', 'verified_by', 'admin_note',
            'created_at',
        ]


# ─────────────────────────────────────────────
# Refund
# ─────────────────────────────────────────────

class RefundSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    processed_by = serializers.CharField(source='processed_by.full_name', read_only=True)

    class Meta:
        model  = Refund
        fields = [
            'id', 'order_number', 'payment', 'amount', 'method',
            'recipient_number', 'reason', 'status', 'proof_url',
            'requested_at', 'processed_at', 'processed_by',
        ]
        read_only_fields = ['id', 'status', 'requested_at', 'processed_at', 'processed_by']


class RefundCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Refund
        fields = ['payment', 'order', 'amount', 'method', 'recipient_number', 'reason']

    def validate(self, data):
        payment = data.get('payment')
        order   = data.get('order')
        amount  = data.get('amount')

        if payment.order != order:
            raise serializers.ValidationError('Payment does not belong to this order.')
        if amount > payment.amount:
            raise serializers.ValidationError('Refund amount exceeds payment amount.')
        return data


class RefundUpdateSerializer(serializers.Serializer):
    status    = serializers.ChoiceField(choices=Refund.Status.choices)
    proof_url = serializers.URLField(required=False, allow_blank=True)


# ─────────────────────────────────────────────
# Expense
# ─────────────────────────────────────────────

class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = ExpenseCategory
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    recorded_by   = serializers.CharField(source='recorded_by.full_name', read_only=True)

    class Meta:
        model  = Expense
        fields = [
            'id', 'category', 'category_name', 'title', 'description',
            'amount', 'receipt_url', 'incurred_on', 'recorded_by', 'created_at',
        ]
        read_only_fields = ['id', 'recorded_by', 'created_at']


class ExpenseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Expense
        fields = ['category', 'title', 'description', 'amount', 'receipt_url', 'incurred_on']