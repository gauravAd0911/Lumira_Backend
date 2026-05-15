# API_HANDLER_DATA_PROVIDER

## Purpose
This document maps the backend FastAPI endpoints to their implementation handlers, data sources, and frontend-facing request/response contracts. It is intended for engineers and frontend integrators who need to understand:

- Which API endpoints exist in each microservice
- What each endpoint does
- What database tables/models are read or written
- What data is returned to the frontend
- When internal service-to-service calls are used

## Service Overview
The backend is composed of multiple microservices. The main services documented here are:

- Auth service (`Auther_M2/Auther_M`) — user signup/login/password flow
- Catalog service (`catalog_services`) — product and category listing
- Cart service (`ecommerce_cart`) — shopping cart management
- Checkout service (`checkout_system`) — guest checkout, order placement, inventory validation
- Order service (`order_services`) — order lifecycle, tracking, admin operations
- Payment service (`payment_app`) — payment creation, verification, status querying
- Notification service (`notification_service`) — device registration, push/email/WhatsApp notifications
- User Profile service (`user_profile_service`) — profile and address management
- Review service (`review_services`) — product reviews and eligibility
- Support service (`support_service`) — support ticket creation and admin ticket operations

---

## 1. Auth Service
### Base route area
- Auth router path: configured in `auth/routes/v1_auth.py`
- Key internal models: `User`, `EmployeeProfile`, `OtpContext`, `AuthSession`, `PasswordResetToken`
- Main database tables:
  - `users`
  - `employee_profiles`
  - `otp_contexts`
  - `auth_sessions`
  - `password_reset_tokens`

### API endpoints

#### `POST /signup/initiate`
- Handler: `signup_initiate`
- Purpose: create or update a pending user, generate OTP context, send OTP SMS
- DB reads/writes:
  - reads/writes `users`
  - writes `otp_contexts`
- Frontend contract:
  - request: `email`, `phone`, `full_name`, `password`
  - response: `context_id`, `message`, `otp_expiry_seconds`

#### `POST /signup/verify-otp`
- Handler: `signup_verify`
- Purpose: verify signup OTP and issue auth tokens
- DB reads/writes:
  - reads `otp_contexts`
  - reads/writes `users` (sets `is_verified`)
  - writes `auth_sessions` via `create_session`
- Frontend contract:
  - request: `context_id`, `otp`
  - response: `access_token`, `refresh_token`, `user`

#### `POST /login`
- Handler: `login`
- Purpose: authenticate existing user by email or phone and password
- DB reads/writes:
  - reads `users`
  - writes `auth_sessions`
- Frontend contract:
  - request: `identifier`, `password`
  - response: `access_token`, `refresh_token`, `user`

#### `POST /password/forgot/initiate`
- Handler: `forgot_initiate`
- Purpose: start forgot-password flow and send OTP if user exists
- DB reads/writes:
  - reads `users`
  - writes `otp_contexts` when user exists
- Frontend contract:
  - request: `identifier`
  - response: `context_id`, `message`, `otp_expiry_seconds`

#### `POST /password/forgot/verify-otp`
- Handler: `forgot_verify`
- Purpose: verify OTP and generate reset token
- DB reads/writes:
  - reads `otp_contexts`
  - reads `users`
  - writes `password_reset_tokens`
- Frontend contract:
  - request: `context_id`, `otp`
  - response: `reset_token`, `reset_token_expiry_seconds`

#### `POST /password/reset`
- Handler: `password_reset`
- Purpose: update password from reset token
- DB reads/writes:
  - reads `password_reset_tokens`
  - reads/writes `users` (`password_hash`)
- Frontend contract:
  - request: `reset_token`, `new_password`
  - response: success message

#### `POST /token/refresh`
- Handler: `token_refresh`
- Purpose: refresh access/refresh token pair
- DB reads/writes:
  - reads/writes `auth_sessions`
  - reads `users`
- Frontend contract:
  - request: `refresh_token`
  - response: `access_token`, `refresh_token`, `user`

#### `POST /logout`
- Handler: `logout`
- Purpose: revoke refresh token session
- DB writes:
  - updates `auth_sessions.revoked_at`
