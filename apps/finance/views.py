from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


from django.db import models
from common.permissions import IsAdminUser
from common.pagination import StandardPagination
from apps.admin_panel.authentication import AdminJWTAuthentication
from apps.customers.authentication import CustomerJWTAuthentication
from apps.sales.models import Order

from .models import Payment, Refund, ExpenseCategory, Expense
from .serializers import (
    PaymentSerializer,
    PaymentAdminSerializer,
    PaymentSubmitSerializer,
    PaymentVerifySerializer,
    PaymentRejectSerializer,
    RefundSerializer,
    RefundCreateSerializer,
    RefundUpdateSerializer,
    ExpenseCategorySerializer,
    ExpenseSerializer,
    ExpenseCreateSerializer,
)


# ─────────────────────────────────────────────
# Storefront — Payment status & submission
# ─────────────────────────────────────────────

class PaymentStatusView(APIView):
    """
    GET /payments/{order_number}/
    Public — guests look up by order_number + phone (tracked via order).
    Registered customers can also use this without extra auth.
    """
    permission_classes = [AllowAny]

    def get(self, request, order_number):
        try:
            payment = (
                Payment.objects
                .select_related('order__billing_info')
                .get(order__order_number=order_number)
            )
        except Payment.DoesNotExist:
            return Response({'detail': 'Payment not found.'}, status=404)
        return Response(PaymentSerializer(payment).data)


class PaymentSubmitView(APIView):
    """
    POST /payments/{order_number}/submit/
    Customer submits bKash/Nagad TrxID + screenshot after sending money.
    No-op if method is COD — returns a clear message.
    Can resubmit if previously rejected (admin note will be visible).
    """
    permission_classes = [AllowAny]

    def post(self, request, order_number):
        try:
            payment = Payment.objects.select_related('order').get(
                order__order_number=order_number
            )
        except Payment.DoesNotExist:
            return Response({'detail': 'Payment not found.'}, status=404)

        # COD — nothing to submit
        if payment.method == Payment.Method.COD:
            return Response(
                {'detail': 'COD payments are confirmed on delivery. No action needed.'},
                status=200,
            )

        # Only allow submission when pending or rejected
        if payment.status == Payment.Status.VERIFIED:
            return Response({'detail': 'Payment is already verified.'}, status=400)

        if payment.status == Payment.Status.SUBMITTED:
            return Response(
                {'detail': 'Payment already submitted. Awaiting admin verification.'},
                status=400,
            )

        serializer = PaymentSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        payment.transaction_id         = data['transaction_id']
        payment.sender_number          = data['sender_number']
        payment.payment_screenshot_url = data['payment_screenshot_url']
        payment.status                 = Payment.Status.SUBMITTED
        payment.submitted_at           = timezone.now()
        payment.admin_note             = ''   # clear previous rejection note
        payment.save(update_fields=[
            'transaction_id', 'sender_number', 'payment_screenshot_url',
            'status', 'submitted_at', 'admin_note',
        ])

        return Response(PaymentSerializer(payment).data)


# ─────────────────────────────────────────────
# Admin — Payment list & detail
# ─────────────────────────────────────────────

class AdminPaymentListView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        qs = (
            Payment.objects
            .select_related('order__billing_info', 'verified_by')
            .order_by('-created_at')
        )

        status_filter = request.query_params.get('status')
        method_filter = request.query_params.get('method')
        date_filter   = request.query_params.get('date')

        if status_filter:
            qs = qs.filter(status=status_filter)
        if method_filter:
            qs = qs.filter(method=method_filter)
        if date_filter:
            qs = qs.filter(created_at__date=date_filter)

        paginator = StandardPagination()
        page      = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(PaymentAdminSerializer(page, many=True).data)


class AdminPaymentDetailView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get_object(self, pk):
        try:
            return Payment.objects.select_related(
                'order__billing_info', 'verified_by'
            ).get(pk=pk)
        except Payment.DoesNotExist:
            return None

    def get(self, request, pk):
        payment = self.get_object(pk)
        if not payment:
            return Response({'detail': 'Not found.'}, status=404)
        return Response(PaymentAdminSerializer(payment).data)


# ─────────────────────────────────────────────
# Admin — Verify / Reject payment
# ─────────────────────────────────────────────

