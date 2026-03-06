from decimal import Decimal
from django.db.models import Sum, Q


def _account_balances(account_type: str, date_filter=None, date_from=None, date_to=None):
    """
    Returns {account_code: {name, debit_total, credit_total, balance}} for
    all posted journal lines matching account_type and optional date range.
    Uses values() + annotate() — never loads ORM objects into memory.
    """
    from .models import JournalLine

    qs = (
        JournalLine.objects
        .filter(
            entry__is_posted=True,
            account__account_type=account_type,
            account__is_active=True,
        )
        .select_related('account')
    )

    if date_filter:
        qs = qs.filter(entry__entry_date__lte=date_filter)
    if date_from:
        qs = qs.filter(entry__entry_date__gte=date_from)
    if date_to:
        qs = qs.filter(entry__entry_date__lte=date_to)

    rows = (
        qs
        .values('account__code', 'account__name', 'account__account_type')
        .annotate(
            total_debit  = Sum('debit'),
            total_credit = Sum('credit'),
        )
        .order_by('account__code')
    )

    result = []
    for row in rows:
        debit  = row['total_debit']  or Decimal('0')
        credit = row['total_credit'] or Decimal('0')
        # Normal balance: assets/expenses → debit; liabilities/equity/revenue → credit
        atype  = row['account__account_type']
        if atype in ('asset', 'expense'):
            balance = debit - credit
        else:
            balance = credit - debit

        result.append({
            'code':    row['account__code'],
            'name':    row['account__name'],
            'debit':   debit,
            'credit':  credit,
            'balance': balance,
        })

    return result


def get_balance_sheet(as_of_date):
    """
    Returns assets, liabilities, equity with totals.
    as_of_date: date string 'YYYY-MM-DD' or date object
    """
    assets      = _account_balances('asset',     date_filter=as_of_date)
    liabilities = _account_balances('liability',  date_filter=as_of_date)
    equity      = _account_balances('equity',     date_filter=as_of_date)

    total_assets      = sum(r['balance'] for r in assets)
    total_liabilities = sum(r['balance'] for r in liabilities)
    total_equity      = sum(r['balance'] for r in equity)

    return {
        'as_of':       str(as_of_date),
        'assets': {
            'accounts': assets,
            'total':    total_assets,
        },
        'liabilities': {
            'accounts': liabilities,
            'total':    total_liabilities,
        },
        'equity': {
            'accounts': equity,
            'total':    total_equity,
        },
        'liabilities_and_equity': total_liabilities + total_equity,
        'balanced': total_assets == (total_liabilities + total_equity),
    }


def get_profit_and_loss(date_from, date_to):
    """
    Revenue - Expenses = Net Profit/Loss for a given period.
    """
    revenue  = _account_balances('revenue', date_from=date_from, date_to=date_to)
    expenses = _account_balances('expense', date_from=date_from, date_to=date_to)

    total_revenue  = sum(r['balance'] for r in revenue)
    total_expenses = sum(r['balance'] for r in expenses)
    net            = total_revenue - total_expenses

    return {
        'from':  str(date_from),
        'to':    str(date_to),
        'revenue': {
            'accounts': revenue,
            'total':    total_revenue,
        },
        'expenses': {
            'accounts': expenses,
            'total':    total_expenses,
        },
        'net_profit': net,
        'profitable': net >= 0,
    }


def get_trial_balance(as_of_date):
    """
    All accounts with their debit/credit totals — used to verify books balance.
    sum(all debits) should equal sum(all credits).
    """
    from .models import JournalLine

    rows = (
        JournalLine.objects
        .filter(entry__is_posted=True, entry__entry_date__lte=as_of_date)
        .values('account__code', 'account__name', 'account__account_type')
        .annotate(
            total_debit  = Sum('debit'),
            total_credit = Sum('credit'),
        )
        .order_by('account__account_type', 'account__code')
    )

    accounts = []
    grand_debit = grand_credit = Decimal('0')

    for row in rows:
        d = row['total_debit']  or Decimal('0')
        c = row['total_credit'] or Decimal('0')
        grand_debit  += d
        grand_credit += c
        accounts.append({
            'code':         row['account__code'],
            'name':         row['account__name'],
            'account_type': row['account__account_type'],
            'debit':        d,
            'credit':       c,
        })

    return {
        'as_of':        str(as_of_date),
        'accounts':     accounts,
        'total_debit':  grand_debit,
        'total_credit': grand_credit,
        'balanced':     grand_debit == grand_credit,
    }