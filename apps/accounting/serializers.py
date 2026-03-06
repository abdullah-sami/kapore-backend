from rest_framework import serializers
from .models import Account, JournalEntry, JournalLine


class AccountSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model  = Account
        fields = [
            'id', 'code', 'name', 'account_type',
            'parent', 'description', 'is_active', 'children',
        ]
        read_only_fields = ['id']

    def get_children(self, obj):
        kids = obj.children.filter(is_active=True)
        return AccountSerializer(kids, many=True).data


class AccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Account
        fields = ['code', 'name', 'account_type', 'parent', 'description', 'is_active']

    def validate_code(self, value):
        qs = Account.objects.filter(code=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('An account with this code already exists.')
        return value


# ─────────────────────────────────────────────
# Journal lines
# ─────────────────────────────────────────────

class JournalLineSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model  = JournalLine
        fields = ['id', 'account', 'account_code', 'account_name', 'debit', 'credit', 'note']
        read_only_fields = ['id', 'account_code', 'account_name']


class JournalLineCreateSerializer(serializers.Serializer):
    account = serializers.UUIDField()
    debit   = serializers.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit  = serializers.DecimalField(max_digits=14, decimal_places=2, default=0)
    note    = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, data):
        if data['debit'] == 0 and data['credit'] == 0:
            raise serializers.ValidationError('A line must have either a debit or credit value.')
        if data['debit'] > 0 and data['credit'] > 0:
            raise serializers.ValidationError('A line cannot have both debit and credit.')
        return data


# ─────────────────────────────────────────────
# Journal entries
# ─────────────────────────────────────────────

class JournalEntrySerializer(serializers.ModelSerializer):
    lines      = JournalLineSerializer(many=True, read_only=True)
    created_by = serializers.CharField(source='created_by.full_name', read_only=True)
    is_balanced = serializers.SerializerMethodField()

    class Meta:
        model  = JournalEntry
        fields = [
            'id', 'reference_number', 'description', 'entry_date',
            'created_by', 'is_posted', 'is_balanced', 'lines', 'created_at',
        ]

    def get_is_balanced(self, obj):
        return obj.is_balanced()


class JournalEntryListSerializer(serializers.ModelSerializer):
    """Lightweight — no lines, for list views."""
    created_by = serializers.CharField(source='created_by.full_name', read_only=True)

    class Meta:
        model  = JournalEntry
        fields = [
            'id', 'reference_number', 'description',
            'entry_date', 'created_by', 'is_posted', 'created_at',
        ]


class JournalEntryCreateSerializer(serializers.Serializer):
    description = serializers.CharField()
    entry_date  = serializers.DateField()
    lines       = JournalLineCreateSerializer(many=True, min_length=2)

    def validate_lines(self, lines):
        from decimal import Decimal
        total_debit  = sum(Decimal(str(l['debit']))  for l in lines)
        total_credit = sum(Decimal(str(l['credit'])) for l in lines)
        if total_debit != total_credit:
            raise serializers.ValidationError(
                f'Entry is not balanced. Debits: {total_debit}, Credits: {total_credit}'
            )
        return lines

    def validate(self, data):
        # Verify all account UUIDs exist
        from .models import Account
        account_ids = [str(l['account']) for l in data['lines']]
        found = Account.objects.filter(pk__in=account_ids, is_active=True).count()
        if found != len(account_ids):
            raise serializers.ValidationError({'lines': 'One or more account IDs are invalid.'})
        return data