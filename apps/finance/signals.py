from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='sales.Order')
def create_payment_record(sender, instance, created, **kwargs):
    """
    Auto-create a Payment row whenever a new Order is saved.
    The checkout view passes payment_method via instance._payment_method
    (a transient attribute set just before save in CheckoutView).
    Falls back to 'cod' if not set.
    """
    if not created:
        return

    from .models import Payment

    # Avoid duplicate if signal fires more than once (e.g. test runners)
    if Payment.objects.filter(order=instance).exists():
        return

    method = getattr(instance, '_payment_method', Payment.Method.COD)

    Payment.objects.create(
        order  = instance,
        method = method,
        amount = instance.total,
        status = Payment.Status.PENDING,
    )