import uuid
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class AdminUser(models.Model):
    class Role(models.TextChoices):
        SUPERADMIN = 'superadmin', 'Superadmin'
        MANAGER    = 'manager',    'Manager'
        STAFF      = 'staff',      'Staff'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email      = models.EmailField(unique=True, db_index=True)
    full_name  = models.CharField(max_length=255)
    password   = models.CharField(max_length=255)
    role       = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    is_active  = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Required by DRF JWTAuthentication — treats AdminUser like a user object
    is_anonymous     = False
    is_authenticated = True

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'admin_users'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} ({self.role})'

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    # Minimal stubs so DRF permission checks don't crash
    def has_perm(self, perm, obj=None): return self.role == self.Role.SUPERADMIN
    def has_module_perms(self, app_label): return self.role == self.Role.SUPERADMIN


class ActivityLog(models.Model):
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin          = models.ForeignKey(
                         AdminUser, on_delete=models.SET_NULL,
                         null=True, related_name='activity_logs'
                     )
    action         = models.CharField(max_length=500)
    # GenericForeignKey — can point to any model (Order, Payment, Product, etc.)
    content_type   = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id      = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    ip_address     = models.GenericIPAddressField(null=True, blank=True)
    timestamp      = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'activity_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f'[{self.timestamp:%Y-%m-%d %H:%M}] {self.admin} — {self.action}'