- Frontend contract:
  - request: `refresh_token`
  - response: success message

#### `GET /me`
- Handler: `me`
- Purpose: return current authenticated user profile
- DB reads:
  - `users`
- Frontend contract:
  - response: `id`, `full_name`, `email`, `phone`, `role`

#### `PATCH /me`
- Handler: `update_me`
- Purpose: update profile fields for active user
- DB reads/writes:
  - reads/writes `users`
- Frontend contract:
  - request: fields such as `full_name`, `email`, `phone`
  - response: updated `user`

### Notes
- The auth service centralizes signup/login/password flows.
- OTP state lives in `otp_contexts` and is reused for signup/password reset.
- Session rotation and logout are implemented through `auth_sessions`.

---

## 2. Catalog Service
### Base route area
- Product routes: `catalog_services/app/api/v1/endpoints/products.py`
- Category routes: `catalog_services/app/api/v1/endpoints/categories.py`
- Main data models: `Product`, `Category`, `ProductImage`, `ProductTag`
- Main database tables:
  - `products`
  - `categories`
  - `product_images`
  - `product_tags`
  - `home_banners` (not part of these endpoints)

### API endpoints

#### `GET /products`
- Handler: `list_products`
- Purpose: list filtered, paginated products for storefront
- DB reads:
  - `products`
  - `categories` if filters require category joins
  - `product_tags`/other product metadata via service logic
- Frontend contract:
  - request query: `q`, `category`, `price_min`, `price_max`, `skin_type`, `sort`, `page`, `limit`
  - response: product listing with summary fields

#### `GET /products/filters`
- Handler: `get_filter_options`
- Purpose: return available listing facets and filter options
- DB reads:
  - `products`
  - `categories`
  - tag/attribute tables used by catalog filters
- Frontend contract:
  - response: category filters, price range, skin type options, sort options

#### `GET /products/{product_id}`
- Handler: `get_product`
- Purpose: return full product detail
- DB reads:
  - `products`
  - `product_images`
  - `product_tags`
  - category metadata if applicable
- Frontend contract:
  - response: detailed product record including name, slug, price, stock, images, attributes, description

#### `GET /products/{product_id}/related`
- Handler: `get_related_products`
- Purpose: list related products by category or rating
- DB reads:
  - `products`
  - category relationships via product metadata
- Frontend contract:
  - response: product list of related items

#### `POST /admin/products`
- Handler: `create_admin_product`
- Purpose: create new catalog product
- DB writes:
  - new row in `products`
  - associated rows in `product_images` / `product_tags` as needed
- Frontend contract:
  - request: admin product payload
  - response: created product data

#### `PUT /admin/products/{product_id}`
- Handler: `update_admin_product`
- Purpose: update existing product
- DB reads/writes: `products` and related metadata tables
- Frontend contract: updated product record

#### `DELETE /admin/products/{product_id}`
- Handler: `delete_admin_product`
- Purpose: soft/persistent delete of product
- DB writes: product status change or deletion in `products`
- Frontend contract: deleted product id

#### `GET /categories`
- Handler: `list_categories`
- Purpose: return all active categories for navigation
- DB reads: `categories`
- Frontend contract: category list with id, name, slug, sort order

### Notes
- Product listing and detail are implemented through `CatalogService`.
- The service provides the frontend with active catalog entries and filter metadata.

---

## 3. Cart Service
### Base route area
- Router: `ecommerce_cart/ecommerce_cart/app/routers/cart.py`
- Main data models: `Cart`, `CartItem`, `Product`
- Main database tables:
  - `carts`
  - `cart_items`
  - `products`

### API endpoints

#### `GET /api/v1/cart`
- Handler: `get_cart`
- Purpose: fetch active cart for the current user
- DB reads/writes:
  - reads and/or creates `carts`
  - reads `cart_items`
  - reads `products`
- Frontend contract:
  - response: cart items, product snapshots, quantity, pricing summary

