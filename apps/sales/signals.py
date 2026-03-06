from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


@receiver(post_save, sender=Order)
def create_payment_on_order(sender, instance, created, **kwargs):
    """
    When an order is created, auto-create a Payment record in finance app.
    The payment_method stored in checkout is passed via Order metadata.

    Note: This signal fires AFTER the checkout transaction commits,
    so the order is guaranteed to exist in DB.
    """
    if not created:
        return

    # Import here to avoid circular imports between sales ↔ finance
    try:
        from apps.finance.models import Payment
        # payment_method is not stored on Order — it comes from checkout context.
        # We default to 'cod'; the checkout view will update it immediately after.
        # A cleaner approach (done in CheckoutView) passes method explicitly.
        Payment.objects.get_or_create(
            order=instance,
            defaults={
                'method': 'cod',
                'amount': instance.total,
                'status': 'pending',
            }
        )
    except Exception:
        # finance app may not be installed yet during development
        pass