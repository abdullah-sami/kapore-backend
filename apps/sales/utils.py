from django.db import transaction
from django.db.models import Max


def generate_order_number() -> str:
    """
    Generates a sequential human-readable order number like KAP-00001.
    Uses select_for_update inside a transaction to prevent race conditions
    under concurrent checkouts.
    """
    from .models import Order
    with transaction.atomic():
        last = Order.objects.select_for_update().aggregate(
            max_num=Max('order_number')
        )['max_num']

        if last:
            # Extract numeric part e.g. "KAP-00123" → 123
            try:
                num = int(last.split('-')[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        return f'KAP-{num:05d}'


def build_variant_label(variant) -> str:
    """Compose a readable label from variant attributes."""
    parts = [variant.size, variant.color, variant.material]
    return ' / '.join(p for p in parts if p)