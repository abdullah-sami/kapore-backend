# Kapore — REST API Documentation

**Base URL:** `https://kaporebackend.com`  
**API Version:** `v1`  
**All endpoints prefixed with:** `/api/v1/`

---

## Table of Contents

- [Authentication](#authentication)
- [Error Format](#error-format)
- [Pagination](#pagination)
- [1. Customers](#1-customers)
- [2. Inventory](#2-inventory)
- [3. Sales](#3-sales)
- [4. Finance](#4-finance)
- [5. Admin Panel](#5-admin-panel)
- [6. Accounting](#6-accounting)

---

## Authentication

Two separate JWT token systems are used — one for customers, one for admin users. They are **not interchangeable**.

### Customer Tokens
Issued by `POST /api/v1/customers/auth/login/`  
Sent as: `Authorization: Bearer <access_token>`

### Admin Tokens
Issued by `POST /api/v1/admin/auth/login/`  
Sent as: `Authorization: Bearer <access_token>`

### Guest Cart Sessions
For unauthenticated cart access, issue a session key via `POST /api/v1/sales/cart/session/`  
Sent as: `X-Cart-Session: <session_key>`

---

## Error Format

All errors follow a uniform shape:

```json
{
  "error": true,
  "status_code": 400,
  "detail": {
    "field_name": ["Error message here."]
  }
}
```

For non-field errors:
```json
{
  "error": true,
  "status_code": 401,
  "detail": "Invalid credentials."
}
```

---

## Pagination

Paginated responses include:

```json
{
  "count": 100,
  "next": "https://kaporebackend.com/api/v1/inventory/products/?page=2",
  "previous": null,
  "results": []
}
```

- Default page size: `20`
- Max page size: `100`
- Query params: `?page=2&page_size=50`
- Total count also returned in header: `X-Total-Count: 100`

---

---

# 1. Customers

**Base path:** `/api/v1/customers/`

---

## POST `/api/v1/customers/auth/register/`

Register a new customer account.

**Auth required:** No

**Request Body:**
```json
{
  "email": "aisha@example.com",
  "phone": "01712345678",
  "full_name": "Aisha Rahman",
  "password": "securepass123"
}
```

**Response `201`:**
```json
{
  "customer": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "aisha@example.com",
    "phone": "01712345678",
    "full_name": "Aisha Rahman",
    "avatar_url": "",
    "is_verified": false,
    "created_at": "2025-03-01T10:00:00Z"
  },
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

**Errors:**
- `400` — email or phone already registered

---

## POST `/api/v1/customers/auth/login/`

Log in with email and password.

**Auth required:** No

**Request Body:**
```json
{
  "email": "aisha@example.com",
  "password": "securepass123"
}
```

**Response `200`:**
```json
{
  "customer": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "aisha@example.com",
    "phone": "01712345678",
    "full_name": "Aisha Rahman",
    "avatar_url": "",
    "is_verified": false,
    "created_at": "2025-03-01T10:00:00Z"
  },
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

**Errors:**
- `401` — invalid credentials

---

## POST `/api/v1/customers/auth/logout/`

Log out the current customer (client should discard tokens).

**Auth required:** Customer JWT

**Request Body:** _(empty)_

**Response `200`:**
```json
{
  "detail": "Logged out."
}
```

---

## POST `/api/v1/customers/auth/refresh/`

Refresh an expired access token.

**Auth required:** No

**Request Body:**
```json
{
  "refresh": "<refresh_token>"
}
```

**Response `200`:**
```json
{
  "access": "<new_access_token>"
}
```

**Errors:**
- `401` — invalid or expired refresh token

---

## GET `/api/v1/customers/me/`

Get the authenticated customer's profile.

**Auth required:** Customer JWT

**Response `200`:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "aisha@example.com",
  "phone": "01712345678",
  "full_name": "Aisha Rahman",
  "avatar_url": "https://res.cloudinary.com/demo/image/upload/avatar.jpg",
  "is_verified": false,
  "created_at": "2025-03-01T10:00:00Z"
}
```

---

## PATCH `/api/v1/customers/me/`

Update the authenticated customer's profile.

**Auth required:** Customer JWT

**Request Body** _(all fields optional)_:
```json
{
  "full_name": "Aisha K. Rahman",
  "phone": "01798765432",
  "avatar_url": "https://res.cloudinary.com/demo/image/upload/new_avatar.jpg"
}
```

**Response `200`:** Same as `GET /me/`

**Errors:**
- `400` — phone number already in use by another account

---

## GET `/api/v1/customers/me/addresses/`

List all addresses for the authenticated customer.

**Auth required:** Customer JWT

**Response `200`:**
```json
[
  {
    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "label": "home",
    "address_line_1": "12/A Mirpur Road",
    "address_line_2": "Flat 3B",
    "city": "Dhaka",
    "district": "Dhaka",
    "postal_code": "1216",
    "country": "Bangladesh",
    "is_default": true
  }
]
```

---

## POST `/api/v1/customers/me/addresses/`

Add a new address.

**Auth required:** Customer JWT

**Request Body:**
```json
{
  "label": "work",
  "address_line_1": "Plot 5, Road 12, Banani",
  "address_line_2": "",
  "city": "Dhaka",
  "district": "Dhaka",
  "postal_code": "1213",
  "country": "Bangladesh",
  "is_default": false
}
```

**Response `201`:** Address object (same shape as list item above)

---

## PATCH `/api/v1/customers/me/addresses/{id}/`

Update an existing address.

**Auth required:** Customer JWT

**Request Body** _(all fields optional)_:
```json
{
  "is_default": true
}
```

**Response `200`:** Updated address object

**Errors:**
- `404` — address not found or does not belong to this customer

---

## DELETE `/api/v1/customers/me/addresses/{id}/`

Delete an address.

**Auth required:** Customer JWT

**Response `204`:** _(no body)_

---

---

# 2. Inventory

**Base path:** `/api/v1/inventory/`

---

## GET `/api/v1/inventory/categories/`

List all root categories (with nested children).

**Auth required:** No

**Response `200`:**
```json
[
  {
    "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "name": "Men's Clothing",
    "slug": "mens-clothing",
    "parent": null,
    "image_url": "https://res.cloudinary.com/demo/image/upload/mens.jpg",
    "is_active": true,
    "sort_order": 1,
    "children": [
      {
        "id": "d4e5f6a7-b8c9-0123-def0-234567890123",
        "name": "T-Shirts",
        "slug": "t-shirts",
        "parent": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "image_url": "",
        "is_active": true,
        "sort_order": 1,
        "children": []
      }
    ]
  }
]
```

---

## GET `/api/v1/inventory/categories/{slug}/`

Get a single category by slug.

**Auth required:** No

**Response `200`:** Same shape as a single item from the list above

**Errors:**
- `404` — category not found or inactive

---

## GET `/api/v1/inventory/products/`

List active products (paginated).

**Auth required:** No

**Query Parameters:**

| Param | Type | Description |
|---|---|---|
| `category` | string | Filter by category slug |
| `search` | string | Search by product name |
| `featured` | `true` | Return only featured products |
| `page` | integer | Page number |
| `page_size` | integer | Results per page (max 100) |

**Example:** `GET /api/v1/inventory/products/?category=t-shirts&featured=true&page=1`

**Response `200`:**
```json
{
  "count": 42,
  "next": "https://kaporebackend.com/api/v1/inventory/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
      "name": "Classic White Tee",
      "slug": "classic-white-tee",
      "category": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "is_featured": true,
      "primary_image": "https://res.cloudinary.com/demo/image/upload/tee.jpg",
      "min_price": "490.00"
    }
  ]
}
```

---

## GET `/api/v1/inventory/products/{slug}/`

Get full product detail including all variants, images, and stock.

**Auth required:** No

**Response `200`:**
```json
{
  "id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
  "name": "Classic White Tee",
  "slug": "classic-white-tee",
  "description": "100% cotton premium quality tee.",
  "category": {
    "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "name": "Men's Clothing",
    "slug": "mens-clothing",
    "parent": null,
    "image_url": "",
    "is_active": true,
    "sort_order": 1,
    "children": []
  },
  "is_featured": true,
  "images": [
    {
      "id": "f6a7b8c9-d0e1-2345-f012-456789012345",
      "image_url": "https://res.cloudinary.com/demo/image/upload/tee_front.jpg",
      "is_primary": true,
      "sort_order": 0
    }
  ],
  "variants": [
    {
      "id": "a7b8c9d0-e1f2-3456-0123-567890123456",
      "sku": "CWT-M-WHT",
      "size": "M",
      "color": "White",
      "material": "Cotton",
      "attributes": {},
      "price": "490.00",
      "compare_price": "650.00",
      "is_active": true,
      "stock": {
        "quantity": 45,
        "low_stock_threshold": 5,
        "is_low": false,
        "is_in_stock": true,
        "updated_at": "2025-03-01T08:00:00Z"
      }
    }
  ],
  "created_at": "2025-02-10T12:00:00Z",
  "updated_at": "2025-02-20T15:30:00Z"
}
```

**Errors:**
- `404` — product not found or inactive

---

## POST `/api/v1/inventory/admin/categories/`

Create a new category.

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "name": "Accessories",
  "parent": null,
  "image_url": "https://res.cloudinary.com/demo/image/upload/accessories.jpg",
  "is_active": true,
  "sort_order": 5
}
```

**Response `201`:** Full category object

---

## GET `/api/v1/inventory/admin/categories/`

List all categories (including inactive) for admin.

**Auth required:** Admin JWT

**Response `200`:** Array of category objects (same shape as storefront)

---

## PATCH `/api/v1/inventory/admin/categories/{id}/`

Update a category by UUID.

**Auth required:** Admin JWT

**Request Body** _(all fields optional)_:
```json
{
  "is_active": false,
  "sort_order": 3
}
```

**Response `200`:** Updated category object

---

## GET `/api/v1/inventory/admin/products/`

List all products (including inactive) for admin, paginated.

**Auth required:** Admin JWT

**Response `200`:** Paginated list with full variant and cost_price data included

---

## POST `/api/v1/inventory/admin/products/`

Create a new product.

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "name": "Slim Fit Chinos",
  "category": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "description": "Comfortable slim fit chinos for everyday wear.",
  "is_active": true,
  "is_featured": false
}
```

**Response `201`:** Full product admin object (slug auto-generated from name)

---

## PATCH `/api/v1/inventory/admin/products/{id}/`

Update an existing product.

**Auth required:** Admin JWT

**Request Body** _(all fields optional)_:
```json
{
  "is_featured": true,
  "description": "Updated description."
}
```

**Response `200`:** Updated product admin object

---

## DELETE `/api/v1/inventory/admin/products/{id}/`

Soft-delete a product (sets `is_active = false`). Order history is preserved.

**Auth required:** Admin JWT

**Response `204`:** _(no body)_

---

## POST `/api/v1/inventory/admin/products/{id}/variants/`

Add a new variant to a product. A stock record with `quantity: 0` is created automatically.

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "sku": "CWT-L-BLK",
  "size": "L",
  "color": "Black",
  "material": "Cotton",
  "attributes": {},
  "price": "490.00",
  "compare_price": "650.00",
  "cost_price": "180.00",
  "is_active": true
}
```

**Response `201`:**
```json
{
  "id": "b8c9d0e1-f2a3-4567-1234-678901234567",
  "sku": "CWT-L-BLK",
  "size": "L",
  "color": "Black",
  "material": "Cotton",
  "attributes": {},
  "price": "490.00",
  "compare_price": "650.00",
  "cost_price": "180.00",
  "is_active": true,
  "stock": {
    "quantity": 0,
    "low_stock_threshold": 5,
    "is_low": true,
    "is_in_stock": false,
    "updated_at": "2025-03-01T10:00:00Z"
  },
  "created_at": "2025-03-01T10:00:00Z",
  "updated_at": "2025-03-01T10:00:00Z"
}
```

**Errors:**
- `400` — SKU already exists
- `404` — product not found

---

## PATCH `/api/v1/inventory/admin/variants/{id}/`

Update a variant's details (price, attributes, active status, etc.).

**Auth required:** Admin JWT

**Request Body** _(all fields optional)_:
```json
{
  "price": "520.00",
  "is_active": false
}
```

**Response `200`:** Updated variant admin object

---

## PATCH `/api/v1/inventory/admin/variants/{id}/stock/`

Update stock quantity or low-stock threshold for a variant.

**Auth required:** Admin JWT

**Request Body** _(all fields optional)_:
```json
{
  "quantity": 120,
  "low_stock_threshold": 10
}
```

**Response `200`:**
```json
{
  "quantity": 120,
  "low_stock_threshold": 10
}
```

---

## POST `/api/v1/inventory/admin/products/{id}/images/`

Attach a Cloudinary image URL to a product. Upload the image to Cloudinary on the frontend first, then send the resulting URL here.

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "image_url": "https://res.cloudinary.com/demo/image/upload/product_shot.jpg",
  "is_primary": true,
  "sort_order": 0
}
```

**Response `201`:**
```json
{
  "id": "c9d0e1f2-a3b4-5678-2345-789012345678",
  "image_url": "https://res.cloudinary.com/demo/image/upload/product_shot.jpg",
  "is_primary": true,
  "sort_order": 0
}
```

---

## DELETE `/api/v1/inventory/admin/products/{product_id}/images/{image_id}/`

Remove an image from a product.

**Auth required:** Admin JWT

**Response `204`:** _(no body)_

---

---

# 3. Sales

**Base path:** `/api/v1/sales/`

---

## POST `/api/v1/sales/cart/session/`

Issue a guest cart session key. Call this on the customer's first site visit and store the returned `session_key` in `localStorage`. Pass it in all subsequent cart requests via the `X-Cart-Session` header.

**Auth required:** No

**Request Body:** _(empty)_

**Response `201`:**
```json
{
  "session_key": "d0e1f2a3-b4c5-6789-3456-890123456789"
}
```

---

## GET `/api/v1/sales/cart/`

Get the current cart (guest or authenticated customer).

**Auth required:** No (guest: `X-Cart-Session` header | logged-in: Customer JWT)

**Response `200`:**
```json
{
  "id": "e1f2a3b4-c5d6-7890-4567-901234567890",
  "session_key": "d0e1f2a3-b4c5-6789-3456-890123456789",
  "items": [
    {
      "id": "f2a3b4c5-d6e7-8901-5678-012345678901",
      "variant": "a7b8c9d0-e1f2-3456-0123-567890123456",
      "variant_sku": "CWT-M-WHT",
      "product_name": "Classic White Tee",
      "variant_label": "M / White / Cotton",
      "unit_price": "490.00",
      "quantity": 2,
      "subtotal": "980.00",
      "image_url": "https://res.cloudinary.com/demo/image/upload/tee_front.jpg"
    }
  ],
  "total": "980.00",
  "item_count": 1
}
```

**Errors:**
- `404` — no cart found (guest without a session key)

---

## POST `/api/v1/sales/cart/items/`

Add an item to the cart, or increase quantity if the variant already exists.

**Auth required:** No (guest: `X-Cart-Session` header | logged-in: Customer JWT)

**Request Body:**
```json
{
  "variant": "a7b8c9d0-e1f2-3456-0123-567890123456",
  "quantity": 2
}
```

**Response `201`** (new item) or **`200`** (quantity updated):
```json
{
  "id": "f2a3b4c5-d6e7-8901-5678-012345678901",
  "variant": "a7b8c9d0-e1f2-3456-0123-567890123456",
  "variant_sku": "CWT-M-WHT",
  "product_name": "Classic White Tee",
  "variant_label": "M / White / Cotton",
  "unit_price": "490.00",
  "quantity": 2,
  "subtotal": "980.00",
  "image_url": "https://res.cloudinary.com/demo/image/upload/tee_front.jpg"
}
```

**Errors:**
- `400` — variant inactive, out of stock, or requested quantity exceeds available stock

---

## PATCH `/api/v1/sales/cart/items/{id}/`

Update the quantity of a cart item.

**Auth required:** No (guest: `X-Cart-Session` | logged-in: Customer JWT)

**Request Body:**
```json
{
  "quantity": 3
}
```

**Response `200`:** Updated cart item object

**Errors:**
- `400` — quantity exceeds available stock
- `404` — item not found in this cart

---

## DELETE `/api/v1/sales/cart/items/{id}/`

Remove an item from the cart.

**Auth required:** No (guest: `X-Cart-Session` | logged-in: Customer JWT)

**Response `204`:** _(no body)_

---

## POST `/api/v1/sales/cart/merge/`

After a guest logs in, merge their guest cart into their customer cart.

**Auth required:** Customer JWT

**Request Body:**
```json
{
  "session_key": "d0e1f2a3-b4c5-6789-3456-890123456789"
}
```

**Response `200`:** Full merged cart object (same shape as `GET /cart/`)

**Errors:**
- `400` — session_key missing
- `404` — guest cart not found

---

## POST `/api/v1/sales/checkout/apply-coupon/`

Validate a coupon code and get the discount amount before placing an order.

**Auth required:** No

**Request Body:**
```json
{
  "code": "SUMMER20",
  "subtotal": "1500.00"
}
```

**Response `200`:**
```json
{
  "code": "SUMMER20",
  "discount_type": "percent",
  "discount_value": "20.00",
  "discount_amount": "300.00"
}
```

**Errors:**
- `400` — invalid code, expired, usage limit reached, or subtotal below minimum order value

---

## POST `/api/v1/sales/checkout/`

Place an order. Atomically validates stock, decrements inventory, creates billing snapshot, and places the order. A payment record is created automatically.

**Auth required:** No (guest: `X-Cart-Session` header | logged-in: Customer JWT)

**Request Body:**
```json
{
  "billing_info": {
    "full_name": "Aisha Rahman",
    "phone": "01712345678",
    "email": "aisha@example.com",
    "address_line_1": "12/A Mirpur Road",
    "address_line_2": "Flat 3B",
    "city": "Dhaka",
    "district": "Dhaka",
    "postal_code": "1216",
    "delivery_instructions": "Please call before arriving."
  },
  "payment_method": "bkash",
  "coupon_code": "SUMMER20",
  "shipping_cost": "60.00"
}
```

> `payment_method` choices: `cod` | `bkash` | `nagad`  
> `coupon_code` is optional  
> `shipping_cost` defaults to `0` if omitted

**Response `201`:**
```json
{
  "id": "a3b4c5d6-e7f8-9012-6789-123456789012",
  "order_number": "KAP-00042",
  "status": "pending",
  "payment_status": "unpaid",
  "subtotal": "1500.00",
  "discount_amount": "300.00",
  "shipping_cost": "60.00",
  "total": "1260.00",
  "billing_info": {
    "full_name": "Aisha Rahman",
    "phone": "01712345678",
    "email": "aisha@example.com",
    "address_line_1": "12/A Mirpur Road",
    "address_line_2": "Flat 3B",
    "city": "Dhaka",
    "district": "Dhaka",
    "postal_code": "1216",
    "delivery_instructions": "Please call before arriving."
  },
  "items": [
    {
      "id": "b4c5d6e7-f8a9-0123-7890-234567890123",
      "product_name": "Classic White Tee",
      "sku": "CWT-M-WHT",
      "variant_label": "M / White / Cotton",
      "unit_price": "490.00",
      "quantity": 2,
      "total_price": "980.00"
    }
  ],
  "status_logs": [],
  "placed_at": "2025-03-01T14:30:00Z"
}
```

**Errors:**
- `400` — cart empty, insufficient stock for any item, invalid coupon

---

## GET `/api/v1/sales/orders/`

List order history for the authenticated customer.

**Auth required:** Customer JWT

**Response `200`:** Paginated list:
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "a3b4c5d6-e7f8-9012-6789-123456789012",
      "order_number": "KAP-00042",
      "status": "shipped",
      "payment_status": "paid",
      "total": "1260.00",
      "placed_at": "2025-03-01T14:30:00Z"
    }
  ]
}
```

---

## GET `/api/v1/sales/orders/{order_number}/`

Get full order detail for the authenticated customer.

**Auth required:** Customer JWT

**Response `200`:** Full order object (same shape as checkout response, with populated `status_logs`)

```json
{
  "id": "a3b4c5d6-e7f8-9012-6789-123456789012",
  "order_number": "KAP-00042",
  "status": "shipped",
  "payment_status": "paid",
  "subtotal": "1500.00",
  "discount_amount": "300.00",
  "shipping_cost": "60.00",
  "total": "1260.00",
  "billing_info": { "..." : "..." },
  "items": [ { "..." : "..." } ],
  "status_logs": [
    {
      "from_status": "pending",
      "to_status": "confirmed",
      "changed_by": "Rafi Admin",
      "note": "Order verified.",
      "timestamp": "2025-03-01T15:00:00Z"
    }
  ],
  "placed_at": "2025-03-01T14:30:00Z"
}
```

**Errors:**
- `404` — order not found or does not belong to this customer

---

## POST `/api/v1/sales/orders/track/`

Track an order as a guest using order number + phone. No authentication required.

**Auth required:** No

**Request Body:**
```json
{
  "order_number": "KAP-00042",
  "phone": "01712345678"
}
```

**Response `200`:** Full order object (same shape as authenticated detail view)

**Errors:**
- `404` — no order found matching order_number + phone combination

---

## GET `/api/v1/sales/admin/orders/`

List all orders with optional filters. Paginated.

**Auth required:** Admin JWT

**Query Parameters:**

| Param | Type | Description |
|---|---|---|
| `status` | string | `pending` \| `confirmed` \| `processing` \| `shipped` \| `delivered` \| `cancelled` \| `refunded` |
| `payment_status` | string | `unpaid` \| `paid` \| `partially_refunded` \| `refunded` |
| `date_from` | `YYYY-MM-DD` | Filter orders placed from this date |
| `date_to` | `YYYY-MM-DD` | Filter orders placed up to this date |
| `search` | string | Search by order number or billing phone |

**Response `200`:** Paginated lightweight order list

---

## GET `/api/v1/sales/admin/orders/{id}/`

Get full order detail by UUID (admin view).

**Auth required:** Admin JWT

**Response `200`:** Full order object including customer info

---

## PATCH `/api/v1/sales/admin/orders/{id}/status/`

Update an order's status. Creates a status log entry. If status is set to `delivered` and the payment method is COD, the payment is automatically verified.

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "status": "shipped",
  "note": "Handed to courier - Pathao"
}
```

> `status` choices: `pending` | `confirmed` | `processing` | `shipped` | `delivered` | `cancelled` | `refunded`

**Response `200`:** Updated full order object

**Errors:**
- `400` — status is unchanged
- `404` — order not found

---

## GET `/api/v1/sales/admin/coupons/`

List all coupons.

**Auth required:** Admin JWT

**Response `200`:**
```json
[
  {
    "id": "c5d6e7f8-a9b0-1234-8901-345678901234",
    "code": "SUMMER20",
    "discount_type": "percent",
    "discount_value": "20.00",
    "min_order_value": "500.00",
    "max_uses": 100,
    "used_count": 14,
    "valid_from": "2025-06-01T00:00:00Z",
    "valid_until": "2025-08-31T23:59:59Z",
    "is_active": true
  }
]
```

---

## POST `/api/v1/sales/admin/coupons/`

Create a new coupon.

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "code": "EID50",
  "discount_type": "flat",
  "discount_value": "50.00",
  "min_order_value": "300.00",
  "max_uses": 200,
  "valid_from": "2025-03-28T00:00:00Z",
  "valid_until": "2025-04-05T23:59:59Z",
  "is_active": true
}
```

> `discount_type` choices: `flat` | `percent`

**Response `201`:** Full coupon object

---

## PATCH `/api/v1/sales/admin/coupons/{id}/`

Update a coupon (e.g., deactivate or extend validity).

**Auth required:** Admin JWT

**Request Body** _(all fields optional)_:
```json
{
  "is_active": false
}
```

**Response `200`:** Updated coupon object

---

---

# 4. Finance

**Base path:** `/api/v1/finance/`

---

## GET `/api/v1/finance/payments/{order_number}/`

Get the payment status for an order.

**Auth required:** No

**Response `200`:**
```json
{
  "id": "d6e7f8a9-b0c1-2345-9012-456789012345",
  "order_number": "KAP-00042",
  "method": "bkash",
  "amount": "1260.00",
  "status": "pending",
  "transaction_id": "",
  "sender_number": "",
  "payment_screenshot_url": "",
  "submitted_at": null,
  "verified_at": null,
  "admin_note": "",
  "created_at": "2025-03-01T14:30:00Z"
}
```

> `status` values: `pending` | `submitted` | `verified` | `rejected`

**Errors:**
- `404` — payment not found

---

## POST `/api/v1/finance/payments/{order_number}/submit/`

Customer submits bKash or Nagad payment proof after sending money. Not applicable for COD.

If previously rejected, the customer can resubmit with corrected details.

**Auth required:** No

**Request Body:**
```json
{
  "transaction_id": "BK24FEB9A7B3C",
  "sender_number": "01811223344",
  "payment_screenshot_url": "https://res.cloudinary.com/demo/image/upload/receipt.jpg"
}
```

**Response `200`:** Updated payment object with `status: "submitted"`

**Errors:**
- `400` — payment already verified, already submitted (awaiting admin), or COD order (no action needed)
- `404` — payment not found

---

## GET `/api/v1/finance/admin/payments/`

List all payments with optional filters. Paginated.

**Auth required:** Admin JWT

**Query Parameters:**

| Param | Type | Description |
|---|---|---|
| `status` | string | `pending` \| `submitted` \| `verified` \| `rejected` |
| `method` | string | `cod` \| `bkash` \| `nagad` |
| `date` | `YYYY-MM-DD` | Filter by creation date |

**Response `200`:** Paginated list of admin payment objects:
```json
{
  "count": 30,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "d6e7f8a9-b0c1-2345-9012-456789012345",
      "order_number": "KAP-00042",
      "billing_name": "Aisha Rahman",
      "billing_phone": "01712345678",
      "method": "bkash",
      "amount": "1260.00",
      "status": "submitted",
      "transaction_id": "BK24FEB9A7B3C",
      "sender_number": "01811223344",
      "payment_screenshot_url": "https://res.cloudinary.com/demo/image/upload/receipt.jpg",
      "submitted_at": "2025-03-01T15:00:00Z",
      "verified_at": null,
      "verified_by": null,
      "admin_note": "",
      "created_at": "2025-03-01T14:30:00Z"
    }
  ]
}
```

---

## GET `/api/v1/finance/admin/payments/{id}/`

Get full payment detail by UUID.

**Auth required:** Admin JWT

**Response `200`:** Single admin payment object (same shape as list item above)

---

## PATCH `/api/v1/finance/admin/payments/{id}/verify/`

Mark a payment as verified. Updates the order's `payment_status` to `paid`.

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "admin_note": "Confirmed in bKash merchant portal."
}
```

> `admin_note` is optional

**Response `200`:** Updated payment object

**Errors:**
- `400` — payment already verified
- `404` — payment not found

---

## PATCH `/api/v1/finance/admin/payments/{id}/reject/`

Reject a payment submission. The customer can resubmit with corrected details.

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "admin_note": "TrxID not found in bKash portal. Please resubmit with the correct ID."
}
```

> `admin_note` is **required** for rejections

**Response `200`:** Updated payment object with `status: "rejected"`

**Errors:**
- `400` — cannot reject a verified payment
- `404` — payment not found

---

## GET `/api/v1/finance/admin/refunds/`

List all refund requests. Paginated.

**Auth required:** Admin JWT

**Response `200`:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "e7f8a9b0-c1d2-3456-0123-567890123456",
      "order_number": "KAP-00037",
      "payment": "d6e7f8a9-b0c1-2345-9012-456789012345",
      "amount": "980.00",
      "method": "bkash",
      "recipient_number": "01712345678",
      "reason": "Customer received wrong size.",
      "status": "pending",
      "proof_url": "",
      "requested_at": "2025-03-02T09:00:00Z",
      "processed_at": null,
      "processed_by": null
    }
  ]
}
```

---

## POST `/api/v1/finance/admin/refunds/`

Create a new refund request for an order.

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "payment": "d6e7f8a9-b0c1-2345-9012-456789012345",
  "order": "a3b4c5d6-e7f8-9012-6789-123456789012",
  "amount": "980.00",
  "method": "bkash",
  "recipient_number": "01712345678",
  "reason": "Customer received wrong size."
}
```

