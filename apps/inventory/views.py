from django.db.models import Prefetch
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from common.permissions import IsAdminUser
from common.pagination import StandardPagination
from apps.admin_panel.authentication import AdminJWTAuthentication
from .models import Category, Product, ProductImage, ProductVariant, Stock
from .serializers import (
    CategorySerializer,
    CategoryCreateSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductAdminSerializer,
    ProductCreateSerializer,
    ProductVariantAdminSerializer,
    ProductVariantCreateSerializer,
    StockUpdateSerializer,
    ProductImageSerializer,
)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def active_product_qs():
    """
    Reusable queryset for storefront — filters active products/variants,
    pre-joins everything needed to avoid N+1 on list and detail views.
    """
    return (
        Product.objects
        .filter(is_active=True)
        .select_related('category')
        .prefetch_related(
            'images',
            Prefetch(
                'variants',
                queryset=ProductVariant.objects
                    .filter(is_active=True)
                    .select_related('stock'),
            )
        )
    )


# ─────────────────────────────────────────────
# Storefront — Categories
# ─────────────────────────────────────────────

class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Only fetch root categories; children nested via serializer (1 level)
        # Result is Redis-cached by the cache middleware / manual cache in future
        categories = (
            Category.objects
            .filter(is_active=True, parent__isnull=True)
            .prefetch_related('children')
            .order_by('sort_order', 'name')
        )
        return Response(CategorySerializer(categories, many=True).data)


class CategoryDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            category = (
                Category.objects
                .prefetch_related('children')
                .get(slug=slug, is_active=True)
            )
        except Category.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        return Response(CategorySerializer(category).data)


# ─────────────────────────────────────────────
# Storefront — Products
# ─────────────────────────────────────────────

class ProductListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = active_product_qs()

        # Filters
        category_slug = request.query_params.get('category')
        search        = request.query_params.get('search')
        featured      = request.query_params.get('featured')

        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if search:
            qs = qs.filter(name__icontains=search)
        if featured == 'true':
            qs = qs.filter(is_featured=True)

        paginator  = StandardPagination()
        page       = paginator.paginate_queryset(qs, request)
        serializer = ProductListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            product = active_product_qs().get(slug=slug)
        except Product.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        return Response(ProductDetailSerializer(product).data)


# ─────────────────────────────────────────────
# Admin — Categories
# ─────────────────────────────────────────────

class AdminCategoryListCreateView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        categories = Category.objects.prefetch_related('children').order_by('sort_order')
        return Response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        serializer = CategoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return Response(CategorySerializer(category).data, status=201)


class AdminCategoryDetailView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get_object(self, pk):
        try:
            return Category.objects.prefetch_related('children').get(pk=pk)
        except Category.DoesNotExist:
            return None

    def patch(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({'detail': 'Not found.'}, status=404)
        serializer = CategoryCreateSerializer(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CategorySerializer(category).data)


# ─────────────────────────────────────────────
# Admin — Products
# ─────────────────────────────────────────────

class AdminProductListCreateView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get(self, request):
        qs = (
            Product.objects
            .select_related('category')
            .prefetch_related(
                'images',
                Prefetch(
                    'variants',
                    queryset=ProductVariant.objects.select_related('stock')
                )
            )
            .order_by('-created_at')
        )
        paginator  = StandardPagination()
        page       = paginator.paginate_queryset(qs, request)
        serializer = ProductAdminSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(ProductAdminSerializer(product).data, status=201)


class AdminProductDetailView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get_object(self, pk):
        try:
            return (
                Product.objects
                .select_related('category')
                .prefetch_related(
                    'images',
                    Prefetch('variants', queryset=ProductVariant.objects.select_related('stock'))
                )
                .get(pk=pk)
            )
        except Product.DoesNotExist:
            return None

    def patch(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'detail': 'Not found.'}, status=404)
        serializer = ProductCreateSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProductAdminSerializer(product).data)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'detail': 'Not found.'}, status=404)
        # Soft delete — never hard delete products (order history references them)
        product.is_active = False
        product.save(update_fields=['is_active'])
        return Response(status=204)


# ─────────────────────────────────────────────
# Admin — Variants
# ─────────────────────────────────────────────

class AdminVariantCreateView(APIView):
    """POST /products/{id}/variants/"""
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def post(self, request, product_pk):
        try:
            product = Product.objects.get(pk=product_pk)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found.'}, status=404)

        serializer = ProductVariantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant = serializer.save(product=product)
        return Response(ProductVariantAdminSerializer(variant).data, status=201)


class AdminVariantDetailView(APIView):
    """PATCH /variants/{id}/"""
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def get_object(self, pk):
        try:
            return ProductVariant.objects.select_related('stock').get(pk=pk)
        except ProductVariant.DoesNotExist:
            return None

    def patch(self, request, pk):
        variant = self.get_object(pk)
        if not variant:
            return Response({'detail': 'Not found.'}, status=404)
        serializer = ProductVariantAdminSerializer(variant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProductVariantAdminSerializer(variant).data)


class AdminVariantStockView(APIView):
    """PATCH /variants/{id}/stock/"""
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def patch(self, request, pk):
        try:
            stock = Stock.objects.select_related('variant').get(variant__pk=pk)
        except Stock.DoesNotExist:
            return Response({'detail': 'Stock not found.'}, status=404)

        serializer = StockUpdateSerializer(stock, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StockUpdateSerializer(stock).data)


# ─────────────────────────────────────────────
# Admin — Product Images
# ─────────────────────────────────────────────

class AdminProductImageView(APIView):
    """
    POST   /products/{id}/images/        ← add image URL (frontend already uploaded to Cloudinary)
    DELETE /products/{id}/images/{img_id}/
    """
    authentication_classes = [AdminJWTAuthentication]
    permission_classes     = [IsAdminUser]

    def post(self, request, product_pk):
        try:
            product = Product.objects.get(pk=product_pk)
        except Product.DoesNotExist:
            return Response({'detail': 'Product not found.'}, status=404)

        serializer = ProductImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image = serializer.save(product=product)
        return Response(ProductImageSerializer(image).data, status=201)

    def delete(self, request, product_pk, img_pk):
        try:
            image = ProductImage.objects.get(pk=img_pk, product__pk=product_pk)
        except ProductImage.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        image.delete()
        return Response(status=204)