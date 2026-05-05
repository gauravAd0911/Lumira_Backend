# Backend Features, Logic, Frontend Contracts, and Status

## Overview
This document summarizes the backend microservices for the Lumira Skin ecommerce platform. It describes each service's purpose, core logic, frontend API contract, response format, and implementation status.

The backend is organized as 11 microservices, each responsible for one domain:
- Authentication Service
- Product Catalog Service
- Shopping Cart Service
- Checkout Service
- Inventory Service
- Payment Service
- Order Management Service
- Review Service
- Profile Service
- Support Service
- Notification Service

Each service returns JSON in a standard envelope format when implemented correctly:
```json
{
  "success": true,
  "message": "Human-readable message",
  "data": { ... },
  "error": null
}
```

Error responses follow:
```json
{
  "success": false,
  "message": "Error message",
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Detailed error message",
    "details": []
  }
}
```

---

## Service Summary and Status

| Service | Folder | Purpose | Status |
|---|---|---|---|
| Authentication | `user_profile_service` / `Auther_M2/Auther_M` (alternate) | Register, login, OTP, token refresh, user auth | ✅ Implemented |
| Product Catalog | `catalog_services` | Products, categories, home content, admin product management | ✅ Implemented |
| Shopping Cart | `ecommerce_cart` | Cart operations, guest merge, pricing | ✅ Implemented |
| Checkout | `checkout_system` | Guest checkout, verification, delivery, checkout validation | ✅ Implemented |
| Inventory | `Inventory_services` | Stock validation, reservation, release, commit | ✅ Implemented |
| Payment | `payment_app` | Razorpay order creation, verification, webhooks | ✅ Implemented |
| Order Management | `order_services` | Order create, list, detail, tracking, status updates | ✅ Implemented |
| Review | `review_services` | Reviews, ratings, eligibility, listing | ✅ Implemented |
| Profile | `user_profile_service` | User profile, addresses, update profile | ✅ Implemented |
| Support | `support_service` | Support queries, admin ticket updates | ⚠️ Partial |
| Notification | `notification_service` | Push registration, in-app notifications, SMS, email, WhatsApp | ✅ Implemented |

---

## 1. Authentication Service
**Folder:** `e:\Learning Projects\Lumia_Backend_updated\user_profile_service` (or alternate `Auther_M2/Auther_M`)

### Purpose
Handles user registration, login, JWT issuance, refresh tokens, password reset, and employee management.

### Logic
- User credentials stored with secure password hashing
- JWT tokens issued for authenticated sessions
- Refresh tokens used to renew access tokens
- OTP flows support password recovery and verification
- `X-User-Id` or JWT-based auth is used for downstream services

### Frontend Contract
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/password/forgot`
- `POST /auth/password/verify-otp`
- `POST /auth/password/reset`
- Admin endpoints: `GET/POST/PUT/DELETE /auth/employees`

### Response Example
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "tokens": {
      "access_token": "...",
      "refresh_token": "...",
      "token_type": "bearer"
    },
    "user": {
      "id": "user-123",
      "email": "user@example.com",
      "fullName": "John Doe",
      "role": "customer",
      "isEmailVerified": true,
      "isPhoneVerified": false
    }
  },
  "error": null
}
```

### Status
✅ **Implemented**

---

## 2. Product Catalog Service
**Folder:** `e:\Learning Projects\Lumia_Backend_updated\catalog_services`

### Purpose
Manages product listing, search, categories, filters, and admin product CRUD.

### Logic
- Supports filtering by text, category, price range, skin type, and sort order
- Returns featured products for homepage
- Includes product metadata: ingredients, benefits, usage, stock, and status
- Provides admin endpoints to create, update, and delete products

### Frontend Contract
- `GET /api/v1/home`
- `GET /api/v1/products`
- `GET /api/v1/products/{product_id}`
- `GET /api/v1/categories`
- `GET /api/v1/products/{product_id}/related`
- Admin endpoints: `POST/PUT/DELETE /api/v1/admin/products/{product_id}`

### Response Example
```json
{
  "success": true,
  "message": "Products retrieved successfully",
  "data": {
    "products": [ ... ],
    "categories": ["Serums", "Moisturizers"]
  },
  "error": null
}
```

### Status
✅ **Implemented**

---

## 3. Shopping Cart Service
**Folder:** `e:\Learning Projects\Lumia_Backend_updated\ecommerce_cart`

### Purpose
Handles cart item management, quantities, guest cart merge, and cart totals.

### Logic
- Stores cart items per user or guest token
- Calculates subtotal, discount, shipping, tax, and total
- Supports merging guest cart into authenticated user cart
- Validates stock before update operations

### Frontend Contract
- `GET /api/v1/cart`
- `POST /api/v1/cart/items`
- `PATCH /api/v1/cart/items/{product_id}`
- `DELETE /api/v1/cart/items/{product_id}`
- `DELETE /api/v1/cart`
- `POST /api/v1/cart/merge`