> `method` choices: `bkash` | `nagad` | `cash`

**Response `201`:** Refund object

**Errors:**
- `400` — payment doesn't belong to this order, or refund amount exceeds payment amount

---

## PATCH `/api/v1/finance/admin/refunds/{id}/`

Update refund status. When status is set to `processed`, stock is restored, the order status becomes `refunded`, and `processed_at` / `processed_by` are recorded.

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "status": "processed",
  "proof_url": "https://res.cloudinary.com/demo/image/upload/refund_proof.jpg"
}
```

> `status` choices: `pending` | `approved` | `processed` | `rejected`  
> `proof_url` is optional

**Response `200`:** Updated refund object

---

## GET `/api/v1/finance/admin/expense-categories/`

List all expense categories.

**Auth required:** Admin JWT

**Response `200`:**
```json
[
  {
    "id": "f8a9b0c1-d2e3-4567-1234-678901234567",
    "name": "Delivery",
    "description": "Courier and shipping expenses"
  }
]
```

---

## POST `/api/v1/finance/admin/expense-categories/`

Create a new expense category.

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "name": "Packaging",
  "description": "Boxes, bubble wrap, tape, etc."
}
```

**Response `201`:** Expense category object

---

## GET `/api/v1/finance/admin/expenses/`

List all expenses with optional filters. Paginated.