#### `POST /api/v1/cart/items`
- Handler: `add_item`
- Purpose: add a product to cart or increment existing line item
- DB reads/writes:
  - reads `products` by `id` or `external_product_id`
  - may create `products` for external catalog entries
  - reads/creates `carts`
  - reads/writes `cart_items`
- Frontend contract:
  - request: `product_id`, `quantity`, optional `product_name`, `slug`, `price`, `stock`, `image_url`
  - response: updated cart payload

#### `POST /api/v1/cart/merge`
- Handler: `merge_cart`
- Purpose: merge guest cart into authenticated user's cart
- DB reads/writes:
  - reads `carts` for guest user and authenticated user
  - reads `cart_items`, `products`
  - writes `cart_items`
  - updates guest `carts.is_active`
- Frontend contract:
  - request: `guest_token`
  - response: merged cart payload

#### `PATCH /api/v1/cart/items/{product_id}`
- Handler: `update_item`
- Purpose: set exact quantity of an item
- DB reads/writes:
  - reads `products`
  - reads `carts`
  - reads/writes `cart_items`
- Frontend contract:
  - request: `quantity`
  - response: updated cart payload

#### `DELETE /api/v1/cart/items/{product_id}`
- Handler: `remove_item`
- Purpose: remove a cart line item
- DB reads/writes:
  - reads `carts`
  - reads `cart_items`
  - deletes `cart_items`
- Frontend contract: updated cart payload

#### `DELETE /api/v1/cart`
- Handler: `clear_cart`
- Purpose: empty the active cart
- DB writes:
  - deletes `cart_items`
- Frontend contract: empty cart summary

### Notes
- This cart implementation uses product snapshots in `products` inside the cart service.
- It supports guest carts identified by `guest:<token>` and authenticated carts by actual user id.

---

## 4. Checkout Service
### Base route area
- Guest checkout: `checkout_system/app/routers/guest_checkout.py`
- Guest orders: `checkout_system/app/routers/guest_orders.py`
- Checkout validation/session: `checkout_system/app/routers/checkout.py`
- Inventory reservation: `checkout_system/app/routers/inventory.py`
- Main database tables:
  - `guest_checkout_sessions`
  - `guest_otps`
  - `guest_orders`
  - `addresses`
  - `checkout_sessions`
  - `checkout_orders`
  - `inventory_reservations`
  - `serviceable_pincodes`
  - `products` (snapshot products)

### Guest checkout endpoints

#### `POST /api/v1/guest-checkout/request-verification`
- Handler: `request_verification`
- Purpose: create or reuse guest checkout session and send OTPs via email + SMS
- DB reads/writes:
  - reads/writes `guest_checkout_sessions`
  - writes `guest_otps`
- Frontend contract:
  - request: `guest_name`, `email`, `phone`
  - response: `session_id`, channel OTP metadata, masked email/phone, expiration

#### `POST /api/v1/guest-checkout/verify`
- Handler: `verify`
- Purpose: verify one OTP channel and return guest session token after both channels are verified
- DB reads/writes:
  - reads/writes `guest_otps`
  - reads/writes `guest_checkout_sessions`
- Frontend contract:
  - request: `session_id`, `otp_id`, `channel`, `code`
  - response: verification state, `session_token` once both email and SMS are verified

#### `POST /api/v1/guest-checkout/resend-otp`
- Handler: `resend_otp`
- Purpose: resend OTP for a guest checkout channel
- DB reads/writes:
  - reads `guest_checkout_sessions`
  - writes `guest_otps`
- Frontend contract:
  - request: `session_id`, `channel`
  - response: new `otp_id`, resend quota, expiration

### Guest orders endpoints

#### `POST /api/v1/guest-orders`
- Handler: `place_order`
- Purpose: place a guest checkout order after verification
- DB reads/writes:
  - validates `guest_checkout_sessions`
  - reads/writes `guest_orders`
  - may call internal order creation or internal service APIs
- Frontend contract:
  - request: order payload including `items`, `paymentDetails`, `shippingDetails`, and `session_token`
  - response: created guest order data

#### `POST /api/v1/guest-orders/request-lookup`
- Handler: `request_lookup`
- Purpose: start guest order lookup via email OTP
- DB reads/writes:
  - writes lookup OTP session (same `guest_otps` / guest checkout session structure)