### Response Example
```json
{
  "success": true,
  "message": "Cart retrieved successfully",
  "data": {
    "items": [ ... ],
    "pricing": {
      "subtotal": 2400,
      "discount": 0,
      "shipping": 100,
      "tax": 240,
      "total": 2740
    }
  },
  "error": null
}
```

### Status
✅ **Implemented**

---

## 4. Checkout Service
**Folder:** `e:\Learning Projects\Lumia_Backend_updated\checkout_system`

### Purpose
Handles guest checkout verification, delivery availability, guest session creation, and checkout validation.

### Logic
- Generates guest OTP verification for email/phone
- Issues guest tokens for guest checkout flows
- Validates delivery serviceability by pincode
- Computes shipping charges by zone and threshold
- Enforces data validation for checkout payloads

### Frontend Contract
- `POST /api/v1/guest-checkout/request-verification`
- `POST /api/v1/guest-checkout/verify`
- `POST /api/v1/guest-orders`
- `POST /api/v1/guest-orders/request-lookup`
- `POST /api/v1/guest-orders/verify-lookup`
- `POST /api/v1/checkout/validate`
- `POST /api/v1/checkout/session`

### Response Example
```json
{
  "success": true,
  "message": "Checkout session created",
  "data": {
    "guestToken": "guest-token-456",
    "expiresAt": "2024-01-01T10:30:00Z"
  },
  "error": null
}
```

### Status
✅ **Implemented**

---

## 5. Inventory Service
**Folder:** `e:\Learning Projects\Lumia_Backend_updated\Inventory_services`

### Purpose
Manages stock validation, inventory reservation, extensions, and release.

### Logic
- Validates available stock for requested items
- Creates reservations for checkout holds
- Commits or releases reservations based on order outcome
- Avoids overselling by tracking reserved quantities

### Frontend Contract
- `POST /api/v1/inventory/validate`
- `POST /api/v1/inventory/reservations`
- `DELETE /api/v1/inventory/reservations/{reservation_id}`
- `POST /api/v1/inventory/reservations/{reservation_id}/commit`

### Response Example
```json
{
  "success": true,
  "message": "Reservation created",
  "data": {
    "reservationId": "reserve-123",
    "expiresAt": "2024-01-01T10:45:00Z"
  },
  "error": null
}
```

### Status
✅ **Implemented**

---

## 6. Payment Service
**Folder:** `e:\Learning Projects\Lumia_Backend_updated\payment_app`

### Purpose
Processes Razorpay payments, verifies transactions, and handles webhooks.

### Logic
- Creates Razorpay orders and payment intents with idempotency
- Converts currency values correctly and returns gateway order IDs
- Verifies Razorpay signatures on payment confirmation
- Stores payment records in database
- Processes `payment.captured`, `order.paid`, and `payment.failed` webhooks
- Reconciles payment status when requested

### Frontend Contract
- `POST /api/v1/payments/orders`
- `POST /api/v1/payments/intent`
- `POST /api/v1/payments/verify`
- `GET /api/v1/payments/{payment_reference}/status`
- `POST /api/v1/payments/webhooks/razorpay`
- `POST /api/v1/payments/webhook/razorpay`

### Request Example for Intent
```json
{
  "amount": 2740,
  "orderReference": "order-ref-123",
  "methodLabel": "Razorpay",
  "reservationId": "reserve-123",
  "guestToken": "guest-token-456",
  "currency": "INR",
  "receipt": "receipt-123",
  "notes": {
    "userId": "user-456",
    "email": "john@example.com"
  }
}
```

### Response Example
```json
{
  "success": true,
  "message": "Payment intent created successfully.",
  "data": {
    "id": "order_xyz123",
    "amount": 2740,
    "provider": "razorpay",
    "status": "created",
    "gatewayOrderId": "order_xyz123",
    "currency": "INR"
  },
  "error": null
}
```

### Status
✅ **Implemented**

---

## 7. Order Management Service
**Folder:** `e:\Learning Projects\Lumia_Backend_updated\order_services`

### Purpose
Manages order lifecycle, order creation, listing, detail retrieval, tracking, and admin status updates.

### Logic
- Resolves authenticated users and guest users
- Normalizes frontend order payloads from multiple naming conventions
- Validates payment verification before order creation
- Tracks order status transitions with allowed state flow
- Supports admin/employee order list and status updates

### Frontend Contract
- `POST /api/v1/orders`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `GET /api/v1/orders/{order_id}/tracking`
- `PATCH /api/v1/orders/admin/{order_id}/status`
- `PATCH /api/v1/orders/admin/{order_id}/assign`

### Request Example
```json
{
  "userId": "user-456",
  "items": [ ... ],
  "summary": {
    "subtotal": 2400,
    "discount": 0,
    "shipping": 100,
    "tax": 240,
    "total": 2740
  },
  "shippingDetails": { ... },
  "paymentDetails": {
    "method": "razorpay",
    "transactionId": "pay_abc123"
  },
  "guestToken": "guest-token-456"
}
```