**Auth required:** Admin JWT

**Query Parameters:**

| Param | Type | Description |
|---|---|---|
| `category` | UUID | Filter by expense category ID |
| `date_from` | `YYYY-MM-DD` | Filter expenses from this date |
| `date_to` | `YYYY-MM-DD` | Filter expenses up to this date |

**Response `200`:**
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "a9b0c1d2-e3f4-5678-2345-789012345678",
      "category": "f8a9b0c1-d2e3-4567-1234-678901234567",
      "category_name": "Delivery",
      "title": "Pathao bulk shipment",
      "description": "March 1st batch",
      "amount": "3500.00",
      "receipt_url": "https://res.cloudinary.com/demo/image/upload/receipt.jpg",
      "incurred_on": "2025-03-01",
      "recorded_by": "Rafi Admin",
      "created_at": "2025-03-01T16:00:00Z"
    }
  ]
}
```

---

## POST `/api/v1/finance/admin/expenses/`

Record a new expense.

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "category": "f8a9b0c1-d2e3-4567-1234-678901234567",
  "title": "Pathao bulk shipment",
  "description": "March 1st batch",
  "amount": "3500.00",
  "receipt_url": "https://res.cloudinary.com/demo/image/upload/receipt.jpg",
  "incurred_on": "2025-03-01"
}
```

