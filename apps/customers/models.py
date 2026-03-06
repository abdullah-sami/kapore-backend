import uuid
from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Customer(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email       = models.EmailField(unique=True, db_index=True)
    phone       = models.CharField(max_length=20, unique=True, db_index=True)
    full_name   = models.CharField(max_length=255)
    password    = models.CharField(max_length=255)
    avatar_url  = models.URLField(blank=True, default='')   # Cloudinary URL from frontend
    is_active   = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    # DRF compatibility
    is_anonymous     = False
    is_authenticated = True

    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} <{self.email}>'

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)


class CustomerAddress(models.Model):
    class Label(models.TextChoices):
        HOME  = 'home',  'Home'
        WORK  = 'work',  'Work'
        OTHER = 'other', 'Other'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer     = models.ForeignKey(
                       Customer, on_delete=models.CASCADE, related_name='addresses'
                   )
    label        = models.CharField(max_length=10, choices=Label.choices, default=Label.HOME)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, default='')
    city         = models.CharField(max_length=100)
    district     = models.CharField(max_length=100, blank=True, default='')
    postal_code  = models.CharField(max_length=20, blank=True, default='')
    country      = models.CharField(max_length=100, default='Bangladesh')
    is_default   = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customer_addresses'
        ordering = ['-is_default', '-created_at']

    def save(self, *args, **kwargs):
        # Enforce only one default address per customer
        if self.is_default:
            CustomerAddress.objects.filter(
                customer=self.customer, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.customer.full_name} — {self.label}'


class CustomerSession(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer      = models.ForeignKey(
                        Customer, on_delete=models.CASCADE, related_name='sessions'
                    )
    refresh_token = models.TextField(unique=True)
    device_info   = models.CharField(max_length=500, blank=True, default='')
    ip_address    = models.GenericIPAddressField(null=True, blank=True)
    expires_at    = models.DateTimeField()
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customer_sessions'
        indexes  = [models.Index(fields=['refresh_token'])]