from django.db import transaction
from django.db.models import Max


def generate_reference_number() -> str:
    """
    Atomic sequential reference number: JE-00001, JE-00002, ...
    Uses select_for_update to prevent duplicates under concurrent writes.
    """
    from .models import JournalEntry
    with transaction.atomic():
        last = JournalEntry.objects.select_for_update().aggregate(
            max_ref=Max('reference_number')
        )['max_ref']

        if last:
            try:
                num = int(last.split('-')[1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        return f'JE-{num:05d}'


# ─────────────────────────────────────────────────────────────────────────────
# Default Chart of Accounts
# Call this once via management command or migration to seed initial accounts.
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_ACCOUNTS = [
    # Assets
    {'code': '1000', 'name': 'Cash',                     'type': 'asset'},
    {'code': '1010', 'name': 'bKash Wallet',              'type': 'asset'},
    {'code': '1020', 'name': 'Nagad Wallet',              'type': 'asset'},
    {'code': '1100', 'name': 'Accounts Receivable',       'type': 'asset'},
    {'code': '1200', 'name': 'Inventory',                 'type': 'asset'},
    {'code': '1300', 'name': 'Prepaid Expenses',         'type': 'asset'},
    # Liabilities
    {'code': '2000', 'name': 'Accounts Payable',          'type': 'liability'},
    {'code': '2100', 'name': 'Customer Refunds Payable',  'type': 'liability'},
    {'code': '2200', 'name': 'Unearned Revenue', 'type': 'liability'},
    # Equity
    {'code': '3000', 'name': "Owner's Equity",            'type': 'equity'},
    {'code': '3100', 'name': 'Retained Earnings',         'type': 'equity'},
    # Revenue
    {'code': '4000', 'name': 'Sales Revenue',             'type': 'revenue'},
    {'code': '4100', 'name': 'Shipping Income',           'type': 'revenue'},
    # Expenses
    {'code': '5000', 'name': 'Cost of Goods Sold',        'type': 'expense'},
    {'code': '5100', 'name': 'Packaging Expense',         'type': 'expense'},
    {'code': '5200', 'name': 'Delivery Expense',          'type': 'expense'},
    {'code': '5300', 'name': 'Marketing Expense',         'type': 'expense'},
    {'code': '5400', 'name': 'Miscellaneous Expense',     'type': 'expense'},
    {'code': '5500', 'name': 'Transaction Charges',       'type': 'expense'},
    {'code': '5600', 'name': 'Bad Debt Expense',         'type': 'expense'},
    {'code': '5700', 'name': 'Food Expense',    'type': 'expense'},
]


def seed_chart_of_accounts():
    from .models import Account
    created = 0
    for entry in DEFAULT_ACCOUNTS:
        _, was_created = Account.objects.get_or_create(
            code=entry['code'],
            defaults={
                'name':         entry['name'],
                'account_type': entry['type'],
            }
        )
        if was_created:
            created += 1
    return created


# ─────────────────────────────────────────────────────────────────────────────
# Journal entry factory — used by signals
# ─────────────────────────────────────────────────────────────────────────────

def create_journal_entry(description: str, entry_date, lines: list, created_by=None) -> None:
    """
    lines = [
        {'account_code': '4000', 'debit': 0,      'credit': 1500, 'note': 'Sale revenue'},
        {'account_code': '1100', 'debit': 1500,   'credit': 0,    'note': 'Receivable'},
    ]
    Silently skips if any account code is missing (avoids crashing if not seeded yet).
    """
    from .models import Account, JournalEntry, JournalLine

    codes   = [l['account_code'] for l in lines]
    account_map = {a.code: a for a in Account.objects.filter(code__in=codes, is_active=True)}

    if len(account_map) != len(set(codes)):
        # One or more accounts not found — skip rather than crash
        return

    with transaction.atomic():
        entry = JournalEntry.objects.create(
            reference_number = generate_reference_number(),
            description      = description,
            entry_date       = entry_date,
            created_by       = created_by,
            is_posted        = True,   # auto-generated entries are posted immediately
        )
        JournalLine.objects.bulk_create([
            JournalLine(
                entry   = entry,
                account = account_map[l['account_code']],
                debit   = l.get('debit', 0),
                credit  = l.get('credit', 0),
                note    = l.get('note', ''),
            )
            for l in lines
        ])