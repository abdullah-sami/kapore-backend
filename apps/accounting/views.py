from django.utils.dateparse import parse_date
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from common.permissions import IsAdminUser
from common.pagination import StandardPagination
from apps.admin_panel.authentication import AdminJWTAuthentication

from .models import Account, JournalEntry, JournalLine
from .serializers import (
    AccountSerializer,
    AccountCreateSerializer,
    JournalEntrySerializer,
    JournalEntryListSerializer,
    JournalEntryCreateSerializer,
)
from .reports import get_balance_sheet, get_profit_and_loss, get_trial_balance


# ─────────────────────────────────────────────
# Accounts (Chart of Accounts)
# ─────────────────────────────────────────────

class AccountListCreateView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        # Only return root accounts — children nested via serializer
        accounts = (
            Account.objects
            .filter(parent__isnull=True, is_active=True)
            .prefetch_related('children')
            .order_by('code')
        )
        return Response(AccountSerializer(accounts, many=True).data)

    def post(self, request):
        serializer = AccountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        return Response(AccountSerializer(account).data, status=201)


class AccountDetailView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get_object(self, pk):
        try:
            return Account.objects.prefetch_related('children').get(pk=pk)
        except Account.DoesNotExist:
            return None

    def patch(self, request, pk):
        account = self.get_object(pk)
        if not account:
            return Response({'detail': 'Not found.'}, status=404)
        serializer = AccountCreateSerializer(account, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AccountSerializer(account).data)


# ─────────────────────────────────────────────
# Journal Entries
# ─────────────────────────────────────────────

class JournalEntryListCreateView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        qs = JournalEntry.objects.select_related('created_by').order_by('-entry_date')

        is_posted  = request.query_params.get('is_posted')
        date_from  = request.query_params.get('date_from')
        date_to    = request.query_params.get('date_to')

        if is_posted is not None:
            qs = qs.filter(is_posted=is_posted.lower() == 'true')
        if date_from:
            qs = qs.filter(entry_date__gte=date_from)
        if date_to:
            qs = qs.filter(entry_date__lte=date_to)

        paginator = StandardPagination()
        page      = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(JournalEntryListSerializer(page, many=True).data)

    def post(self, request):
        serializer = JournalEntryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from django.db import transaction as db_transaction
        with db_transaction.atomic():
            from .utils import generate_reference_number
            entry = JournalEntry.objects.create(
                reference_number = generate_reference_number(),
                description      = data['description'],
                entry_date       = data['entry_date'],
                created_by       = request.user,
                is_posted        = False,   # drafts require explicit post action
            )
            lines = []
            for line_data in data['lines']:
                lines.append(JournalLine(
                    entry   = entry,
                    account = Account.objects.get(pk=line_data['account']),
                    debit   = line_data['debit'],
                    credit  = line_data['credit'],
                    note    = line_data.get('note', ''),
                ))
            JournalLine.objects.bulk_create(lines)

        return Response(
            JournalEntrySerializer(
                JournalEntry.objects.prefetch_related('lines__account').get(pk=entry.pk)
            ).data,
            status=201,
        )


class JournalEntryDetailView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get_object(self, pk):
        try:
            return (
                JournalEntry.objects
                .select_related('created_by')
                .prefetch_related('lines__account')
                .get(pk=pk)
            )
        except JournalEntry.DoesNotExist:
            return None

    def get(self, request, pk):
        entry = self.get_object(pk)
        if not entry:
            return Response({'detail': 'Not found.'}, status=404)
        return Response(JournalEntrySerializer(entry).data)


class JournalEntryPostView(APIView):
    """PATCH /journal-entries/{id}/post/ — marks a draft entry as posted (irreversible)."""
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def patch(self, request, pk):
        try:
            entry = JournalEntry.objects.prefetch_related('lines').get(pk=pk)
        except JournalEntry.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        if entry.is_posted:
            return Response({'detail': 'Already posted.'}, status=400)

        if not entry.is_balanced():
            return Response(
                {'detail': 'Cannot post an unbalanced entry. Check debits and credits.'},
                status=400,
            )

        entry.is_posted = True
        entry.save(update_fields=['is_posted'])
        return Response(JournalEntrySerializer(entry).data)


# ─────────────────────────────────────────────
# Reports
# ─────────────────────────────────────────────

class BalanceSheetView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        date_str = request.query_params.get('date', str(timezone.now().date()))
        date     = parse_date(date_str)
        if not date:
            return Response({'detail': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
        return Response(get_balance_sheet(date))


class ProfitLossView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        from_str = request.query_params.get('from')
        to_str   = request.query_params.get('to', str(timezone.now().date()))

        if not from_str:
            return Response({'detail': '?from= is required (YYYY-MM-DD).'}, status=400)

        date_from = parse_date(from_str)
        date_to   = parse_date(to_str)

        if not date_from or not date_to:
            return Response({'detail': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

        if date_from > date_to:
            return Response({'detail': '"from" must be before "to".'}, status=400)

        return Response(get_profit_and_loss(date_from, date_to))


class TrialBalanceView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        date_str = request.query_params.get('date', str(timezone.now().date()))
        date     = parse_date(date_str)
        if not date:
            return Response({'detail': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
        return Response(get_trial_balance(date))