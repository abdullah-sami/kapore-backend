from django.urls import path
from .views import (
    AccountListCreateView,
    AccountDetailView,
    JournalEntryListCreateView,
    JournalEntryDetailView,
    JournalEntryPostView,
    BalanceSheetView,
    ProfitLossView,
    TrialBalanceView,
)

urlpatterns = [
    # Chart of accounts
    path('accounts/',             AccountListCreateView.as_view()),
    path('accounts/<uuid:pk>/',   AccountDetailView.as_view()),

    # Journal entries
    path('journal-entries/',                        JournalEntryListCreateView.as_view()),
    path('journal-entries/<uuid:pk>/',              JournalEntryDetailView.as_view()),
    path('journal-entries/<uuid:pk>/post/',         JournalEntryPostView.as_view()),

    # Reports
    path('reports/balance-sheet/',  BalanceSheetView.as_view()),
    path('reports/profit-loss/',    ProfitLossView.as_view()),
    path('reports/trial-balance/',  TrialBalanceView.as_view()),
]