**Response `201`:** Expense object

---

## PATCH `/api/v1/finance/admin/expenses/{id}/`

Update an existing expense record.

**Auth required:** Admin JWT

**Request Body** _(all fields optional)_:
```json
{
  "amount": "3800.00",
  "description": "Updated amount after recount."
}
```

**Response `200`:** Updated expense object

---

---

# 5. Admin Panel

**Base path:** `/api/v1/admin/`

---

## POST `/api/v1/admin/auth/login/`

Log in as an admin user.

**Auth required:** No

**Request Body:**
```json
{
  "email": "rafi@kapore.com",
  "password": "adminpass123"
}
```

**Response `200`:**
```json
{
  "admin": {
    "id": "b0c1d2e3-f4a5-6789-3456-890123456789",
    "email": "rafi@kapore.com",
    "full_name": "Rafi Hossain",
    "role": "superadmin",
    "is_active": true,
    "last_login": "2025-03-01T10:00:00Z",
    "created_at": "2024-12-01T08:00:00Z"
  },
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

> `role` values: `superadmin` | `manager` | `staff`

**Errors:**
- `401` — invalid credentials or inactive account

---

## POST `/api/v1/admin/auth/logout/`

Log out the admin (client discards tokens).

**Auth required:** Admin JWT

**Response `200`:**
```json
{
  "detail": "Logged out."
}
```

---

## POST `/api/v1/admin/auth/refresh/`

Refresh an admin access token.

**Auth required:** No

**Request Body:**
```json
{
  "refresh": "<refresh_token>"
}
```

**Response `200`:**
```json
{
  "access": "<new_access_token>"
}
```

**Errors:**
- `401` — invalid, expired, or non-admin token

---

## GET `/api/v1/admin/me/`

Get the current admin user's profile.

**Auth required:** Admin JWT

**Response `200`:**
```json
{
  "id": "b0c1d2e3-f4a5-6789-3456-890123456789",
  "email": "rafi@kapore.com",
  "full_name": "Rafi Hossain",
  "role": "superadmin",
  "is_active": true,
  "last_login": "2025-03-01T10:00:00Z",
  "created_at": "2024-12-01T08:00:00Z"
}
```

---

## PATCH `/api/v1/admin/me/`

Update own profile. Staff-role users cannot change their own role.

**Auth required:** Admin JWT

**Request Body** _(all fields optional)_:
```json
{
  "full_name": "Rafi H."
}
```

**Response `200`:** Updated admin user object

---

## GET `/api/v1/admin/users/`

List all admin users.

**Auth required:** Admin JWT (superadmin only)

**Response `200`:**
```json
[
  {
    "id": "b0c1d2e3-f4a5-6789-3456-890123456789",
    "email": "rafi@kapore.com",
    "full_name": "Rafi Hossain",
    "role": "superadmin",
    "is_active": true,
    "last_login": "2025-03-01T10:00:00Z",
    "created_at": "2024-12-01T08:00:00Z"
  }
]
```

---

## POST `/api/v1/admin/users/`

Create a new admin user.

**Auth required:** Admin JWT (superadmin only)

**Request Body:**
```json
{
  "email": "nadia@kapore.com",
  "full_name": "Nadia Islam",
  "role": "staff",
  "password": "staffpass456"
}
```

**Response `201`:** New admin user object

---

## PATCH `/api/v1/admin/users/{id}/`

Update an admin user (role, active status, name).

**Auth required:** Admin JWT (superadmin only)

**Request Body** _(all fields optional)_:
```json
{
  "role": "manager",
  "is_active": false
}
```

**Response `200`:** Updated admin user object

---

## GET `/api/v1/admin/activity-logs/`

Get paginated activity logs for all admin actions.

**Auth required:** Admin JWT

**Response `200`:**
```json
{
  "count": 200,
  "next": "https://kaporebackend.com/api/v1/admin/activity-logs/?page=2",
  "previous": null,
  "results": [
    {
      "id": "c1d2e3f4-a5b6-7890-4567-901234567890",
      "admin_name": "Rafi Hossain",
      "action": "Updated order KAP-00042 to shipped",
      "ip_address": "103.123.45.67",
      "timestamp": "2025-03-01T15:00:00Z"
    }
  ]
}
```

---

---

# 6. Accounting

**Base path:** `/api/v1/accounting/`

All accounting endpoints are restricted to admin users.

---

## GET `/api/v1/accounting/accounts/`

List all root accounts in the chart of accounts (with nested children).

**Auth required:** Admin JWT

**Response `200`:**
```json
[
  {
    "id": "d2e3f4a5-b6c7-8901-5678-012345678901",
    "code": "1000",
    "name": "Cash",
    "account_type": "asset",
    "parent": null,
    "description": "",
    "is_active": true,
    "children": []
  },
  {
    "id": "e3f4a5b6-c7d8-9012-6789-123456789012",
    "code": "4000",
    "name": "Sales Revenue",
    "account_type": "revenue",
    "parent": null,
    "description": "",
    "is_active": true,
    "children": []
  }
]
```

> `account_type` values: `asset` | `liability` | `equity` | `revenue` | `expense`

---

## POST `/api/v1/accounting/accounts/`

Add a new account to the chart of accounts.

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "code": "5800",
  "name": "Platform Fees",
  "account_type": "expense",
  "parent": null,
  "description": "Fees charged by e-commerce platforms",
  "is_active": true
}
```

