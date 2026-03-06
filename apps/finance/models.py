import uuid
from django.db import models


class Payment(models.Model):
    class Method(models.TextChoices):
        COD   = 'cod',   'Cash on Delivery'
        BKASH = 'bkash', 'bKash'
        NAGAD = 'nagad', 'Nagad'

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        SUBMITTED = 'submitted', 'Submitted'   # customer sent TrxID
        VERIFIED  = 'verified',  'Verified'    # admin confirmed
        REJECTED  = 'rejected',  'Rejected'    # admin rejected, customer can resubmit

    id                     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order                  = models.OneToOneField(
                                 'sales.Order', on_delete=models.CASCADE,
                                 related_name='payment'
                             )
    method                 = models.CharField(max_length=10, choices=Method.choices)
    amount                 = models.DecimalField(max_digits=12, decimal_places=2)
    status                 = models.CharField(
                                 max_length=10, choices=Status.choices,
                                 default=Status.PENDING, db_index=True
                             )
    # bKash / Nagad fields — blank for COD
    transaction_id         = models.CharField(max_length=100, blank=True, default='')
    sender_number          = models.CharField(max_length=20, blank=True, default='')
    payment_screenshot_url = models.URLField(blank=True, default='')  # Cloudinary

    submitted_at = models.DateTimeField(null=True, blank=True)
    verified_at  = models.DateTimeField(null=True, blank=True)
    verified_by  = models.ForeignKey(
                       'admin_panel.AdminUser', on_delete=models.SET_NULL,
                       null=True, blank=True, related_name='verified_payments'
                   )
    admin_note   = models.TextField(blank=True, default='')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        indexes  = [
            models.Index(fields=['status', 'method']),
        ]

    def __str__(self):
        return f'{self.order.order_number} — {self.method} — {self.status}'

    @property
    def is_mobile_banking(self):
        return self.method in (self.Method.BKASH, self.Method.NAGAD)


class Refund(models.Model):
    class Method(models.TextChoices):
        BKASH = 'bkash', 'bKash'
        NAGAD = 'nagad', 'Nagad'
        CASH  = 'cash',  'Cash'

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        APPROVED  = 'approved',  'Approved'
        PROCESSED = 'processed', 'Processed'
        REJECTED  = 'rejected',  'Rejected'

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment          = models.ForeignKey(
                           Payment, on_delete=models.CASCADE, related_name='refunds'
                       )
    order            = models.ForeignKey(
                           'sales.Order', on_delete=models.CASCADE, related_name='refunds'
                       )
    amount           = models.DecimalField(max_digits=12, decimal_places=2)
    method           = models.CharField(max_length=10, choices=Method.choices)
    recipient_number = models.CharField(max_length=20, blank=True, default='')
    reason           = models.TextField()
    status           = models.CharField(
                           max_length=10, choices=Status.choices,
                           default=Status.PENDING, db_index=True
                       )
    proof_url        = models.URLField(blank=True, default='')  # Cloudinary screenshot
    requested_at     = models.DateTimeField(auto_now_add=True)
    processed_at     = models.DateTimeField(null=True, blank=True)
    processed_by     = models.ForeignKey(
                           'admin_panel.AdminUser', on_delete=models.SET_NULL,
                           null=True, blank=True, related_name='processed_refunds'
                       )

    class Meta:
        db_table = 'refunds'
        ordering = ['-requested_at']

    def __str__(self):
        return f'Refund for {self.order.order_number} — {self.status}'


class ExpenseCategory(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        db_table  = 'expense_categories'
        ordering  = ['name']
        verbose_name_plural = 'expense categories'

    def __str__(self):
        return self.name


class Expense(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category    = models.ForeignKey(
                      ExpenseCategory, on_delete=models.SET_NULL,
                      null=True, related_name='expenses'
                  )
    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    amount      = models.DecimalField(max_digits=12, decimal_places=2)
    receipt_url = models.URLField(blank=True, default='')  # Cloudinary
    incurred_on = models.DateField(db_index=True)
    recorded_by = models.ForeignKey(
                      'admin_panel.AdminUser', on_delete=models.SET_NULL,
                      null=True, related_name='recorded_expenses'
                  )
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'expenses'
        ordering = ['-incurred_on']
        indexes  = [
            models.Index(fields=['incurred_on', 'category']),
        ]

    def __str__(self):
        return f'{self.title} — {self.amount}'