### Status
✅ **Implemented**

---

## 8. Review Service
**Folder:** `e:\Learning Projects\Lumia_Backend_updated\review_services`

### Purpose
Stores product reviews, calculates ratings, verifies review eligibility, and returns review lists.

### Logic
- Allows reviews only for authenticated users
- Checks buyer eligibility before accepting reviews
- Supports review listing by product
- Provides rating summary and pagination

### Frontend Contract
- `GET /api/v1/products/{product_id}/reviews`
- `POST /api/v1/products/{product_id}/reviews`
- `GET /api/v1/products/{product_id}/rating-summary`
- `GET /api/v1/reviews/eligibility/{product_id}`
- `GET /api/v1/users/me/reviews`
- `PATCH /api/v1/reviews/{review_id}`
- `GET /api/v1/reviews/{review_id}`

### Status
✅ **Implemented**

---

## 9. Profile Service
**Folder:** `e:\Learning Projects\Lumia_Backend_updated\user_profile_service`

### Purpose
Manages user profile and address book functionality.

### Logic
- Returns current user profile using authentication dependency
- Updates profile data via patch
- Stores multiple addresses per user with default address support
- Marks addresses as default and handles CRUD operations

### Frontend Contract
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `GET /api/v1/users/me/addresses`
- `POST /api/v1/users/me/addresses`
- `PATCH /api/v1/users/me/addresses/{address_id}`
- `DELETE /api/v1/users/me/addresses/{address_id}`
- `PATCH /api/v1/users/me/addresses/{address_id}/default`

### Status
✅ **Implemented**

---

## 10. Support Service
**Folder:** `e:\Learning Projects\Lumia_Backend_updated\support_service`

### Purpose
Handles customer support tickets and admin ticket management.

### Logic
- Creates support queries for users
- Lists support tickets for users and admins
- Updates ticket status
- Assigns tickets to employees

### Frontend Contract
- `GET /api/v1/support/queries`
- `POST /api/v1/support/queries`
- `GET /api/v1/admin/queries`
- `PATCH /api/v1/admin/queries/{ticket_id}`
- `GET /api/v1/admin/queries/{ticket_id}`

### Status
⚠️ **Partial**

### Notes
- Core query flow is implemented
- Support category options remain basic
- No advanced dynamic support metadata

---

## 11. Notification Service
**Folder:** `e:\Learning Projects\Lumia_Backend_updated\notification_service`

### Purpose
Delivers notifications via push, email, WhatsApp, and SMS.

### Logic
- Stores in-app notifications in the database
- Registers and removes device tokens for push notifications
- Sends SMS via Twilio
- Sends email via SMTP using HTML templates
- Sends WhatsApp messages via WhatsApp Business API

### Frontend Contract
- `POST /api/v1/notifications/devices/register`
- `DELETE /api/v1/notifications/devices/{device_id}`
- `POST /api/v1/notifications`
- `GET /api/v1/notifications?user_id={id}`
- `PATCH /api/v1/notifications/{id}/read`
- `POST /api/v1/notifications/email`
- `POST /api/v1/notifications/whatsapp`
- `POST /api/v1/notifications/sms`

### Status
✅ **Implemented**

### Implementation Details
- Email is handled by `app/services/email_service.py`
- WhatsApp is handled by `app/services/whatsapp_service.py`
- SMS remains handled by `app/services/twilio_service.py`
- Email templates live in `app/templates/email_templates.py`

### Notification Email Flow
1. Frontend or backend calls `/api/v1/notifications/email`
2. Service builds HTML/text using templates
3. SMTP sends the message
4. Returns success or error envelope

### WhatsApp Flow
1. Call `/api/v1/notifications/whatsapp`
2. Service sends the message via Meta WhatsApp Business API
3. Returns success or error envelope

---

## Deployment and Integration Notes

### Environment Variables
At minimum, production should define:
- `DATABASE_URL` or database connection settings
- `RAZORPAY_KEY_ID`
- `RAZORPAY_SECRET_KEY`
- `RAZORPAY_WEBHOOK_SECRET`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`

### Key Production Requirements
- HTTPS enabled for all services
- Valid JWT secrets and token expiration policies
- Razorpay webhooks registered correctly
- SMTP account configured for transactional email
- WhatsApp Business API approved and configured
- Redis caching recommended for session and product data
- Centralized logging for all services

---

## Status Summary

### Fully implemented and ready
- Authentication
- Product Catalog
- Shopping Cart
- Checkout
- Inventory
- Payment
- Order Management
- Review
- Profile
- Notification

### Partially implemented
- Support Service

### Needs improvement
- Support service should include dynamic categories and more advanced ticket metadata
- Notification service can be extended with actual push delivery (FCM/APNs) if required

---

## Conclusion
The backend architecture is largely complete and matches frontend expectations. The only feature area that is still partial is the support service, while notification service now supports the required email and WhatsApp channels.

Use this document as the single source of truth for backend feature coverage and frontend contract expectations.