**Response `201`:** Full account object

**Errors:**
- `400` — account code already exists

---

## PATCH `/api/v1/accounting/accounts/{id}/`

Update an account.

**Auth required:** Admin JWT

**Request Body** _(all fields optional)_:
```json
{
  "description": "Updated description.",
  "is_active": false
}
```

**Response `200`:** Updated account object

---

## GET `/api/v1/accounting/journal-entries/`

List journal entries with optional filters. Paginated.

**Auth required:** Admin JWT

**Query Parameters:**

| Param | Type | Description |
|---|---|---|
| `is_posted` | `true` \| `false` | Filter by posted status |
| `date_from` | `YYYY-MM-DD` | Filter entries from this date |
| `date_to` | `YYYY-MM-DD` | Filter entries up to this date |

**Response `200`:**
```json
{
  "count": 85,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "f4a5b6c7-d8e9-0123-7890-234567890123",
      "reference_number": "JE-00001",
      "description": "Sales revenue — Order KAP-00042",
      "entry_date": "2025-03-01",
      "created_by": "System",
      "is_posted": true,
      "created_at": "2025-03-01T14:30:00Z"
    }
  ]
}
```

---

## POST `/api/v1/accounting/journal-entries/`

Create a new manual journal entry (saved as a draft — must be explicitly posted).

