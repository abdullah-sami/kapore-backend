import uuid
from django.db import models


class Account(models.Model):
    class Type(models.TextChoices):
        ASSET     = 'asset',     'Asset'
        LIABILITY = 'liability', 'Liability'
        EQUITY    = 'equity',    'Equity'
        REVENUE   = 'revenue',   'Revenue'
        EXPENSE   = 'expense',   'Expense'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name         = models.CharField(max_length=255)
    code         = models.CharField(max_length=20, unique=True, db_index=True)
    account_type = models.CharField(max_length=10, choices=Type.choices, db_index=True)
    parent       = models.ForeignKey(
                       'self', on_delete=models.SET_NULL,
                       null=True, blank=True, related_name='children'
                   )
    description  = models.TextField(blank=True, default='')
    is_active    = models.BooleanField(default=True)

    class Meta:
        db_table = 'accounts'
        ordering = ['code']

    def __str__(self):
        return f'[{self.code}] {self.name}'


class JournalEntry(models.Model):
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_number = models.CharField(max_length=50, unique=True, db_index=True)
    description      = models.TextField()
    entry_date       = models.DateField(db_index=True)
    created_by       = models.ForeignKey(
                           'admin_panel.AdminUser', on_delete=models.SET_NULL,
                           null=True, related_name='journal_entries'
                       )
    is_posted        = models.BooleanField(default=False, db_index=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'journal_entries'
        ordering = ['-entry_date', '-created_at']
        indexes  = [
            models.Index(fields=['entry_date', 'is_posted']),
        ]

    def __str__(self):
        return f'{self.reference_number} — {self.description[:60]}'

    def total_debits(self):
        from django.db.models import Sum
        return self.lines.aggregate(t=Sum('debit'))['t'] or 0

    def total_credits(self):
        from django.db.models import Sum
        return self.lines.aggregate(t=Sum('credit'))['t'] or 0

    def is_balanced(self):
        return self.total_debits() == self.total_credits()


class JournalLine(models.Model):
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entry   = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(
                  Account, on_delete=models.PROTECT, related_name='journal_lines'
              )
    debit   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    note    = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'journal_lines'
        indexes  = [
            models.Index(fields=['account', 'entry']),
        ]

    def __str__(self):
        return f'{self.entry.reference_number} | {self.account.code} | D:{self.debit} C:{self.credit}'