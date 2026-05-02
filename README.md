# Lumia Backend Updated

This repository contains the backend services for the Mahi/Lumia commerce app. The codebase is organized as independent FastAPI services, so each folder should be treated as a deployable microservice with its own API contract, database schema, dependencies, and runtime.

The backend source of truth is:

1. The FastAPI route files in each service.
2. The Pydantic request/response schemas beside those routes.
3. The SQL schema files in each service folder.
4. The generated OpenAPI pages exposed by each running service at `/docs` and `/openapi.json`.

The frontend should not treat local mock services as the final contract. Mock mode is useful for UI development only. Production should use backend-owned OTP, authentication, catalog, cart, checkout, inventory reservation, payment verification, orders, addresses, reviews, notifications, and support tickets.

## Architecture

The backend is split into these services:

| Service folder | Responsibility | Main API prefix |
| --- | --- | --- |
| `Auther_M2/Auther_M` | Customer signup, OTP verification, login, JWT refresh, logout, current user | `/api/v1/auth` |
| `catalog_services` | Home content, product catalog, categories, filters, product details | `/api/v1` |
| `ecommerce_cart` | Authenticated cart and simple product CRUD for cart product records | `/api/cart`, `/api/products` |
| `checkout_system` | Guest checkout OTP flow, guest orders, checkout validation/session | `/api/v1/guest-checkout`, `/api/v1/guest-orders`, `/api/v1/checkout` |
| `Inventory_services` | Stock validation, stock reservation, release, commit | `/api/v1/inventory` |
| `payment_app` | Razorpay order creation, mobile payment intent, verification, status, webhooks | `/api/v1/payments` |
| `order_services` | Authenticated order finalization, order listing/detail, tracking | `/api/v1/orders` |
| `review_services` | Product reviews, rating summary, review eligibility, user reviews | `/api/v1` |
| `user_profile_service` | Current user profile and address book | `/api/v1/users` |
| `support_service` | Support query submission and support options | `/api/v1/support` |
| `notification_service` | Device registration and user notification records | `/api/v1/notifications` |

## Recommended Source Of Truth Flow

For mobile/frontend integration, use backend OpenAPI contracts as the final source of truth:

1. Start the required service.
2. Open `http://localhost:<port>/docs`.
3. Confirm request and response schemas from Swagger/OpenAPI.
4. Update frontend service wrappers to match the backend route and payload exactly.
5. Keep `src/types/apiContracts.ts` aligned with backend Pydantic schemas.

For production-quality microservices, put an API Gateway or BFF in front of these services. The React Native app currently supports only:

```ts
AUTH_BASE_URL
PRODUCT_BASE_URL
```

That is enough for a prototype, but not enough for a clean microservice deployment. A gateway is the best source-of-truth boundary for the mobile app:

```text
React Native app
  -> API Gateway / BFF
      -> Auth Service
      -> Catalog Service
      -> Cart Service
      -> Checkout Service
      -> Inventory Service
      -> Payment Service
      -> Order Service
      -> Review Service
      -> Profile Service
      -> Support Service
      -> Notification Service
```

## Service Contracts

### Auth Service

Location: `Auther_M2/Auther_M`

Run from service folder:

```bash
uvicorn auth.main:app --reload --port 8001
```

Important endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/auth/signup/initiate` | Start signup and send OTP |
| `POST` | `/api/v1/auth/signup/verify-otp` | Verify signup OTP and return tokens |
| `POST` | `/api/v1/auth/login` | Login with email/phone identifier and password |
| `POST` | `/api/v1/auth/password/forgot/initiate` | Start forgot-password OTP |
| `POST` | `/api/v1/auth/password/forgot/verify-otp` | Verify forgot-password OTP and return reset token |
| `POST` | `/api/v1/auth/password/reset` | Reset password with reset token |
| `POST` | `/api/v1/auth/token/refresh` | Refresh access token |
| `POST` | `/api/v1/auth/logout` | Logout/invalidate refresh token |
| `GET` | `/api/v1/auth/me` | Return current authenticated user |

Key request/response models:

```json
POST /api/v1/auth/login
Request:
{
  "identifier": "user@example.com",
  "password": "secret123"
}