**Auth required:** Admin JWT

**Request Body:**
```json
{
  "description": "Manual adjustment — packaging materials",
  "entry_date": "2025-03-01",
  "lines": [
    {
      "account": "d2e3f4a5-b6c7-8901-5678-012345678901",
      "debit": "0.00",
      "credit": "500.00",
      "note": "Cash paid"
    },
    {
      "account": "a5b6c7d8-e9f0-1234-8901-345678901234",
      "debit": "500.00",
      "credit": "0.00",
      "note": "Packaging expense"
    }
  ]
}
```

> The entry must be **balanced**: total debits must equal total credits.  
> Each line must have either a debit **or** credit (not both, not neither).  
> Minimum 2 lines required.

**Response `201`:**
```json
{
  "id": "a5b6c7d8-e9f0-1234-8901-345678901234",
  "reference_number": "JE-00086",
  "description": "Manual adjustment — packaging materials",
  "entry_date": "2025-03-01",
  "created_by": "Rafi Hossain",
  "is_posted": false,
  "is_balanced": true,
  "lines": [
    {
      "id": "b6c7d8e9-f0a1-2345-9012-456789012345",
      "account": "d2e3f4a5-b6c7-8901-5678-012345678901",
      "account_code": "1000",
      "account_name": "Cash",
      "debit": "0.00",
      "credit": "500.00",
      "note": "Cash paid"
    },
    {
      "id": "c7d8e9f0-a1b2-3456-0123-567890123456",
      "account": "a5b6c7d8-e9f0-1234-8901-345678901234",
      "account_code": "5100",
      "account_name": "Packaging Expense",
      "debit": "500.00",
      "credit": "0.00",
      "note": "Packaging expense"
    }
  ],
  "created_at": "2025-03-01T16:00:00Z"
}
```

