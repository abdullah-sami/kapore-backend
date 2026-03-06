from django.urls import path
from .views import (
    # Storefront
    CategoryListView,
    CategoryDetailView,
    ProductListView,
    ProductDetailView,
    # Admin — categories
    AdminCategoryListCreateView,
    AdminCategoryDetailView,
    # Admin — products
    AdminProductListCreateView,
    AdminProductDetailView,
    # Admin — variants
    AdminVariantCreateView,
    AdminVariantDetailView,
    AdminVariantStockView,
    # Admin — images
    AdminProductImageView,
)

urlpatterns = [
    # ── Storefront (public) ──────────────────────────────
    path('categories/',               CategoryListView.as_view()),
    path('categories/<slug:slug>/',   CategoryDetailView.as_view()),
    path('products/',                 ProductListView.as_view()),
    path('products/<slug:slug>/',     ProductDetailView.as_view()),

    # ── Admin — categories ───────────────────────────────
    path('admin/categories/',             AdminCategoryListCreateView.as_view()),
    path('admin/categories/<uuid:pk>/',   AdminCategoryDetailView.as_view()),

    # ── Admin — products ─────────────────────────────────
    path('admin/products/',               AdminProductListCreateView.as_view()),
    path('admin/products/<uuid:pk>/',     AdminProductDetailView.as_view()),

    # ── Admin — variants ─────────────────────────────────
    path('admin/products/<uuid:product_pk>/variants/', AdminVariantCreateView.as_view()),
    path('admin/variants/<uuid:pk>/',                  AdminVariantDetailView.as_view()),
    path('admin/variants/<uuid:pk>/stock/',            AdminVariantStockView.as_view()),

    # ── Admin — images ───────────────────────────────────
    path('admin/products/<uuid:product_pk>/images/',                   AdminProductImageView.as_view()),
    path('admin/products/<uuid:product_pk>/images/<uuid:img_pk>/',     AdminProductImageView.as_view()),
]