Response:
{
  "access_token": "jwt",
  "refresh_token": "jwt",
  "user": {
    "id": "user-id",
    "full_name": "User Name",
    "email": "user@example.com",
    "phone": "+919876543210",
    "role": "consumer"
  }
}
```

Frontend alignment needed:

| Frontend currently calls | Backend currently exposes | Required action |
| --- | --- | --- |
| `/auth/register/initiate` | `/api/v1/auth/signup/initiate` | Rename frontend endpoint or add gateway alias |
| `/auth/register/verify` | `/api/v1/auth/signup/verify-otp` | Rename and send `{ contextId, otp }` |
| `/auth/refresh` | `/api/v1/auth/token/refresh` | Send `refresh_token`, not empty body |
| `/auth/me` | `/api/v1/auth/me` | Prefix mismatch only |

### Catalog Service

Location: `catalog_services`

Run:

```bash
uvicorn app.main:app --reload --port 8002
```

Important endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/home` | Home page banners, featured products, top categories |
| `GET` | `/api/v1/products` | Product listing with search/filter/sort/pagination |
| `GET` | `/api/v1/products/filters` | Available categories, skin types, price range, sort options |
| `GET` | `/api/v1/products/{product_id}` | Product details |
| `GET` | `/api/v1/products/{product_id}/related` | Related products |
| `GET` | `/api/v1/categories` | Category listing |

Product list query parameters:

```text
q, category, price_min, price_max, skin_type, sort, page, limit
```

Frontend alignment needed:

| Frontend currently expects | Backend currently returns | Required action |
| --- | --- | --- |
| `{ products: ProductListItem[] }` from `/products` | `{ total, page, limit, items }` from `/api/v1/products` | Add frontend adapter or gateway mapper |
| `/products/filter-options` | `/api/v1/products/filters` | Rename endpoint |
| `id` as string slugs in mock data | Backend uses numeric `id` and `slug` | Decide whether mobile routes use `id` or `slug` consistently |
| `imageUrl`, `discountPercent`, `reviewCount` | `primary_image_url`, `compare_at_price`, `rating_count` | Map field names |

### Cart Service

Location: `ecommerce_cart`

Run:

```bash
uvicorn app.main:app --reload --port 8003
```

Important endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/cart` | Fetch active cart |
| `POST` | `/api/cart/items` | Add item |
| `PUT` | `/api/cart/items/{product_id}` | Set quantity |
| `DELETE` | `/api/cart/items/{product_id}` | Remove item |
| `DELETE` | `/api/cart` | Clear cart |

Request examples:

```json
POST /api/cart/items
{
  "product_id": 1,
  "quantity": 2
}
```

Response shape:

```json
{
  "id": 1,
  "user_id": "user-id",
  "is_active": true,
  "items": [],
  "total_items": 2,
  "total_price": 2598
}
```

Frontend alignment needed:

The frontend currently uses local cart state heavily and only calls `GET /cart` for initial seed items. To make cart backend-owned, add frontend wrappers for add/update/remove/clear and map `/cart` to `/api/cart` through the gateway.

### Checkout Service

Location: `checkout_system`

Run:

```bash
uvicorn app.main:app --reload --port 8004
```

Important endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/checkout/validate` | Validate cart, delivery, inventory, pricing |
| `POST` | `/api/v1/checkout/session` | Create checkout session |
| `POST` | `/api/v1/guest-checkout/request-verification` | Send email and SMS OTP for guest checkout |
| `POST` | `/api/v1/guest-checkout/verify` | Verify one OTP channel |
| `POST` | `/api/v1/guest-checkout/resend-otp` | Resend OTP for one channel |
| `POST` | `/api/v1/guest-orders` | Place guest order |
| `POST` | `/api/v1/guest-orders/request-lookup` | Send OTP for guest order lookup |
| `POST` | `/api/v1/guest-orders/verify-lookup` | Verify lookup OTP and return orders |