**Errors:**
- `400` — entry is unbalanced, invalid account IDs, or line validation failure

---

## GET `/api/v1/accounting/journal-entries/{id}/`

Get full journal entry detail including all lines.

**Auth required:** Admin JWT

**Response `200`:** Full journal entry object (same shape as create response)

---

## PATCH `/api/v1/accounting/journal-entries/{id}/post/`

Post a draft journal entry. This action is **irreversible** — posted entries cannot be edited.

**Auth required:** Admin JWT

**Request Body:** _(empty)_

**Response `200`:** Updated journal entry with `is_posted: true`

**Errors:**
- `400` — entry is already posted, or entry is unbalanced

---

## GET `/api/v1/accounting/reports/balance-sheet/`

Generate a balance sheet as of a given date.

**Auth required:** Admin JWT

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `date` | `YYYY-MM-DD` | today | Balance sheet as of this date |

**Example:** `GET /api/v1/accounting/reports/balance-sheet/?date=2025-03-01`

**Response `200`:**
```json
{
  "as_of": "2025-03-01",
  "assets": {
    "accounts": [
      { "code": "1000", "name": "Cash", "debit": "50000.00", "credit": "12000.00", "balance": "38000.00" },
      { "code": "1010", "name": "bKash Wallet", "debit": "25000.00", "credit": "5000.00", "balance": "20000.00" },
      { "code": "1100", "name": "Accounts Receivable", "debit": "8000.00", "credit": "8000.00", "balance": "0.00" }
    ],
    "total": "58000.00"
  },
  "liabilities": {
    "accounts": [
      { "code": "2000", "name": "Accounts Payable", "debit": "0.00", "credit": "3000.00", "balance": "3000.00" }
    ],
    "total": "3000.00"
  },
  "equity": {
    "accounts": [
      { "code": "3000", "name": "Owner's Equity", "debit": "0.00", "credit": "45000.00", "balance": "45000.00" },
      { "code": "3100", "name": "Retained Earnings", "debit": "0.00", "credit": "10000.00", "balance": "10000.00" }
    ],
    "total": "55000.00"
  },
  "liabilities_and_equity": "58000.00",
  "balanced": true
}
```

