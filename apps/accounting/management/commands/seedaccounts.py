from django.core.management.base import BaseCommand
from apps.accounting.utils import seed_chart_of_accounts


class Command(BaseCommand):
    help = 'Seed the default chart of accounts (run once after first migrate)'

    def handle(self, *args, **kwargs):
        created = seed_chart_of_accounts()
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created {created} accounts.'))
        else:
            self.stdout.write('Chart of accounts already seeded — nothing to do.')