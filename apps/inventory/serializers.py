from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductVariant, Stock


# ─────────────────────────────────────────────
# Stock
# ─────────────────────────────────────────────

class StockSerializer(serializers.ModelSerializer):
    is_low      = serializers.BooleanField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Stock
        fields = ['quantity', 'low_stock_threshold', 'is_low', 'is_in_stock', 'updated_at']
        read_only_fields = ['updated_at']


class StockUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Stock
        fields = ['quantity', 'low_stock_threshold']


# ─────────────────────────────────────────────
# Product images
# ─────────────────────────────────────────────

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductImage
        fields = ['id', 'image_url', 'is_primary', 'sort_order']
        read_only_fields = ['id']


# ─────────────────────────────────────────────
# Variants — storefront (no cost_price)
# ─────────────────────────────────────────────

class ProductVariantStorefrontSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)

    class Meta:
        model  = ProductVariant
        fields = [
            'id', 'sku', 'size', 'color', 'material', 'attributes',
            'price', 'compare_price', 'is_active', 'stock',
        ]


# ─────────────────────────────────────────────
# Variants — admin (includes cost_price)
# ─────────────────────────────────────────────

class ProductVariantAdminSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)

    class Meta:
        model  = ProductVariant
        fields = [
            'id', 'sku', 'size', 'color', 'material', 'attributes',
            'price', 'compare_price', 'cost_price', 'is_active',
            'stock', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductVariantCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductVariant
        fields = [
            'sku', 'size', 'color', 'material', 'attributes',
            'price', 'compare_price', 'cost_price', 'is_active',
        ]

    def validate_sku(self, value):
        if ProductVariant.objects.filter(sku=value).exists():
            raise serializers.ValidationError('A variant with this SKU already exists.')
        return value

    def create(self, validated_data):
        variant = super().create(validated_data)
        # Auto-create a Stock record with 0 quantity
        Stock.objects.create(variant=variant)
        return variant


# ─────────────────────────────────────────────
# Category
# ─────────────────────────────────────────────

class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = [
            'id', 'name', 'slug', 'parent', 'image_url',
            'is_active', 'sort_order', 'children',
        ]
        read_only_fields = ['id', 'slug']

    def get_children(self, obj):
        # Only recurse one level deep to avoid heavy nesting
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data


class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Category
        fields = ['name', 'parent', 'image_url', 'is_active', 'sort_order']


# ─────────────────────────────────────────────
# Product — storefront list (lightweight)
# ─────────────────────────────────────────────

class ProductListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    min_price     = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'category',
            'is_featured', 'primary_image', 'min_price',
        ]

    def get_primary_image(self, obj):
        # images are prefetched — no extra query
        for img in obj.images.all():
            if img.is_primary:
                return img.image_url
        images = list(obj.images.all())
        return images[0].image_url if images else None

    def get_min_price(self, obj):
        prices = [v.price for v in obj.variants.all() if v.is_active]
        return min(prices) if prices else None


# ─────────────────────────────────────────────
# Product — storefront detail (full)
# ─────────────────────────────────────────────

class ProductDetailSerializer(serializers.ModelSerializer):
    images   = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantStorefrontSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'category', 'is_featured', 'images', 'variants',
            'created_at', 'updated_at',
        ]


# ─────────────────────────────────────────────
# Product — admin (create / update)
# ─────────────────────────────────────────────

class ProductAdminSerializer(serializers.ModelSerializer):
    images   = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantAdminSerializer(many=True, read_only=True)

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'description', 'category',
            'is_active', 'is_featured', 'images', 'variants',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = ['name', 'category', 'description', 'is_active', 'is_featured']