- Frontend contract:
  - request: `email`
  - response: lookup `session_id`, `otp_id`, expiration

#### `POST /api/v1/guest-orders/verify-lookup`
- Handler: `verify_lookup`
- Purpose: verify lookup OTP and return matching guest orders
- DB reads:
  - `guest_orders`
  - lookup session state
- Service-to-service calls:
  - internal request to Order service endpoint `/api/v1/orders/internal/guest-lookup`
- Frontend contract:
  - request: `session_id`, `otp_id`, `channel`, optional `order_number`
  - response: list of guest orders

### Checkout validation/session endpoints

#### `POST /api/v1/checkout/validate`
- Handler: `validate_checkout`
- Purpose: validate order items, inventory, pricing and delivery availability before checkout
- DB reads/writes:
  - reads/writes `products` snapshot table
  - reads `serviceable_pincodes`
- Frontend contract:
  - request: `items`, `address`, `guest_token`, optional `address_id`
  - response: validation result, `cart_valid`, `delivery_valid`, `inventory_valid`, pricing, `issues`

#### `POST /api/v1/checkout/session`
- Handler: `create_checkout_session`
- Purpose: create a temporary checkout reservation session
- DB writes:
  - writes `checkout_sessions`
- Frontend contract:
  - request: checkout payload with items, address, guest token
  - response: `checkoutId`, `reservation_required`, pricing, `expires_at`, `items`, `address_id`

### Inventory reservation endpoints

#### `POST /api/v1/inventory/validate`
- Handler: `validate_inventory`
- Purpose: validate stock availability for reservation
- DB reads:
  - `products`
  - `inventory_reservations`
- Frontend contract:
  - request: `items`, optional `warehouse_id`
  - response: `is_available`, `available_quantity`, `issues`

#### `POST /api/v1/inventory/reservations`
- Handler: `create_reservation`
- Purpose: reserve stock for checkout until expiry
- DB writes:
  - writes `inventory_reservations`
- Frontend contract:
  - request: `items`, optional `warehouse_id`, optional `idempotency_key`
  - response: reservation payload with `reservation_id`, expiry, item details

#### `DELETE /api/v1/inventory/reservations/{reservation_id}`
- Handler: `release_reservation`
- Purpose: release a reservation early
- DB writes:
  - updates `inventory_reservations.status` to `released`
- Frontend contract:
  - response: `reservation_id`

#### `POST /api/v1/inventory/reservations/{reservation_id}/commit`
- Handler: `commit_reservation`
- Purpose: commit a reservation when order is finalized
- DB reads/writes:
  - reads `inventory_reservations`
  - reads/writes `products.stock_qty`
  - updates reservation `status` to `committed`
- Frontend contract:
  - response: committed reservation id

### Notes
- Checkout and inventory validation share `products` snapshot tables to keep pricing/stock accurate when external item payloads are provided.
- `serviceable_pincodes` drives delivery availability logic.
- Guest flows maintain multi-channel OTP state in `guest_checkout_sessions` and `guest_otps`.

---

## 5. Order Service
### Base route area
- Router: `order_services/app/api/order_routes.py`
- Main internal models: `Order`, `OrderItem`, `OrderStatusHistory`
- Main database tables:
  - `orders`
  - `order_items`
  - `order_tracking`

### API endpoints

#### `POST /api/v1/orders/finalize`
- Handler: `finalize`
- Purpose: finalize order payload and persist order state
- DB writes:
  - `orders`
  - `order_items`
  - `order_tracking` via order service logic
- Frontend contract:
  - request: `FinalizeOrderRequest` payload
  - response: created order summary

#### `POST /api/v1/orders`
- Handler: `create_order`
- Purpose: create a new order after payment verification
- DB reads/writes:
  - reads `payments` indirectly via payment service call
  - reads/writes `orders`
  - writes `order_items`
- External call:
  - payment status fetched from Payment service `/api/v1/payments/{reference}/status`
- Frontend contract:
  - request: complete checkout order payload with `paymentDetails.paymentReference`
  - response: created order detail