Frontend alignment needed:

The frontend sends one combined payload:

```json
{
  "verificationId": "id",
  "emailOtp": "123456",
  "whatsappOtp": "123456"
}
```

The backend verifies one channel at a time:

```json
{
  "session_id": "id",
  "otp_id": "otp-id",
  "channel": "email",
  "code": "123456"
}
```

Either update the frontend to follow backend two-step channel verification, or add a gateway endpoint that accepts the mobile combined shape and calls the backend twice.

### Inventory Service

Location: `Inventory_services`

Run:

```bash
uvicorn app.main:app --reload --port 8005
```

Important endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/inventory/validate` | Validate stock for one product/warehouse |
| `POST` | `/api/v1/inventory/reservations` | Reserve stock |
| `DELETE` | `/api/v1/inventory/reservations/{reservation_id}` | Release reservation |
| `POST` | `/api/v1/inventory/reservations/{reservation_id}/commit` | Commit reservation after order/payment |

Backend request shape:

```json
{
  "product_id": 1,
  "warehouse_id": 1,
  "quantity": 2,
  "idempotency_key": "checkout-123"
}
```

Frontend alignment needed:

The frontend sends batch items:

```json
{
  "items": [
    { "productId": "dew-ritual-cleanser", "quantity": 1 }
  ]
}
```

For production, inventory should support batch validation/reservation for checkout. The best backend contract for the frontend is:

```json
{
  "items": [
    { "productId": "product-id", "warehouseId": "warehouse-id", "quantity": 1 }
  ],
  "idempotencyKey": "checkout-session-id"
}
```

Then return:

```json
{
  "reservationId": "reservation-id",
  "expiresAt": "2026-05-02T12:00:00Z",
  "items": []
}
```

### Payment Service

Location: `payment_app`

Run:

```bash
uvicorn app.main:app --reload --port 8006
```

Important endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/payments/orders` | Create Razorpay order using amount in minor units |
| `POST` | `/api/v1/payments/intent` | Frontend-compatible mobile payment intent |
| `POST` | `/api/v1/payments/verify` | Verify Razorpay payment signature |
| `GET` | `/api/v1/payments/{payment_reference}/status` | Read payment status |
| `POST` | `/api/v1/payments/webhooks/razorpay` | Razorpay webhook |

Mobile intent request:

```json
{
  "amount": 1599,
  "orderReference": "checkout-session-id",
  "methodLabel": "Card / Netbanking",
  "reservationId": "reservation-id",
  "guestToken": "optional"
}
```

Mobile intent response:

```json
{
  "id": "payment-reference",
  "amount": 1599,
  "provider": "razorpay",
  "status": "created",
  "gatewayOrderId": "order_xxx",
  "currency": "INR"
}
```

This service is already close to the frontend `paymentService.ts` contract.

### Order Service

Location: `order_services`

Run:

```bash
uvicorn app.main:app --reload --port 8007
```

