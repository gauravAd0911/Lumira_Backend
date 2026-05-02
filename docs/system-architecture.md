# System Architecture

## 1. System Overview

This D2C platform is split into three delivery surfaces backed by FastAPI microservices:

- React Web: customer, admin, and employee experiences
- React Native Mobile: customer experience
- FastAPI microservices: auth, catalog, cart, checkout, inventory, payments, orders, reviews, support, and profile

The backend is the system of record. Frontends are responsible for presentation, session handling, and optimistic UX only. Pricing, stock validation, checkout validation, payment verification, and order creation are owned by backend services.

## 2. Module Breakdown

- `auth`: registration, login, OTP, refresh, profile session lookup
- `catalog`: product listing, product detail, filters, merchandising content
- `cart`: persistent cart items and backend-calculated cart summary
- `checkout`: delivery validation, checkout validation, checkout session creation
- `inventory`: stock validation, limited-stock warnings, reservation, release, commit
- `payments`: Razorpay order creation, verification, reconciliation, webhook ingestion
- `orders`: order finalization, order listing, order detail, tracking
- `user_profile_service`: profile and address ownership
- `review_services`: review eligibility and review CRUD
- `support_service`: customer support query intake and admin handling

## 3. User Flows

### Customer flow

1. User signs up or logs in through auth service.
2. Catalog APIs return products and filter metadata.
3. Cart APIs persist line items and return backend-owned totals.
4. Checkout validation confirms address, delivery, pricing, and inventory.
5. Checkout service creates a reservation-ready checkout session with backend pricing.
6. Inventory service reserves stock for a short TTL before payment.
7. Payment service creates a Razorpay payment intent/order.
8. Backend verifies payment signature.
9. Order service finalizes the order after verified payment.
8. Customer fetches order list and order detail from order service.

### Admin flow

1. Admin authenticates with role `admin`.
2. Admin manages catalog and internal users through protected APIs.
3. Admin reviews support queries and order state.
4. Admin performs operational updates through backend-authorized routes only.

## 4. Where Logic Lives

### Backend-owned logic

- pricing totals
- discount calculation
- shipping charge calculation
- stock validation
- stock reservation lifecycle
- delivery pincode serviceability
- payment verification
- order creation rules
- order state transitions
- role-based access control

### Frontend-owned logic

- rendering
- navigation
- loading and retry states
- local input validation before submit
- local persistence only when mock mode is explicitly enabled

No frontend should decide final totals, verify payment authenticity, or create orders without backend confirmation.

## 5. API Contract Summary

All production APIs should return the same envelope:

```json
{
  "success": true,
  "message": "Human-readable outcome",
  "data": {},
  "error": null
}
```

Error responses use:

```json
{
  "success": false,
  "message": "Human-readable error",
  "data": null,
  "error": {
    "code": "MACHINE_CODE",
    "message": "Human-readable error",
    "details": []
  }
}
```

The web and mobile clients now normalize this envelope in their shared API layers before mapping into UI models.

## 6. Role-Based Access

- `customer`: browse, cart, checkout, orders, profile, reviews, support
- `employee`: operational access only, no customer checkout/cart actions
- `admin`: full operational and management access

Frontend role gating is for UX only. Backend authorization remains authoritative.

## 7. State Synchronization

- Cart state is synchronized from backend cart APIs in production mode.
- Checkout pricing is refreshed from checkout validation rather than recomputed locally.
- Delivery-aware shipping is refreshed from backend checkout validation before payment opens.
- Payment state flows from payment intent to backend verification to order finalization.
- Both web and mobile use the same reserve -> pay -> commit / release inventory pattern.
- Order history is read from order service, not reconstructed from client-side state.
- Mock storage remains available only for explicit mock-mode development.

## 8. Error Handling Strategy

- Validation errors return `VALIDATION_ERROR` with field-level `details`.
- Auth failures return machine-readable auth codes.
- Checkout and inventory failures return actionable issue details.
- Limited stock is returned as a warning without blocking checkout session creation.
- Payment failures never create a confirmed order.
- Client interceptors handle token expiry and session refresh centrally.

## 9. Build and Run Instructions

### Backend

- Start each FastAPI service from its own service root with its configured environment.
- Required live services for the customer checkout path:
  - auth
  - catalog
  - cart
  - checkout
  - inventory
  - payments
  - orders

### Web

```bash
cd E:\Push_projects\AIBarejTech_pushed\D2Cwebsite
npm install
npm run build
npm run dev
```

### Mobile

```bash
cd E:\Learning Projects\Android_react_native_apps\MahiApp
npm install
npx tsc --noEmit
npm test -- --runInBand --watch=false
npm run android
```

### Environment expectations

- Disable mock mode in production:
  - Web: `VITE_USE_MOCK_BACKEND=false`
  - Mobile: `MAHI_USE_MOCK_BACKEND=false`
- Configure live backend base URLs and Razorpay keys in each frontend.

## 10. Current Completion Notes

- Core response-envelope normalization was applied to auth, cart, checkout, payment, and order flows.
- Web cart, checkout, payment, and order clients are aligned to backend envelopes.
- Mobile cart, checkout, payment, and order clients are aligned to backend envelopes.
- Delivery pincode management is backend-owned through `/api/v1/admin/delivery/pincodes`.
- Operational order status changes are backend-owned through `/api/v1/orders/admin/{order_id}/status`.
- Admin finance summary is exposed through `/api/v1/orders/admin/dashboard/summary`.
- Remaining non-core modules such as support, reviews, and full admin management still need the same envelope and authorization standard applied consistently service by service before a full production launch.