class AdminPaymentVerifyView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def patch(self, request, pk):
        try:
            payment = Payment.objects.select_related('order').get(pk=pk)
        except Payment.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        if payment.status == Payment.Status.VERIFIED:
            return Response({'detail': 'Already verified.'}, status=400)

        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment.status      = Payment.Status.VERIFIED
        payment.verified_at = timezone.now()
        payment.verified_by = request.user
        payment.admin_note  = serializer.validated_data.get('admin_note', '')
        payment.save(update_fields=['status', 'verified_at', 'verified_by', 'admin_note'])

        # Update order payment_status
        order = payment.order
        order.payment_status = 'paid'
        order.save(update_fields=['payment_status'])

        return Response(PaymentAdminSerializer(payment).data)


class AdminPaymentRejectView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def patch(self, request, pk):
        try:
            payment = Payment.objects.select_related('order').get(pk=pk)
        except Payment.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        if payment.status == Payment.Status.VERIFIED:
            return Response({'detail': 'Cannot reject a verified payment.'}, status=400)

        serializer = PaymentRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment.status     = Payment.Status.REJECTED
        payment.admin_note = serializer.validated_data['admin_note']
        payment.save(update_fields=['status', 'admin_note'])

        # Order payment_status stays unpaid — customer can resubmit
        return Response(PaymentAdminSerializer(payment).data)


# ─────────────────────────────────────────────
# Admin — Refunds
# ─────────────────────────────────────────────

class AdminRefundListCreateView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        refunds = (
            Refund.objects
            .select_related('order', 'payment', 'processed_by')
            .order_by('-requested_at')
        )
        paginator = StandardPagination()
        page      = paginator.paginate_queryset(refunds, request)
        return paginator.get_paginated_response(RefundSerializer(page, many=True).data)

    def post(self, request):
        serializer = RefundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refund = serializer.save()
        return Response(RefundSerializer(refund).data, status=201)


class AdminRefundDetailView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get_object(self, pk):
        try:
            return Refund.objects.select_related(
                'order', 'payment', 'processed_by'
            ).get(pk=pk)
        except Refund.DoesNotExist:
            return None

    def patch(self, request, pk):
        refund = self.get_object(pk)
        if not refund:
            return Response({'detail': 'Not found.'}, status=404)

        serializer = RefundUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        new_status = data['status']
        refund.status = new_status

        if data.get('proof_url'):
            refund.proof_url = data['proof_url']

        if new_status == Refund.Status.PROCESSED:
            refund.processed_at = timezone.now()
            refund.processed_by = request.user

            # Restore stock when refund is processed
            try:
                from apps.inventory.models import Stock
                from apps.sales.models import OrderItem
                
                items = OrderItem.objects.filter(order=refund.order).select_related('variant')
                for item in items:
                    Stock.objects.filter(variant=item.variant).update(
                        quantity=models.F('quantity') + item.quantity
                    )
            except Exception:
                pass

            # Update order statuses
            refund.order.status         = 'refunded'
            refund.order.payment_status = 'refunded'
            refund.order.save(update_fields=['status', 'payment_status'])

        refund.save()
        return Response(RefundSerializer(refund).data)


# ─────────────────────────────────────────────
# Admin — Expenses
# ─────────────────────────────────────────────

class AdminExpenseCategoryView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        categories = ExpenseCategory.objects.all()
        return Response(ExpenseCategorySerializer(categories, many=True).data)

    def post(self, request):
        serializer = ExpenseCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return Response(ExpenseCategorySerializer(category).data, status=201)


class AdminExpenseListCreateView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        qs = (
            Expense.objects
            .select_related('category', 'recorded_by')
            .order_by('-incurred_on')
        )

        category = request.query_params.get('category')
        date_from = request.query_params.get('date_from')
        date_to   = request.query_params.get('date_to')

        if category:
            qs = qs.filter(category__id=category)
        if date_from:
            qs = qs.filter(incurred_on__gte=date_from)
        if date_to:
            qs = qs.filter(incurred_on__lte=date_to)

        paginator = StandardPagination()
        page      = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(ExpenseSerializer(page, many=True).data)

    def post(self, request):
        serializer = ExpenseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = serializer.save(recorded_by=request.user)
        return Response(ExpenseSerializer(expense).data, status=201)


class AdminExpenseDetailView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get_object(self, pk):
        try:
            return Expense.objects.select_related('category', 'recorded_by').get(pk=pk)
        except Expense.DoesNotExist:
            return None

    def patch(self, request, pk):
        expense = self.get_object(pk)
        if not expense:
            return Response({'detail': 'Not found.'}, status=404)
        serializer = ExpenseCreateSerializer(expense, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ExpenseSerializer(expense).data)