Important endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/orders/finalize` | Finalize order after checkout/payment |
| `POST` | `/api/v1/orders` | Create order |
| `GET` | `/api/v1/orders` | List current user orders |
| `GET` | `/api/v1/orders/{order_id}` | Order detail |
| `GET` | `/api/v1/orders/{order_id}/tracking` | Tracking timeline |

Mobile finalize request shape:

```json
{
  "total": 1599,
  "paymentMethod": "Card / Netbanking",
  "shippingAddress": "Full address text",
  "itemCount": 1,
  "primaryLabel": "Product name",
  "items": [
    {
      "productId": "product-id",
      "productName": "Product name",
      "price": 1599,
      "quantity": 1,
      "imageUrl": "https://..."
    }
  ]
}
```

Frontend alignment needed:

The frontend currently posts to `/orders`, not `/orders/finalize`, and expects `OrderItem` directly. Either point the app to `POST /api/v1/orders/finalize` or create a gateway `/orders` alias that performs finalization.

### Review Service

Location: `review_services`

Run:

```bash
uvicorn app.main:app --reload --port 8008
```

Important endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/products/{product_id}/reviews` | Product review list |
| `GET` | `/api/v1/products/{product_id}/rating-summary` | Rating summary |
| `GET` | `/api/v1/reviews/eligibility/{product_id}` | Can current user review product |
| `POST` | `/api/v1/products/{product_id}/reviews` | Create review |
| `PATCH` | `/api/v1/reviews/{review_id}` | Update review |
| `GET` | `/api/v1/users/me/reviews` | Current user reviews |
| `GET` | `/api/v1/reviews/{review_id}` | Review detail |

Frontend alignment needed:

Frontend currently calls `/account/reviews`, `/account/reviews/{id}`, `/reviews/public`, and posts to `/account/reviews`. These should be mapped to review-service endpoints. Also align field names: frontend uses `comment`, backend uses `title` and `body`.

### User Profile Service

Location: `user_profile_service`

Run:

```bash
uvicorn app.main:app --reload --port 8009
```

Important endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/users/me` | Current user profile |
| `PATCH` | `/api/v1/users/me` | Update current user |
| `GET` | `/api/v1/users/me/addresses` | List addresses |
| `POST` | `/api/v1/users/me/addresses` | Create address |
| `PATCH` | `/api/v1/users/me/addresses/{address_id}` | Update address |
| `DELETE` | `/api/v1/users/me/addresses/{address_id}` | Delete address |
| `PATCH` | `/api/v1/users/me/addresses/{address_id}/default` | Set default address |

Frontend alignment needed:

Frontend currently uses `/account/addresses`. Map that to `/api/v1/users/me/addresses`. Also align fields:

| Frontend field | Backend field |
| --- | --- |
| `name` | `full_name` |
| `line1` | `address_line1` |
| `line2` | `address_line2` |
| `pincode` | `postal_code` |
| `label` | Not currently present |

### Support Service

Location: `support_service`

Run:

```bash
uvicorn app.main:app --reload --port 8010
```

Important endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/support/queries` | Submit support query |
| `GET` | `/api/v1/support/options` | Return support options |

Frontend alignment needed:

The frontend support flow is currently mocked in `accountService.ts`. It should call this service when mock backend is disabled.

### Notification Service

Location: `notification_service`

Run:

```bash
uvicorn app.main:app --reload --port 8011
```

