# apps/admin_panel/management/commands/createsuperadmin.py
from django.core.management.base import BaseCommand
from apps.admin_panel.models import AdminUser

class Command(BaseCommand):
    help = 'Create an initial superadmin user'

    def handle(self, *args, **kwargs):
        email = input('Email: ')
        full_name = input('Full name: ')
        password = input('Password: ')

        admin = AdminUser.objects.create(
            email=email,
            full_name=full_name,
            role='superadmin',
            is_active=True,
        )
        admin.set_password(password)
        admin.save()

        self.stdout.write(self.style.SUCCESS(f'Superadmin "{email}" created.'))