#### `GET /api/v1/orders`
- Handler: `get_orders`
- Purpose: fetch user or admin order list
- DB reads:
  - `orders`
  - `order_items` if summary data requires item count
- Frontend contract:
  - response: list of orders with `orderNumber`, `status`, `total`, `placedOn`, `paymentReference`

#### `GET /api/v1/orders/{order_id}`
- Handler: `get_order`
- Purpose: fetch order details for user or operational staff
- DB reads:
  - `orders`
  - `order_items`
- Frontend contract:
  - response: full order detail with shipping, payment, items, status note

#### `GET /api/v1/orders/{order_id}/tracking`
- Handler: `get_tracking`
- Purpose: return tracking history for an order
- DB reads:
  - `orders`
  - `order_tracking`
- Frontend contract:
  - response: `tracking` list entries

#### `GET /api/v1/orders/internal/guest-lookup`
- Handler: `internal_guest_lookup`
- Purpose: internal service lookup for guest orders by email
- DB reads:
  - `orders`
- Frontend contract:
  - response: guest orders list for internal consumers

#### `PATCH /api/v1/orders/admin/{order_id}/status`
- Handler: `update_order_status`
- Purpose: operational order status transition and tracking
- DB reads/writes:
  - `orders`
  - `order_tracking`
- Frontend contract:
  - request: `status`, optional `note`, `actorUserId`
  - response: updated order detail

#### `PATCH /api/v1/orders/admin/{order_id}/assign`
- Handler: `assign_order`
- Purpose: assign order to an employee
- DB writes:
  - updates `orders.assigned_to_employee_id`
- Frontend contract:
  - request: `employeeId`
  - response: updated order detail

#### `GET /api/v1/orders/admin/dashboard/summary`
- Handler: `admin_dashboard_summary`
- Purpose: return admin metrics for orders
- DB reads:
  - `orders`
- Frontend contract:
  - response: `total_orders`, `gross_revenue`, `average_order_value`, `status_breakdown`

### Notes
- Order creation verifies payment externally before persisting the order.
- Guest lookup in the checkout flow may merge local guest orders with data returned from this endpoint.

---

## 6. Payment Service
### Base route area
- Router: `payment_app/payment_app/app/routers/payment.py`
- Main models: `Payment`, `PaymentEvent`, `Order`, `Cart`
- Main database tables:
  - `payments`
  - `payment_events`
  - `orders`
  - `carts`

### API endpoints

#### `POST /api/v1/payments/orders`
- Handler: `create_payment_order`
- Purpose: create a payment order with payment provider (Razorpay)
- DB writes:
  - `payments` with provider order details
- Frontend contract:
  - request: `amount`, `currency`
  - response: `payment_reference`, `provider`, `razorpay_order_id`, `amount`, `currency`, `key_id`

#### `POST /api/v1/payments/intent`
- Handler: `create_payment_intent`
- Purpose: create a payment intent for mobile or custom workflow
- DB writes:
  - `payments`
- Frontend contract:
  - request: `amount`, `currency`, optional `orderReference`, `receipt`, `reservationId`, `guestToken`
  - response: provider order id or payment reference depending on payload

#### `POST /api/v1/payments/verify`
- Handler: `verify_payment`
- Purpose: verify Razorpay payment details after checkout
- DB writes:
  - updates `payments.status`, `payment_events`, provider IDs
- Frontend contract:
  - request: `payment_reference`/`paymentReference`, `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`
  - response: verification status and `paymentReference`

#### `GET /api/v1/payments/{payment_reference}/status`
- Handler: `get_payment_status`
- Purpose: fetch payment record or optionally reconcile with provider
- DB reads/writes:
  - `payments`
  - `payment_events` if reconciliation occurs
- Frontend contract:
  - response: `payment_reference`, `provider`, `status`, `razorpay_order_id`, `provider_payment_id`, `amount`, `currency`, `verified_at`

#### `POST /api/v1/payments/webhooks/razorpay`
- Handler: `razorpay_webhook`
- Purpose: receive Razorpay webhook and process payment events
- DB writes:
  - `payments`
  - `payment_events`
