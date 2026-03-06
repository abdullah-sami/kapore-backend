# from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    # path('', admin.site.urls),
    path('api/v1/customers/',  include('apps.customers.urls')),
    path('api/v1/inventory/',  include('apps.inventory.urls')),
    path('api/v1/sales/',      include('apps.sales.urls')),
    path('api/v1/finance/',    include('apps.finance.urls')),
    path('api/v1/admin/',      include('apps.admin_panel.urls')),
    path('api/v1/accounting/', include('apps.accounting.urls')),
]