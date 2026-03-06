import uuid
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name       = models.CharField(max_length=255)
    slug       = models.SlugField(unique=True, db_index=True, max_length=255)
    parent     = models.ForeignKey(
                     'self', on_delete=models.SET_NULL,
                     null=True, blank=True, related_name='children'
                 )
    image_url  = models.URLField(blank=True, default='')   # Cloudinary
    is_active  = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table  = 'categories'
        ordering  = ['sort_order', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category    = models.ForeignKey(
                      Category, on_delete=models.SET_NULL,
                      null=True, blank=True, related_name='products'
                  )
    name        = models.CharField(max_length=255)
    slug        = models.SlugField(unique=True, db_index=True, max_length=255)
    description = models.TextField(blank=True, default='')
    is_active   = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product    = models.ForeignKey(
                     Product, on_delete=models.CASCADE, related_name='images'
                 )
    image_url  = models.URLField()   # Cloudinary — frontend uploads, sends URL
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'product_images'
        ordering = ['-is_primary', 'sort_order']

    def save(self, *args, **kwargs):
        # Enforce only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product       = models.ForeignKey(
                        Product, on_delete=models.CASCADE, related_name='variants'
                    )
    sku           = models.CharField(max_length=100, unique=True, db_index=True)
    size          = models.CharField(max_length=50, blank=True, default='')
    color         = models.CharField(max_length=50, blank=True, default='')
    material      = models.CharField(max_length=100, blank=True, default='')
    # Extra flexible attributes (e.g. {"weight": "500g", "style": "slim"})
    attributes    = models.JSONField(default=dict, blank=True)
    price         = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # cost_price is admin-only — never serialized in storefront responses
    cost_price    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active     = models.BooleanField(default=True, db_index=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_variants'
        indexes  = [models.Index(fields=['product', 'is_active'])]

    def __str__(self):
        return f'{self.product.name} — {self.sku}'


class Stock(models.Model):
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variant             = models.OneToOneField(
                              ProductVariant, on_delete=models.CASCADE, related_name='stock'
                          )
    quantity            = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stock'

    def __str__(self):
        return f'{self.variant.sku} — qty: {self.quantity}'

    @property
    def is_low(self):
        return self.quantity <= self.low_stock_threshold

    @property
    def is_in_stock(self):
        return self.quantity > 0