- Frontend contract:
  - not directly used by frontend; provider callback endpoint

#### Legacy endpoints
- `GET /create-order`
- `POST /verify`
- Purpose: legacy cart/payment flows for older integrations
- DB reads/writes: `payments`, `orders`, `carts`

### Notes
- Payment service is the source-of-truth for provider payment state.
- Orders use payment reference verification before final creation.

---

## 7. Notification Service
### Base route area
- Router: `notification_service/app/routes/notification_routes.py`
- Main models: `Device`, `Notification`
- Main database tables:
  - `devices`
  - `notifications`

### API endpoints

#### `POST /api/v1/notifications/devices/register`
- Handler: `register_device`
- Purpose: register or refresh a push notification device token
- DB writes:
  - upserts `devices`
- Frontend contract:
  - request: `user_id`, `device_token`, `platform`
  - response: `device_id`, `user_id`, `device_token`, `platform`

#### `DELETE /api/v1/notifications/devices/{device_id}`
- Handler: `delete_device`
- Purpose: remove registered device token
- DB writes: delete `devices`
- Frontend contract: success message

#### `POST /api/v1/notifications`
- Handler: `create_notification`
- Purpose: create a notification record for a user
- DB writes: `notifications`
- Frontend contract:
  - request: `user_id`, `title`, `message`, `type`
  - response: notification object

#### `GET /api/v1/notifications`
- Handler: `get_notifications`
- Purpose: fetch notifications for a user
- DB reads: `notifications`
- Frontend contract: list of notification objects

#### `PATCH /api/v1/notifications/{notification_id}/read`
- Handler: `mark_read`
- Purpose: mark a notification as read
- DB writes: updates notification status
- Frontend contract: updated notification object

#### `POST /api/v1/notifications/email`
- Handler: `send_email_notification`
- Purpose: send a templated email notification
- DB does not persist state directly in this handler
- Frontend contract:
  - request: `type`, `recipient`, `data`
  - response: success status

### Notes
- Notification service stores device and notification state but delegates actual sending to email/WhatsApp/Twilio service utilities.

---

## 8. User Profile Service
### Base route area
- Router: `user_profile_service/app/api/v1/endpoints/user.py`
- Address router: `user_profile_service/app/api/v1/endpoints/address.py`
- Main database tables:
  - `app_users`
  - `addresses`

### API endpoints

#### `GET /me`
- Handler: `get_me`
- Purpose: return the current user's profile
- DB reads: `app_users`
- Frontend contract:
  - response: user profile fields from `UserResponse`

#### `PATCH /me`
- Handler: `update_me`
- Purpose: update user profile fields
- DB writes: `app_users`
- Frontend contract:
  - request: profile updates
  - response: updated user profile

#### `GET /addresses`
- Handler: `get_addresses`
- Purpose: list addresses for current user
- DB reads: `addresses`
- Frontend contract:
  - response: list of address objects

#### `GET /addresses/{address_id}`
- Handler: `get_address`
- Purpose: fetch a specific address
- DB reads: `addresses`
- Frontend contract: single address object

#### `POST /addresses`
- Handler: `create_address`
- Purpose: store a new address for current user
- DB writes: `addresses`
- Frontend contract:
  - request: address fields
  - response: saved address object

#### `PATCH /addresses/{address_id}`
- Handler: `update_address`
- Purpose: update existing address
- DB writes: `addresses`
- Frontend contract: updated address object

#### `DELETE /addresses/{address_id}`
- Handler: `delete_address`
- Purpose: remove address record
- DB writes: delete `addresses`
- Frontend contract: deleted address info

#### `PATCH /addresses/{address_id}/default`
- Handler: `set_default`
- Purpose: set address as default
- DB writes: `addresses`
- Frontend contract: updated address object

### Notes
- This service is the authoritative store for user profile and address data separate from auth.

---

## 9. Review Service
### Base route area
- Router: `review_services/app/api/v1/endpoints/reviews.py`
- Main database tables:
  - `products`
  - `users`
  - `orders`
  - `reviews`
  - `outbox_events`