**Errors:**
- `400` — invalid date format

---

## GET `/api/v1/accounting/reports/profit-loss/`

Generate a profit and loss report for a date range.

**Auth required:** Admin JWT

**Query Parameters:**

| Param | Type | Required | Description |
|---|---|---|---|
| `from` | `YYYY-MM-DD` | **Yes** | Start of period |
| `to` | `YYYY-MM-DD` | No (defaults to today) | End of period |

**Example:** `GET /api/v1/accounting/reports/profit-loss/?from=2025-03-01&to=2025-03-31`

**Response `200`:**
```json
{
  "from": "2025-03-01",
  "to": "2025-03-31",
  "revenue": {
    "accounts": [
      { "code": "4000", "name": "Sales Revenue", "debit": "0.00", "credit": "180000.00", "balance": "180000.00" },
      { "code": "4100", "name": "Shipping Income", "debit": "0.00", "credit": "4200.00", "balance": "4200.00" }
    ],
    "total": "184200.00"
  },
  "expenses": {
    "accounts": [
      { "code": "5000", "name": "Cost of Goods Sold", "debit": "90000.00", "credit": "0.00", "balance": "90000.00" },
      { "code": "5200", "name": "Delivery Expense", "debit": "8500.00", "credit": "0.00", "balance": "8500.00" },
      { "code": "5300", "name": "Marketing Expense", "debit": "5000.00", "credit": "0.00", "balance": "5000.00" }
    ],
    "total": "103500.00"
  },
  "net_profit": "80700.00",
  "profitable": true
}
```

**Errors:**
- `400` — missing `from` param, invalid date format, or `from` is after `to`

---

## GET `/api/v1/accounting/reports/trial-balance/`

Generate a trial balance to verify that books are balanced.

**Auth required:** Admin JWT

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `date` | `YYYY-MM-DD` | today | Trial balance as of this date |

**Example:** `GET /api/v1/accounting/reports/trial-balance/?date=2025-03-31`

**Response `200`:**
```json
{
  "as_of": "2025-03-31",
  "accounts": [
    { "code": "1000", "name": "Cash",           "account_type": "asset",   "debit": "50000.00", "credit": "12000.00" },
    { "code": "4000", "name": "Sales Revenue",  "account_type": "revenue", "debit": "0.00",     "credit": "180000.00" },
    { "code": "5000", "name": "Cost of Goods",  "account_type": "expense", "debit": "90000.00", "credit": "0.00" }
  ],
  "total_debit": "192000.00",
  "total_credit": "192000.00",
  "balanced": true
}
```

**Errors:**
- `400` — invalid date format

---

---

## Default Chart of Accounts

The following accounts are seeded by default via `python manage.py seedaccounts`:

| Code | Name | Type |
|---|---|---|
| 1000 | Cash | Asset |
| 1010 | bKash Wallet | Asset |
| 1020 | Nagad Wallet | Asset |
| 1100 | Accounts Receivable | Asset |
| 1200 | Inventory | Asset |
| 1300 | Prepaid Expenses | Asset |
| 2000 | Accounts Payable | Liability |
| 2100 | Customer Refunds Payable | Liability |
| 2200 | Unearned Revenue | Liability |
| 3000 | Owner's Equity | Equity |
| 3100 | Retained Earnings | Equity |
| 4000 | Sales Revenue | Revenue |
| 4100 | Shipping Income | Revenue |
| 5000 | Cost of Goods Sold | Expense |
| 5100 | Packaging Expense | Expense |
| 5200 | Delivery Expense | Expense |
| 5300 | Marketing Expense | Expense |
| 5400 | Miscellaneous Expense | Expense |
| 5500 | Transaction Charges | Expense |
| 5600 | Bad Debt Expense | Expense |
| 5700 | Food Expense | Expense |

---

## Signal-Driven Journal Entries (Auto-generated)

The following events automatically generate posted journal entries:

| Event | Accounts Affected |
|---|---|
| Order placed | DR Accounts Receivable / CR Sales Revenue + Shipping Income |
| Payment verified (bKash/Nagad) | DR bKash/Nagad Wallet / CR Accounts Receivable |
| COD delivered | DR Cash / CR Accounts Receivable |
| Refund processed | Reverse of payment entry |
| Expense recorded | DR Expense Account / CR Cash or Payable |

---

## Order Status Flow

```
pending → confirmed → processing → shipped → delivered
                                           ↘ cancelled
                                  → refunded
```

## Payment Status Flow

```
COD:          pending → verified (auto when order = delivered)
bKash/Nagad:  pending → submitted → verified
                                  → rejected → (customer resubmits) → submitted
```