Important endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/notifications/devices/register` | Register device token |
| `DELETE` | `/api/v1/notifications/devices/{device_id}` | Delete device token |
| `POST` | `/api/v1/notifications` | Create notification |
| `GET` | `/api/v1/notifications?user_id=1` | List notifications |
| `PATCH` | `/api/v1/notifications/{notification_id}/read` | Mark notification as read |

## Frontend Readiness Review

The React Native app is already structured well for backend integration:

- It has centralized clients in `src/services/apiClient.ts`.
- It has feature-specific services for auth, product, cart, inventory, payment, account, delivery, and guest access.
- It has a clear mock toggle: `MAHI_USE_MOCK_BACKEND`.
- It stores access tokens and injects `Authorization: Bearer <token>` automatically.
- It already handles backend-style error codes in `src/services/errorService.ts`.

The main limitation is not UI efficiency. The main limitation is contract mismatch. The frontend can handle the backend efficiently once these items are fixed:

1. Add a gateway/BFF or add per-service base URLs.
2. Normalize endpoint paths.
3. Normalize camelCase/snake_case field names.
4. Normalize id strategy: product slug/string ids vs numeric database ids.
5. Add batch inventory reservation endpoints for mobile checkout.
6. Make refresh token storage explicit. The frontend currently stores access token, but the backend refresh route expects `refresh_token`.
7. Replace remaining mocked flows: home content, support, delivery, reviews, addresses, cart mutations.

## Recommended Mobile API Contract

For best frontend efficiency, the mobile app should talk to one gateway contract, even if the backend remains microservices internally.

Recommended mobile-facing endpoints:

| Mobile endpoint | Backend service behind it |
| --- | --- |
| `POST /auth/register/initiate` | Auth |
| `POST /auth/register/verify` | Auth |
| `POST /auth/login` | Auth |
| `POST /auth/refresh` | Auth |
| `GET /auth/me` | Auth/Profile |
| `GET /home` | Catalog |
| `GET /products` | Catalog |
| `GET /products/{idOrSlug}` | Catalog |
| `GET /products/filter-options` | Catalog |
| `GET /cart` | Cart |
| `POST /cart/items` | Cart |
| `PUT /cart/items/{productId}` | Cart |
| `DELETE /cart/items/{productId}` | Cart |
| `GET /account/addresses` | User Profile |
| `POST /account/addresses` | User Profile |
| `PATCH /account/addresses/{id}/default` | User Profile |
| `POST /delivery/check` | Checkout or Delivery service |
| `POST /inventory/validate` | Inventory |
| `POST /inventory/reservations` | Inventory |
| `POST /inventory/reservations/{id}/release` | Inventory |
| `POST /inventory/reservations/{id}/commit` | Inventory |
| `POST /payments/intent` | Payment |
| `POST /payments/verify` | Payment |
| `POST /orders` | Order |
| `GET /orders` | Order |
| `GET /orders/{id}` | Order |
| `GET /orders/{id}/tracking` | Order |
| `GET /reviews/eligibility/{productId}` | Review |
| `POST /account/reviews` | Review |
| `GET /account/reviews` | Review |
| `POST /support/queries` | Support |
| `GET /support/options` | Support |

This lets the mobile app remain simple and stable while backend services can evolve independently behind the gateway.

## Error Contract

The frontend already expects:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Please correct the highlighted details.",
  "fieldErrors": [
    { "field": "email", "message": "Enter a valid email." }
  ]
}
```

Recommended backend standard error codes:

```text
INVALID_OTP
OTP_EXPIRED
OTP_RATE_LIMITED
OUT_OF_STOCK
INSUFFICIENT_STOCK
DELIVERY_UNAVAILABLE
RESERVATION_EXPIRED
PAYMENT_FAILED
PAYMENT_VERIFICATION_FAILED
ORDER_CREATE_FAILED
REVIEW_NOT_ELIGIBLE
UNAUTHORIZED
FORBIDDEN
VALIDATION_ERROR
```

Every service should return this shape through a shared exception handler or gateway-level mapper.

## Local Development

Each service has its own `requirements.txt`.

Typical setup:

```bash
cd <service-folder>
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port <port>
```

Auth service uses:

```bash
uvicorn auth.main:app --reload --port 8001
```

OpenAPI documentation:

```text
http://localhost:<port>/docs
http://localhost:<port>/openapi.json
```

## Production Notes

- Put services behind a gateway or service mesh.
- Keep service databases private to each service.
- Use idempotency keys for checkout, inventory reservation, payment creation, and order finalization.
- Verify Razorpay signatures only on the backend.
- Do not let the frontend commit inventory or create orders until payment verification succeeds.
- Use short-lived access tokens and store refresh tokens securely.
- Standardize request/response casing at the mobile boundary.
- Add health checks for every service.
- Add centralized logs with request ids across gateway and microservices.

## Current Backend Efficiency For The Frontend

The backend can support the current frontend with good efficiency after contract alignment. The service split is strong for scaling because catalog browsing, auth, cart, inventory, payment, and orders can scale separately. Payment intent is already frontend-compatible. Review, profile, support, and catalog are mostly ready.

The biggest immediate work is API normalization, not performance tuning. Once a gateway maps the routes and fields, the frontend can move from mock mode to real backend mode with much less screen-level change.