### API endpoints

#### `GET /products/{product_id}/reviews`
- Handler: `list_product_reviews`
- Purpose: list reviews for a product with pagination
- DB reads: `reviews`, `products`
- Frontend contract: paginated review list

#### `GET /products/{product_id}/rating-summary`
- Handler: `get_rating_summary`
- Purpose: return aggregate rating data for product
- DB reads: `reviews`
- Frontend contract: rating summary fields

#### `GET /reviews/eligibility/{product_id}`
- Handler: `get_review_eligibility`
- Purpose: determine if current user can submit review
- DB reads: `orders`, `reviews`
- Frontend contract: `can_review`, `reason`

#### `GET /reviews`
- Handler: `list_reviews`
- Purpose: list reviews optionally filtered by product
- DB reads: `reviews`
- Frontend contract: paginated reviews list

#### `POST /products/{product_id}/reviews`
- Handler: `create_review`
- Purpose: create a new review for a product
- DB writes: `reviews`
- Frontend contract: created review object

#### `POST /account/reviews`
- Handler: `create_review_compat`
- Purpose: legacy review creation for alternate payload formats
- DB writes: `reviews`
- Frontend contract: created review object

#### `GET /account/reviews`
- Handler: `get_my_reviews_compat`
- Purpose: fetch reviews by current user
- DB reads: `reviews`
- Frontend contract: list of current user reviews

#### `GET /account/reviews/{review_id}` and `GET /reviews/{review_id}`
- Handler: `get_review` / `get_review_compat`
- Purpose: fetch individual review detail
- DB reads: `reviews`
- Frontend contract: single review object

#### `GET /reviews/public`
- Handler: `list_public_reviews`
- Purpose: public listing for a single product
- DB reads: `reviews`
- Frontend contract: paginated result

#### `PATCH /reviews/{review_id}`
- Handler: `patch_review`
- Purpose: update review body/rating
- DB writes: `reviews`
- Frontend contract: updated review object

### Notes
- Review service also uses outbox events for asynchronous processing and integrations.

---

## 10. Support Service
### Base route area
- Router: `support_service/app/api/support_routes.py`
- Main database tables:
  - `support_tickets`
  - `support_options`
  - `users`

### API endpoints

#### `POST /support/queries`
- Handler: `create_support`
- Purpose: create a support ticket from user input
- DB writes: `support_tickets`
- Frontend contract:
  - request: `email`, `subject`, `message`, optional `user_id`
  - response: ticket details

#### `GET /support/options`
- Handler: `get_support_options`
- Purpose: return static support contact options
- DB reads: none (hard-coded)
- Frontend contract: support contact options

#### `GET /admin/queries`
- Handler: `list_all_queries`
- Purpose: list open support tickets for admin/employee
- DB reads: `support_tickets`
- Frontend contract: list of ticket objects

#### `PATCH /admin/queries/{ticket_id}`
- Handler: `update_query`
- Purpose: update support ticket status or assignment
- DB reads/writes: `support_tickets`
- Frontend contract: updated ticket detail

#### `GET /admin/queries/{ticket_id}`
- Handler: `get_query`
- Purpose: fetch one support ticket
- DB reads: `support_tickets`
- Frontend contract: ticket object

### Notes
- `support_options` is statically returned and not backed by a database table in the current implementation.

---

## 11. Cross-Service Patterns
### Auth and profile
- Auth service owns login/signup/token state.
- User profile service owns profile and address details.
- Frontend should authenticate via Auth service and then fetch profile/address from User Profile service.

### Checkout and order integration
- Checkout service handles payment-ready session state and validation.
- Order service finalizes orders after payment verification and tracks fulfillment state.
- Guest order lookup may call Order service internally for a combined result.

### Payment dependencies
- Payment service stores provider references in `payments` and exposes status verification APIs.
- Order service verifies payment before creating an order and then persists order data.

### Notification integration
- Order service may trigger notification workflows when statuses change.
- Notification service handles device registration and outbound email/WhatsApp flows.

---

## 12. Frontend Data Provider Guidance
### How frontend should use this mapping
1. **Auth flows**: call Auth service endpoints for login/signup/refresh/logout.
2. **Catalog**: query Catalog service for product list/detail and category navigation.
3. **Cart**: manage cart with Cart service APIs; use `guest_token` to merge guest cart after login.
4. **Checkout**: validate cart and address, create checkout session, reserve stock, then pass payment reference to order service.
5. **Payment**: create payment order/intent from Payment service; verify with `payment_reference`.
6. **Order history**: fetch orders from Order service.
7. **Reviews**: use Review service for product reviews and eligibility checks.
8. **Notifications**: register device tokens and fetch notifications from Notification service.
9. **Support**: create support tickets and allow admin staff to manage them.

### Practical request/response notes
- Many endpoints return a common envelope with `success`, `message`, `data`, `error`.
- Auth responses often return the `user` object with id, name, email, phone, and role.
- Cart responses include `items` and `summary` with `subtotal`, `shipping`, `tax`, `total`, and `currency`.
- Checkout/inventory responses provide `issues` arrays for invalid items or unavailable stock.
- Order responses include `orderNumber`, `status`, `paymentReference`, `shippingDetails`, and item line information.

---

## 13. Quick Table Reference
| Service | Endpoint | Data Source / Tables | Notes |
|---|---|---|---|
| Auth | `/signup/initiate` | `users`, `otp_contexts` | OTP starts signup flow |
| Auth | `/login` | `users`, `auth_sessions` | returns tokens |
| Catalog | `/products` | `products`, `categories`, `product_tags`, `product_images` | filter/pagination |
| Cart | `/api/v1/cart/items` | `products`, `carts`, `cart_items` | active cart item add |
| Checkout | `/api/v1/checkout/session` | `checkout_sessions`, `products`, `serviceable_pincodes` | creates temporary checkout session |
| Order | `/api/v1/orders` | `orders`, `order_items`, payment service | creates final order after payment |
| Payment | `/api/v1/payments/verify` | `payments`, `payment_events` | verifies provider payment |
| Notification | `/api/v1/notifications/devices/register` | `devices` | device token registration |
| Profile | `/me` | `app_users` | get current user profile |
| Review | `/products/{id}/reviews` | `reviews`, `products`, `users` | product review list |
| Support | `/support/queries` | `support_tickets` | create support ticket |

---

## 14. Implementation Notes
- When building frontend integrations, prefer the dedicated endpoints in the service owning the data.
- For user identity, use Auth service tokens; for profile/address data, use User Profile service.
- Guest checkout and guest orders use session tokens separate from authenticated user sessions.
- `inventory` endpoints are designed for pre-order validation/reservation; `checkout` endpoints store actual session snapshots.
- The review service is asynchronous-friendly but still reads from `reviews` and `orders` tables for eligibility.

---

## 15. Recommended Next Steps
- Align frontend route configuration to service prefixes for each microservice.
- Confirm which environment variables point each service to others (`PAYMENT_SERVICE_BASE_URL`, `ORDER_SERVICE_BASE_URL`, `INTERNAL_SERVICE_TOKEN`).
- Use the Auth service token in `Authorization` or `X-User-Id` headers as expected by the request handlers.
- Validate actual table names with the deployed schema before production integration.

---

## 16. Appendix: Key Database Table Names
- Auth: `users`, `employee_profiles`, `otp_contexts`, `auth_sessions`, `password_reset_tokens`
- Catalog: `products`, `categories`, `product_images`, `product_tags`, `home_banners`
- Cart: `carts`, `cart_items`, `products`
- Checkout: `guest_checkout_sessions`, `guest_otps`, `guest_orders`, `addresses`, `checkout_sessions`, `checkout_orders`, `inventory_reservations`, `serviceable_pincodes`
- Order: `orders`, `order_items`, `order_tracking`
- Payment: `payments`, `payment_events`, `orders`, `carts`
- Notification: `devices`, `notifications`
- User Profile: `app_users`, `addresses`
- Review: `products`, `users`, `orders`, `reviews`, `outbox_events`
- Support: `support_tickets`, `support_options`, `users`
