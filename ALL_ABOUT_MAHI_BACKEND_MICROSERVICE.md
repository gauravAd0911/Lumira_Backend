# ALL_ABOUT_MAHI_BACKEND_MICROSERVICE.md

## Backend System Overview

### Business Purpose
The Lumia Backend is a comprehensive FastAPI-based microservices architecture powering a D2C (Direct-to-Consumer) e-commerce platform specializing in skin care products. The system handles the complete customer journey from user registration through product browsing, shopping cart management, checkout, payment processing, order fulfillment, and post-purchase support.

### Overall Architecture
The backend follows a **microservices architecture** with 11 independent services, each deployed on separate ports (8001-8014). Each service owns its data and APIs, communicating primarily through synchronous HTTP REST calls with some asynchronous event-driven patterns (transactional outbox in Review Service).

**Key Architectural Characteristics:**
- **Service-Oriented Design**: Each service manages a specific business capability
- **Synchronous Inter-Service Communication**: HTTP REST for real-time interactions
- **Event-Driven Patterns**: Transactional outbox pattern for event dispatch
- **Multiple Authentication Models**: JWT tokens for authenticated users, OTP-based verification for guests
- **Distributed Checkout**: Guest and authenticated checkout flows with dual-channel OTP verification
- **Razorpay Integration**: Payment processing with webhook support
- **Multi-Channel Notifications**: Email (SendGrid/SMTP), SMS (Twilio), WhatsApp (Meta), in-app push

### Microservice Ecosystem

| Service | Port | Database | Purpose |
| --- | ---: | --- | --- |
| Auth | 8001 | `auth_m2_db` | Signup/login OTP, JWT sessions, password reset |
| Catalog | 8014 | `abt_dev` | Products, categories, storefront/admin catalog APIs |
| Cart | 8000 | `ecommerce_db` | Guest/user carts and cart pricing |
| Inventory | 8002 | `inventory_db` | Stock checks and optional reservations |
| Checkout | 8003 | `abt_dev` | Checkout validation, delivery checks, guest OTP, guest orders |
| Payment | 8006 | `payments_db` | Razorpay order/intent creation, verification, webhooks |
| Order | 8007 | `abt_dev` | Authenticated order creation/history/tracking |
| Notification | 8008 | `abt_dev` | Devices, in-app notifications, email, WhatsApp, SMS |
| Profile | 8009 | `user_profile_service` | User profile and persistent address book |
| Support | 8010 | `abt_dev` | Customer support tickets/queries |
| Reviews | 8012 | `review_service` | Product reviews and verified-review checks |

### Service Responsibilities
- **Auth Service**: Manages user lifecycle, authentication, and authorization
- **Catalog Service**: Product catalog management and storefront APIs
- **Cart Service**: Shopping cart persistence and management
- **Inventory Service**: Stock level management and reservations
- **Checkout Service**: Order validation and guest checkout flow
- **Payment Service**: Razorpay payment gateway integration
- **Order Service**: Order creation and management
- **Notification Service**: Multi-channel communication dispatch
- **Profile Service**: User profile and address management
- **Support Service**: Customer support ticket system
- **Review Service**: Product reviews with verification

### High-Level Request Lifecycle

#### Authenticated Customer Flow
1. **Registration/Login** → Auth Service creates JWT session
2. **Browse Products** → Catalog Service provides product data
3. **Add to Cart** → Cart Service stores items
4. **Checkout** → Checkout Service validates cart/inventory/delivery
5. **Payment** → Payment Service creates Razorpay order
6. **Order Creation** → Order Service persists order after payment verification
7. **Notifications** → Notification Service sends confirmations

#### Guest Checkout Flow
1. **Submit Email/Phone** → Checkout Service initiates dual OTP verification
2. **Verify Email OTP** → Checkout Service marks email verified
3. **Verify WhatsApp OTP** → Checkout Service issues session token
4. **Place Order** → Checkout Service creates guest order
5. **Payment & Notification** → Same as authenticated flow

### Service-to-Service Communication
- **Synchronous**: HTTP REST calls between services (Order→Payment, Checkout→Order)
- **Asynchronous**: Transactional outbox pattern (Review Service events)
- **Shared Databases**: Multiple services share `abt_dev` database
- **No Message Queues**: Current implementation uses direct HTTP calls

### Shared Infrastructure
- **Database**: MySQL 8+ across all services
- **Language**: Python 3.10+ with FastAPI framework
- **Authentication**: JWT tokens with refresh token rotation
- **OTP Delivery**: Twilio (SMS), Meta (WhatsApp)
- **Payment Gateway**: Razorpay with webhook verification
- **Email**: SendGrid primary, SMTP fallback

### Database Architecture
- **Distributed Databases**: 6 separate MySQL databases
- **Shared Schema**: `abt_dev` used by 4 services (Checkout, Order, Notification, Support)
- **Service Isolation**: Each service owns its primary data
- **Shadow Tables**: Review Service maintains copies of user/product/order data

### Async/Event-Driven Architecture
- **Transactional Outbox**: Review Service uses outbox pattern for event dispatch
- **Background Workers**: Outbox relay worker polls and publishes events
- **Future-Ready**: Architecture designed for message broker integration (RabbitMQ/Kafka)

### Third-Party Integrations
- **Razorpay**: Payment processing and webhooks
- **Twilio**: SMS and WhatsApp OTP delivery
- **Meta Cloud API**: WhatsApp business messaging
- **SendGrid**: Email notifications
- **SMTP**: Email fallback mechanism

### Deployment Strategy Overview
- **Local Development**: Individual service startup with `uvicorn`
- **Port Distribution**: Fixed ports per service (8001-8014)
- **Environment Variables**: Service-specific configuration
- **Database Setup**: Individual schema files per service
- **No Containerization**: Current setup uses virtual environments

## How To Run Entire Backend Locally

### Prerequisites
- **Python 3.10+**: All services require Python 3.10 or higher
- **MySQL 8+**: Database server with MySQL 8.0 or later
- **Git**: For cloning repositories (if applicable)
- **Virtual Environment**: Python venv for dependency isolation

### Language/Runtime Versions
- **Python**: 3.10+ (tested with 3.10, 3.11)
- **FastAPI**: 0.111.0 to 0.116.1 (varies by service)
- **SQLAlchemy**: 2.0+ (ORM for database operations)
- **PyMySQL**: 1.1.1 (MySQL driver)
- **Uvicorn**: ASGI server for FastAPI

### Docker Setup (Not Currently Implemented)
The current codebase does not include Docker configuration. For production deployment, each service would need:
- `Dockerfile` with Python base image
- `docker-compose.yml` for local orchestration
- Multi-stage builds for optimized images

### Kubernetes Setup (Not Currently Implemented)
For production scaling:
- **Service Deployment**: Individual deployments per microservice
- **ConfigMaps**: Environment variable management
- **Secrets**: Secure credential storage
- **Ingress**: API gateway and load balancing
- **Service Mesh**: Istio or Linkerd for service communication

### Environment Variables Setup
Each service requires a `.env` file with database credentials and API keys:

```env
# Common Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=service_specific_db

# Service-Specific Variables
JWT_SECRET=your_jwt_secret_key
RAZORPAY_KEY=rzp_live_your_key
RAZORPAY_SECRET=your_secret
TWILIO_ACCOUNT_SID=your_sid
# ... etc
```

### Service Startup Order
Due to inter-service dependencies, start services in this order:

1. **Auth Service** (Port 8001) - Foundation for user management
2. **Catalog Service** (Port 8014) - Products and categories
3. **Cart Service** (Port 8000) - Shopping cart functionality
4. **Inventory Service** (Port 8002) - Stock management
5. **Payment Service** (Port 8006) - Payment processing
6. **Checkout Service** (Port 8003) - Order validation
7. **Order Service** (Port 8007) - Order management
8. **Notification Service** (Port 8008) - Communication
9. **Profile Service** (Port 8009) - User profiles
10. **Support Service** (Port 8010) - Customer support
11. **Review Service** (Port 8012) - Product reviews

### Local Dependencies
- **MySQL Server**: Running on localhost:3306
- **Database Creation**: Run schema.sql files for each service
- **Python Dependencies**: Install from requirements.txt
- **Network Ports**: Ensure ports 8000-8014 are available

### Redis/Kafka/RabbitMQ Setup (Not Currently Used)
The current implementation does not use message queues or Redis. For future scalability:
- **Redis**: Could be added for caching and session storage
- **RabbitMQ/Kafka**: For event-driven communication to replace HTTP calls

### DB Setup
Run schema files in order:
```sql
-- Auth Service
mysql -u root -p < Auther_M2/Auther_M/schema.sql

-- Other services
mysql -u root -p < catalog_services/schema.sql
# ... etc for each service
```

### Migration Setup
- **Alembic**: Used in Auth and Inventory services
- **Manual Schema**: Most services use raw SQL schema files
- **Migration Order**: Run after database creation

### Secrets/Configuration Handling
- **Environment Variables**: All secrets stored in .env files
- **Development Mode**: OTP codes revealed in responses (disable for production)
- **Production Security**: Move secrets to secure vaults (HashiCorp Vault, AWS Secrets Manager)

### Common Startup Failures

#### Port Conflicts
**Symptoms**: "Address already in use" error
**Cause**: Another service or application using the port
**Solution**: 
```bash
# Check what's using the port
netstat -ano | findstr :8001
# Kill the process or change port in service config
```

#### Database Connection Issues
**Symptoms**: "Can't connect to MySQL server"
**Cause**: MySQL not running or wrong credentials
**Solution**:
```bash
# Start MySQL service
sudo systemctl start mysql  # Linux
# or
net start mysql            # Windows

# Verify credentials in .env file
```

#### Missing Dependencies
**Symptoms**: "ModuleNotFoundError"
**Cause**: requirements.txt not installed
**Solution**:
```bash
cd service_directory
pip install -r requirements.txt
```

#### Environment Variables Missing
**Symptoms**: "KeyError" or None values in config
**Cause**: .env file not created or incomplete
**Solution**: Copy .env.example to .env and fill values

#### Migration Issues
**Symptoms**: "Table doesn't exist" errors
**Cause**: Database schema not applied
**Solution**:
```bash
# For services with Alembic
alembic upgrade head

# For services with schema.sql
mysql -u root -p db_name < schema.sql
```

## Microservice Discovery

### Auth Service (Port 8001)

#### Business Purpose
The Auth Service manages the complete user lifecycle including registration, authentication, session management, and password recovery. It serves as the foundation for user identity across the entire platform.

#### Responsibilities
- User registration with OTP verification
- Login authentication with OTP
- JWT token generation and refresh
- Password reset flows
- Employee account management
- Session revocation and security

#### Service Dependencies
- **Called By**: All other services (for user authentication)
- **Calls**: None (standalone authentication service)
- **Communication**: Provides JWT tokens to other services

#### Entry Points
- **Main Application**: `Auther_M2/Auther_M/auth/main.py`
- **Server Bootstrap**: FastAPI app with CORS middleware
- **Route Registration**: `/api/v1/auth/*` endpoints
- **Worker Startup**: None (synchronous service)

#### Folder Structure
- `main.py`: FastAPI application setup
- `middleware/`: Authentication guards
- `models/`: User and employee data models
- `routes/`: API endpoint definitions
- `schemas/`: Pydantic request/response models
- `services/`: Business logic (auth, OTP, session management)
- `utils/`: Password hashing, token utilities
- `templates/`: Email/SMS templates (if any)
- `static/`: Static assets

### Catalog Service (Port 8014)

#### Business Purpose
Manages the product catalog including products, categories, and storefront APIs for browsing and purchasing.

#### Responsibilities
- Product CRUD operations (admin)
- Category management
- Storefront product listing
- Product search and filtering
- Homepage banners

#### Service Dependencies
- **Called By**: Frontend, Cart Service, Checkout Service
- **Calls**: None
- **Communication**: Synchronous HTTP from other services

#### Entry Points
- **Main Application**: `catalog_services/app/main.py`
- **Routes**: `/api/v1/products`, `/api/v1/categories`, `/api/v1/admin/*`

### Cart Service (Port 8000)

#### Business Purpose
Manages shopping cart functionality for both authenticated users and guests.

#### Responsibilities
- Cart creation and management
- Add/remove/update cart items
- Guest cart persistence
- Cart merging (guest to authenticated)
- Cart pricing calculations

#### Service Dependencies
- **Called By**: Frontend, Checkout Service
- **Calls**: Catalog Service (for product details)

### Inventory Service (Port 8002)

#### Business Purpose
Manages product stock levels, reservations, and inventory tracking across warehouses.

#### Responsibilities
- Stock level monitoring
- Stock reservation during checkout
- Reservation expiration handling
- Stock deduction on order completion
- Inventory audit trail

#### Service Dependencies
- **Called By**: Checkout Service
- **Calls**: None

### Checkout Service (Port 8003)

#### Business Purpose
Handles order validation, delivery checks, and guest checkout flows with dual OTP verification.

#### Responsibilities
- Cart and inventory validation
- Delivery zone checking
- Guest checkout with email + WhatsApp OTP
- Address management for checkout
- Guest order placement and lookup

#### Service Dependencies
- **Called By**: Frontend
- **Calls**: Inventory Service, Order Service, Notification Service

### Payment Service (Port 8006)

#### Business Purpose
Integrates with Razorpay payment gateway for secure payment processing.

#### Responsibilities
- Payment order creation
- Payment verification
- Webhook handling
- Idempotent payment processing
- Payment event logging

#### Service Dependencies
- **Called By**: Checkout Service, Order Service
- **Calls**: Razorpay API

### Order Service (Port 8007)

#### Business Purpose
Manages order creation, history, and tracking for authenticated users and guest orders.

#### Responsibilities
- Order creation and persistence
- Order history and details
- Order status management
- Payment verification before order creation
- Guest order lookup

#### Service Dependencies
- **Called By**: Checkout Service, Frontend
- **Calls**: Payment Service

### Notification Service (Port 8008)

#### Business Purpose
Handles multi-channel notifications including email, SMS, WhatsApp, and in-app notifications.

#### Responsibilities
- Device registration for push notifications
- Email dispatch (SendGrid/SMTP)
- SMS delivery (Twilio)
- WhatsApp messaging (Meta API)
- In-app notification storage

#### Service Dependencies
- **Called By**: All services (for notifications)
- **Calls**: External APIs (SendGrid, Twilio, Meta)

### Profile Service (Port 8009)

#### Business Purpose
Manages user profiles and persistent address books for checkout and account management.

#### Responsibilities
- User profile updates
- Address book management
- Default address designation
- Profile data persistence

#### Service Dependencies
- **Called By**: Frontend, Checkout Service
- **Calls**: None

### Support Service (Port 8010)

#### Business Purpose
Provides customer support ticket system for queries and issue resolution.

#### Responsibilities
- Support ticket creation
- Ticket assignment and tracking
- Support channel information
- Resolution tracking

#### Service Dependencies
- **Called By**: Frontend
- **Calls**: None

### Review Service (Port 8012)

#### Business Purpose
Manages product reviews with verified purchaser validation and rating aggregation.

#### Responsibilities
- Review creation and management
- Verified purchaser checking
- Rating summary calculations
- Event-driven review notifications
- Review moderation

#### Service Dependencies
- **Called By**: Frontend
- **Calls**: None (uses outbox pattern for events)

## API Documentation

### Auth Service APIs

#### POST /api/v1/auth/signup/initiate
**Business Purpose**: Initiates user registration with OTP verification
**Called From**: Frontend registration form
**Authentication**: None required
**Request Payload**:
```json
{
  "email": "user@example.com",
  "phone": "+919876543210",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```
**Validation Rules**: Email format, phone format, password strength
**Business Meaning**: Email and phone become unique identifiers

**Request Lifecycle**:
1. Route → Controller
2. Validate request payload
3. Check for existing verified users
4. Create pending user record
5. Generate OTP context with expiration
6. Send SMS OTP via Twilio
7. Return success with context info

**Database Operations**:
- INSERT into users (pending state)
- INSERT into otp_contexts
- Uses auth_m2_db

**Success Response**:
```json
{
  "success": true,
  "message": "OTP sent successfully.",
  "data": {
    "user_id": "uuid",
    "otp_id": "uuid",
    "otp_expires_in_seconds": 300
  }
}
```

**Error Response**:
```json
{
  "success": false,
  "message": "Email already exists",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [{"field": "email", "message": "Email already registered"}]
  }
}
```

**Side Effects**:
- SMS sent to phone number
- User record created (unverified)
- OTP context stored with expiration

**Risks & Observations**:
- OTP sent immediately (no rate limiting beyond cooldown)
- User created before verification (potential spam accounts)
- No email OTP (only SMS for signup)

#### POST /api/v1/auth/signup/verify
**Business Purpose**: Completes registration by verifying OTP
**Request Payload**:
```json
{
  "user_id": "uuid",
  "otp_id": "uuid", 
  "otp_code": "123456"
}
```

**Database Operations**:
- SELECT otp_contexts for verification
- UPDATE users SET is_verified = true
- DELETE or mark otp_context as verified

#### POST /api/v1/auth/login/initiate
**Business Purpose**: Initiates login with OTP
**Request Payload**:
```json
{
  "identifier": "email@example.com or +91phone",
  "password": "password"
}
```

#### POST /api/v1/auth/login/verify
**Business Purpose**: Completes login with OTP verification
**Response**: JWT access + refresh tokens

#### POST /api/v1/auth/token/refresh
**Business Purpose**: Rotates refresh tokens for session extension
**Authentication**: Valid refresh token required

#### POST /api/v1/auth/logout
**Business Purpose**: Revokes user session
**Side Effects**: Sets revoked_at on auth_sessions table

### Catalog Service APIs

#### GET /api/v1/products
**Business Purpose**: Lists products for storefront
**Query Parameters**: page, limit, category_id, search
**Database Operations**: SELECT from products with JOIN to categories

#### GET /api/v1/products/{product_id}
**Business Purpose**: Get detailed product information
**Database Operations**: SELECT product with images and tags

#### POST /api/v1/admin/products
**Business Purpose**: Create new product (admin only)
**Authentication**: JWT with admin role
**Request Payload**: Full product data with images

### Cart Service APIs

#### GET /api/v1/cart
**Business Purpose**: Retrieve user's shopping cart
**Authentication**: JWT or X-User-Id header
**Database Operations**: SELECT cart + cart_items with product details

#### POST /api/v1/cart/items
**Business Purpose**: Add product to cart
**Request Payload**:
```json
{
  "product_id": 1,
  "quantity": 2
}
```

### Checkout Service APIs

#### POST /api/v1/checkout/validate
**Business Purpose**: Validate cart before payment
**Calls**: Inventory Service for stock check
**Database Operations**: Multiple validations across services

#### POST /api/v1/guest-checkout/request-verification
**Business Purpose**: Initiate guest checkout with dual OTP
**Request Payload**:
```json
{
  "email": "guest@example.com",
  "phone": "+919876543210",
  "guest_name": "John Doe"
}
```
**Side Effects**: Sends email OTP + WhatsApp OTP

#### POST /api/v1/guest-checkout/verify
**Business Purpose**: Verify individual OTP channel
**Request Payload**:
```json
{
  "session_id": "uuid",
  "channel": "email",
  "otp_code": "123456"
}
```

#### POST /api/v1/guest-orders
**Business Purpose**: Place guest order
**Authentication**: session_token from dual verification
**Side Effects**: Creates order, calls Payment Service, sends notifications

### Payment Service APIs

#### POST /api/v1/payments/orders
**Business Purpose**: Create Razorpay payment order
**Response**: Razorpay order ID and payment details

#### POST /api/v1/payments/verify
**Business Purpose**: Verify payment signature after completion
**Request Payload**: Razorpay signature components

### Order Service APIs

#### POST /api/v1/orders
**Business Purpose**: Create authenticated order
**Authentication**: JWT required
**Side Effects**: Calls Payment Service to verify payment before creation

#### GET /api/v1/orders
**Business Purpose**: List user's order history
**Authentication**: JWT required

### Notification Service APIs

#### POST /api/v1/notifications/devices/register
**Business Purpose**: Register device for push notifications
**Request Payload**:
```json
{
  "device_token": "fcm_token",
  "platform": "ios"
}
```

#### POST /api/v1/notifications/send
**Business Purpose**: Send notification (internal API)
**Called From**: Other services
**Channels**: email, sms, whatsapp, push

### Review Service APIs

#### POST /api/v1/reviews
**Business Purpose**: Create product review
**Authentication**: JWT required
**Validation**: Must be verified purchaser
**Side Effects**: Publishes review.created event to outbox

#### GET /api/v1/products/{product_id}/reviews
**Business Purpose**: List product reviews
**Database Operations**: SELECT with pagination

## Database & Schema Documentation

### Auth Service Database (auth_m2_db)

#### users Table
**Purpose**: Core user accounts for authentication and profile data
**Data Stored**: User identity, contact info, authentication credentials
**Columns**:
- id (CHAR(36) UUID, PRIMARY KEY)
- full_name (VARCHAR(255))
- email (VARCHAR(255), UNIQUE, INDEX)
- phone (VARCHAR(20), INDEX)
- password_hash (VARCHAR(255), NOT NULL)
- role (ENUM: admin, consumer, vendor, DEFAULT consumer)
- is_active (TINYINT, DEFAULT 1)
- is_verified (TINYINT, DEFAULT 0)
- created_at (DATETIME)
- updated_at (DATETIME)

**Relationships**: One-to-many with otp_contexts, auth_sessions, password_reset_tokens
**Data Flow**: 
- INSERT: User registration
- UPDATE: Profile updates, verification
- SELECT: Authentication, profile retrieval

**Query Patterns**: Lookup by email/phone for auth, list by role for admin

#### otp_contexts Table
**Purpose**: OTP verification states for signup/login/password reset
**Data Stored**: OTP lifecycle and verification attempts
**Columns**:
- id (CHAR(36) UUID, PRIMARY KEY)
- purpose (ENUM: signup, password_forgot)
- user_id (FK to users.id)
- email, phone (verification targets)
- otp_hash (VARCHAR(255), bcrypt hash)
- expires_at (DATETIME)
- resend_count (INT, DEFAULT 0)
- attempt_count (INT, DEFAULT 0)
- verified_at (DATETIME)
- revoked_at (DATETIME)

**Relationships**: FK to users
**Data Flow**: Created during OTP initiation, updated on verification attempts

#### auth_sessions Table
**Purpose**: JWT refresh token storage for session management
**Data Stored**: Active authentication sessions
**Columns**:
- id (CHAR(36) UUID, PRIMARY KEY)
- user_id (FK to users.id)
- refresh_token_hash (VARCHAR(255))
- revoked_at (DATETIME)
- created_at (DATETIME)
- last_used_at (DATETIME)

**Relationships**: FK to users
**Data Flow**: Created on login, revoked on logout

### Catalog Service Database (abt_dev)

#### products Table
**Purpose**: Product catalog with pricing and inventory info
**Data Stored**: Product details, pricing, availability
**Columns**:
- id (INT, PRIMARY KEY)
- category_id (FK)
- name, slug
- price, compare_at_price
- size, skin_type
- stock_quantity
- is_featured, is_active
- rating_average, rating_count

**Relationships**: FK to categories, one-to-many with product_images, product_tags
**Data Flow**: Admin CRUD operations, storefront queries

#### categories Table
**Purpose**: Product categorization hierarchy
**Data Stored**: Category tree structure
**Columns**:
- id (INT, PRIMARY KEY)
- name, slug
- description
- image_url
- parent_id (self-referencing)
- is_active, sort_order

### Cart Service Database (ecommerce_db)

#### carts Table
**Purpose**: Shopping cart containers
**Data Stored**: Cart ownership and metadata
**Columns**:
- id (INT, PRIMARY KEY)
- user_id (nullable for guests)
- is_active (TINYINT)
- created_at (DATETIME)

#### cart_items Table
**Purpose**: Individual cart line items
**Data Stored**: Product quantities in carts
**Columns**:
- id (INT, PRIMARY KEY)
- cart_id (FK)
- product_id (FK)
- quantity (INT)
- added_at (DATETIME)

**Relationships**: FK to carts and products
**Unique Constraint**: (cart_id, product_id)

### Inventory Service Database (inventory_db)

#### stock Table
**Purpose**: Current stock levels by product and warehouse
**Data Stored**: Available and reserved quantities
**Columns**:
- id (INT, PRIMARY KEY)
- product_id (FK)
- warehouse_id (FK)
- total_quantity (INT)
- reserved_quantity (INT)
- available_quantity (COMPUTED)

#### reservations Table
**Purpose**: Stock holds during checkout process
**Data Stored**: Temporary stock reservations with TTL
**Columns**:
- id (INT, PRIMARY KEY)
- product_id, warehouse_id (FKs)
- quantity (INT)
- status (ENUM: ACTIVE, COMMITTED, RELEASED, EXPIRED)
- expires_at (DATETIME)
- idempotency_key (VARCHAR)

### Payment Service Database (payments_db)

#### payments Table
**Purpose**: Payment transaction records
**Data Stored**: Razorpay payment states and metadata
**Columns**:
- id (INT, PRIMARY KEY)
- payment_reference (UUID)
- provider_order_id (Razorpay order ID)
- idempotency_key
- amount_minor (paise)
- status (ENUM: creating, created, pending, verified, failed)

#### payment_events Table
**Purpose**: Webhook event audit trail
**Data Stored**: Razorpay webhook payloads
**Columns**:
- id (INT, PRIMARY KEY)
- payment_id (FK)
- event_type (VARCHAR)
- signature_verified (TINYINT)
- payload (JSON)
- received_at (DATETIME)

### Order Service Database (abt_dev)

#### orders Table
**Purpose**: Order records for all purchases
**Data Stored**: Complete order information
**Columns**:
- id (INT, PRIMARY KEY)
- order_number (UNIQUE)
- user_id (nullable for guests)
- payment_reference
- total (DECIMAL)
- status (ENUM: PLACED, CONFIRMED, PACKED, SHIPPED, DELIVERED, CANCELLED)
- shipping_address (JSON)
- item_count (INT)

#### order_items Table
**Purpose**: Order line items (snapshots)
**Data Stored**: Product details at time of order
**Columns**:
- id (INT, PRIMARY KEY)
- order_id (FK)
- product_id
- product_name
- price (DECIMAL)
- quantity (INT)
- image_url

### Checkout Service Database (abt_dev)

#### guest_checkout_sessions Table
**Purpose**: Guest checkout verification state
**Data Stored**: Dual OTP verification progress
**Columns**:
- id (INT, PRIMARY KEY)
- guest_name, email, phone
- email_verified, sms_verified (TINYINT)
- session_token (VARCHAR)
- session_expires_at (DATETIME)

#### guest_otps Table
**Purpose**: Individual OTP verification records
**Data Stored**: OTP attempts and verification state
**Columns**:
- id (INT, PRIMARY KEY)
- session_id (FK)
- channel (ENUM: email, sms)
- otp_hash (VARCHAR)
- status (ENUM: PENDING, VERIFIED, EXPIRED)
- expires_at, verified_at
- attempt_count, resend_count

### Review Service Database (review_service)

#### reviews Table
**Purpose**: Product reviews and ratings
**Data Stored**: User reviews with verification status
**Columns**:
- review_id (CHAR(36) UUID, PRIMARY KEY)
- product_id (FK)
- user_id (FK)
- rating (TINYINT 1-5)
- title, body (TEXT)
- is_verified (TINYINT)
- status (ENUM: PUBLISHED, HIDDEN, DELETED)

**Unique Constraint**: (user_id, product_id) - one review per user per product

#### outbox_events Table
**Purpose**: Transactional outbox for event dispatch
**Data Stored**: Events to be published asynchronously
**Columns**:
- event_id (CHAR(36) UUID, PRIMARY KEY)
- event_type (VARCHAR)
- aggregate_id (review_id)
- payload (JSON)
- status (ENUM: PENDING, DISPATCHED, FAILED)

### Notification Service Database (abt_dev)

#### devices Table
**Purpose**: Push notification device registrations
**Data Stored**: FCM/APNS tokens for push delivery
**Columns**:
- id (INT, PRIMARY KEY)
- user_id (FK)
- device_token (VARCHAR)
- platform (ENUM: ios, android, web)

#### notifications Table
**Purpose**: In-app notification storage
**Data Stored**: User notifications with read status
**Columns**:
- id (INT, PRIMARY KEY)
- user_id (FK)
- title, message
- type (VARCHAR)
- is_read (TINYINT)

### Profile Service Database (user_profile_service)

#### app_users Table
**Purpose**: User profile data
**Data Stored**: Extended user information

#### addresses Table
**Purpose**: Persistent address book
**Data Stored**: Reusable delivery addresses
**Columns**:
- id (INT, PRIMARY KEY)
- user_id (FK)
- full_name, phone
- address_line1, address_line2
- city, state, postal_code, country
- address_type (ENUM: Home, Work, Other)
- is_default (TINYINT)

### Support Service Database (abt_dev)

#### support_tickets Table
**Purpose**: Customer support interactions
**Data Stored**: Support queries and resolutions
**Columns**:
- id (INT, PRIMARY KEY)
- user_id (nullable)
- name, email, phone
- message (TEXT)
- status (ENUM: open, pending, resolved, closed)
- priority (ENUM: low, medium, high)
- assigned_to_employee_id (FK)
- resolution_note (TEXT)

## Inter-Service Communication

### Service Communication Architecture

The backend uses a hybrid communication model combining synchronous HTTP REST calls with asynchronous event-driven patterns.

#### Synchronous Communication Patterns

**HTTP REST Calls**:
- **Order Service → Payment Service**: Fetch payment status before order creation
- **Checkout Service → Order Service**: Guest order lookup with internal token
- **Checkout Service → Inventory Service**: Stock availability validation
- **All Services → Notification Service**: Receive notifications to send

**Authentication for Service Calls**:
- Internal service token: `X-Internal-Token` header
- Example: Checkout → Order guest lookup uses `INTERNAL_SERVICE_TOKEN`

**Timeout Handling**:
- Default timeout: 5 seconds for inter-service calls
- No retry logic implemented
- Failures cascade to calling service

#### Asynchronous Communication Patterns

**Transactional Outbox Pattern (Review Service)**:
- Reviews create events in `outbox_events` table within same transaction
- Background worker polls for PENDING events
- Publishes to message broker (currently logs to console)
- Updates status to DISPATCHED or FAILED

**Worker Implementation**:
```python
class OutboxRelayWorker:
    async def start(self):
        while True:
            pending_events = self.get_pending_events()
            for event in pending_events:
                await self.publish_event(event)
            await asyncio.sleep(5)  # Poll interval
```

### Communication Flow Examples

#### Guest Checkout Flow
1. **Frontend → Checkout Service**: POST /guest-checkout/request-verification
2. **Checkout Service**: Creates session, sends dual OTP
3. **Frontend → Checkout Service**: POST /verify (email OTP)
4. **Frontend → Checkout Service**: POST /verify (WhatsApp OTP)
5. **Checkout Service**: Issues session_token
6. **Frontend → Checkout Service**: POST /guest-orders with session_token
7. **Checkout Service → Payment Service**: Create payment order
8. **Frontend**: Completes Razorpay payment
9. **Payment Service**: Receives webhook, verifies payment
10. **Checkout Service → Order Service**: Create guest order
11. **Order Service → Payment Service**: Verify payment status
12. **Order Service**: Creates order record
13. **Notification Service**: Sends confirmation emails/SMS

#### Order Creation Flow (Authenticated)
1. **Frontend → Order Service**: POST /orders with payment_reference
2. **Order Service → Payment Service**: GET payment status
3. **Payment Service**: Returns verified status
4. **Order Service**: Creates order in database
5. **Order Service → Notification Service**: Send order confirmation

### Failure Handling

**Timeout Handling**:
- Synchronous calls use 5-second timeout
- No circuit breaker implemented
- Failures result in 502 Bad Gateway responses

**Retry Logic**:
- Not implemented for HTTP calls
- Outbox pattern provides at-least-once delivery
- Failed events marked as FAILED, can be retried manually

**Idempotency**:
- Payment orders use Idempotency-Key header
- Prevents duplicate charges on retry

## Authentication & Authorization Flow

### Complete Authentication Flow

#### User Registration (OTP-Based)
1. **Initiate**: POST /signup/initiate
   - Validate email/phone uniqueness
   - Create pending user (is_verified=false)
   - Generate OTP context with 5-minute expiration
   - Send SMS OTP via Twilio
   - Return otp_id and user_id

2. **Verify**: POST /signup/verify
   - Validate OTP code against stored hash
   - Update user is_verified=true
   - Mark OTP context as verified
   - Return success (no tokens yet)

#### User Login (OTP-Based)
1. **Initiate**: POST /login/initiate
   - Validate identifier (email/phone) and password
   - Generate OTP context
   - Send SMS OTP
   - Return otp_id

2. **Verify**: POST /login/verify
   - Validate OTP code
   - Create JWT access token (15-minute expiry)
   - Create refresh token (7-day expiry)
   - Store refresh token hash in auth_sessions
   - Return access_token and refresh_token

#### Token Refresh
1. **Request**: POST /token/refresh with refresh_token
2. **Validate**: Check refresh token not revoked
3. **Rotate**: Issue new access + refresh token pair
4. **Revoke**: Mark old refresh token as used
5. **Return**: New token pair

#### Logout
1. **Request**: POST /logout with access_token
2. **Revoke**: Set revoked_at on auth_sessions record
3. **Invalidate**: All tokens from that session become invalid

### JWT Token Structure

**Access Token Payload**:
```json
{
  "sub": "user_id",
  "user_id": "uuid",
  "email": "user@example.com", 
  "role": "consumer",
  "type": "access",
  "iat": 1234567890,
  "exp": 1234567890 + 900  // 15 minutes
}
```

**Refresh Token Payload**:
```json
{
  "sub": "user_id",
  "type": "refresh",
  "iat": 1234567890,
  "exp": 1234567890 + 604800  // 7 days
}
```

### Authorization Patterns

**Role-Based Access**:
- **consumer**: Regular customers
- **vendor**: Employee/vendor accounts  
- **admin**: Administrative access

**Middleware Implementation**:
```python
def get_current_user(token: str) -> User:
    # Decode JWT
    # Verify signature with JWT_SECRET
    # Check expiration
    # Return User object from database
```

**Service-to-Service Authentication**:
- **X-Internal-Token**: Shared secret for internal calls
- Used in: Checkout → Order guest lookup

### Guest Authentication

**Session Token Flow**:
1. Dual OTP verification (email + WhatsApp)
2. Issue session_token (JWT-like, 30-minute expiry)
3. Store in guest_checkout_sessions
4. Use for order placement
5. Auto-expire after timeout

### Security Considerations

**Token Storage**:
- Access tokens: Client-side (localStorage/cookies)
- Refresh tokens: HttpOnly cookies or secure storage

**Session Management**:
- Refresh token rotation prevents compromise
- Immediate revocation on logout
- Session tracking with last_used_at

**OTP Security**:
- Hashed storage (bcrypt)
- 5-minute expiration
- Attempt limits (5 max)
- Resend cooldown (30 seconds)

**Common Auth Bugs**:
- Token not validated on each request
- Missing role checks on admin endpoints
- Guest session tokens not properly validated

## Configuration & Environment Variables

### Environment Variables Documentation

#### Database Configuration (All Services)
```
DB_HOST=localhost                    # MySQL server host
DB_USER=root                         # Database username  
DB_PASSWORD=your_password           # Database password
DB_NAME=service_specific_db         # Service database name
```

**Purpose**: Database connection configuration
**Security Impact**: Contains database credentials
**Required**: Yes for all services

#### JWT Configuration (Auth, Order Services)
```
JWT_SECRET=your_secret_key_here     # JWT signing secret
```

**Purpose**: Token signing and verification
**Security Impact**: Compromised secret allows token forgery
**Required**: Yes for auth-dependent services

#### Payment Configuration (Payment Service)
```
RAZORPAY_KEY=rzp_live_...           # Razorpay public key
RAZORPAY_SECRET=...                 # Razorpay secret key
RAZORPAY_WEBHOOK_SECRET=...         # Webhook signature verification
```

**Purpose**: Payment gateway integration
**Security Impact**: Allows payment processing
**Required**: Yes for payment features

#### Communication Configuration (Notification Service)
```
SENDGRID_API_KEY=...                # Email service API key
SMTP_HOST=smtp.gmail.com            # Fallback email host
SMTP_USER=...                       # SMTP username
SMTP_PASSWORD=...                   # SMTP password
TWILIO_ACCOUNT_SID=...              # SMS/WhatsApp account
TWILIO_AUTH_TOKEN=...               # Twilio auth token
WHATSAPP_ACCESS_TOKEN=...           # Meta WhatsApp API
WHATSAPP_PHONE_NUMBER_ID=...        # WhatsApp business ID
```

**Purpose**: Multi-channel notification delivery
**Security Impact**: Allows sending communications
**Required**: Yes for notifications

#### OTP Configuration (Checkout Service)
```
OTP_VALIDITY_SECONDS=300           # OTP expiration (5 min)
OTP_MAX_RESENDS=3                   # Max resend attempts
OTP_MAX_ATTEMPTS=5                  # Max verification attempts
OTP_RESEND_COOLDOWN_SECONDS=30      # Cooldown between resends
```

**Purpose**: OTP security and usability settings
**Security Impact**: Prevents brute force attacks
**Required**: No (defaults provided)

#### Inventory Configuration (Inventory Service)
```
ENABLE_STOCK_RESERVATION=false      # Feature flag
DEDUCT_STOCK_ON_ORDER=true          # MVP behavior
RESERVATION_TTL_SECONDS=900         # Reservation timeout (15 min)
```

**Purpose**: Stock management behavior
**Security Impact**: Affects inventory integrity
**Required**: No (defaults provided)

#### CORS Configuration (All Services)
```
ALLOWED_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]
```

**Purpose**: Cross-origin request permissions
**Security Impact**: Restricts frontend access
**Required**: Yes for web applications

### Secrets Management

**Current Implementation**:
- All secrets stored in `.env` files
- Files committed to version control (security risk)
- No encryption or secure storage

**Production Requirements**:
- HashiCorp Vault or AWS Secrets Manager
- Environment-specific secret rotation
- Principle of least privilege

### Configuration Loading Flow

**Service Startup**:
1. Load `.env` file with `python-dotenv`
2. Override with system environment variables
3. Validate required configuration
4. Initialize database connections
5. Start FastAPI application

**Configuration Validation**:
- Required fields checked on startup
- Missing config causes immediate failure
- No runtime config reloading

### Environment Separation

**Development**:
- Local MySQL databases
- Debug logging enabled
- OTP codes revealed in responses
- CORS allows localhost origins

**Production**:
- External database hosts
- Secure logging (no sensitive data)
- OTP codes hidden
- Restricted CORS origins
- HTTPS enforcement required

## Background Jobs & Schedulers

### Outbox Relay Worker (Review Service)

**Purpose**: Asynchronous event dispatch using transactional outbox pattern

**Trigger Condition**: Service startup (lifespan event)

**Business Purpose**: 
- Publish review events without blocking review creation
- Ensure at-least-once delivery of events
- Decouple event publishing from business logic

**Database Impact**:
- Polls `outbox_events` table for PENDING status
- Updates status to DISPATCHED or FAILED
- No modifications to review data

**Failure Handling**:
- Exceptions logged but don't stop worker
- Failed events marked as FAILED
- Manual retry possible by resetting status

**Retry Logic**: 
- Continuous polling (5-second intervals)
- Failed events remain in FAILED status
- No automatic retry (manual intervention required)

### No Traditional Job Queues

**Current State**: No Celery, RQ, or APScheduler implemented

**Future Requirements**:
- Order status updates (automated shipping notifications)
- Cart cleanup (expired guest carts)
- Failed payment retry logic
- Email/SMS campaign scheduling

**Recommended Implementation**:
- Celery with Redis broker
- Scheduled tasks for cleanup operations
- Dead letter queues for failed jobs

## Debugging & Production Support Guide

### How To Debug Backend

#### Tracing Request Lifecycle

**API Request Flow**:
1. **Client Request** → Nginx/Load Balancer
2. **Service Routing** → FastAPI route handler
3. **Authentication** → JWT validation middleware
4. **Validation** → Pydantic model validation
5. **Business Logic** → Service layer processing
6. **Database** → SQLAlchemy ORM queries
7. **External Calls** → HTTP requests to other services
8. **Response** → JSON serialization

**Debug Points**:
- Add logging at each layer
- Use request IDs for tracing
- Check database query logs
- Monitor inter-service calls

#### Debugging Database Queries

**Enable SQL Logging**:
```python
# In database.py
engine = create_engine(
    DATABASE_URL,
    echo=True  # Logs all SQL queries
)
```

**Common Issues**:
- N+1 query problems in loops
- Missing indexes causing slow queries
- Connection pool exhaustion
- Transaction deadlocks

**Debug Tools**:
- MySQL slow query log
- SQLAlchemy query profiling
- Database monitoring dashboards

#### Debugging Auth Failures

**JWT Token Issues**:
- Check token expiration (15-minute access, 7-day refresh)
- Verify JWT_SECRET consistency across services
- Validate token signature

**OTP Issues**:
- Check Twilio delivery status
- Verify OTP hash comparison
- Check attempt/resend limits

**Session Issues**:
- Check revoked_at in auth_sessions
- Verify refresh token rotation

#### Debugging Inter-Service Failures

**HTTP Call Debugging**:
```python
# Add logging to service calls
response = requests.get(url, timeout=5)
logger.info(f"Service call: {url} -> {response.status_code}")
```

**Common Issues**:
- Service down (check port availability)
- Network connectivity
- Invalid internal tokens
- Timeout issues (5-second default)

#### Debugging Queue Issues

**Outbox Debugging**:
- Check outbox_events table status
- Verify worker is running
- Check broker connectivity
- Monitor dispatch failures

#### Debugging Async Jobs

**Worker Debugging**:
- Check asyncio task status
- Monitor exception logs
- Verify database connectivity
- Check polling intervals

#### Important Log Files

**Service Logs**:
- FastAPI access logs (requests/responses)
- SQLAlchemy query logs
- External API call logs
- Error/exception traces

**Database Logs**:
- MySQL general query log
- MySQL slow query log
- MySQL error log

**External Service Logs**:
- Twilio SMS delivery logs
- SendGrid email delivery logs
- Razorpay webhook logs

#### Tracing IDs

**Request Tracing**:
- Generate UUID for each request
- Pass in X-Request-ID header
- Log with all operations
- Include in error responses

**Implementation**:
```python
import uuid
request_id = str(uuid.uuid4())
logger.info(f"Request {request_id}: Processing...")
```

#### Monitoring Tools

**Application Metrics**:
- Response times per endpoint
- Error rates by service
- Database connection pool usage
- Memory/CPU usage per service

**Business Metrics**:
- Order conversion rates
- Payment success rates
- OTP verification success rates
- Cart abandonment rates

#### Health Check Endpoints

**Service Health**:
- GET /health - Basic health check
- GET /ready - Readiness probe
- GET /metrics - Prometheus metrics

**Database Health**:
- Connection pool status
- Query performance metrics
- Table sizes and growth

## Code Review & Engineering Audit

### High Risk Issues

#### 1. Hard-Coded Service URLs
**Location**: `order_services_/app/api/order_routes.py`
**Risk**: Production deployments require different URLs
**Impact**: Service communication failures in non-local environments
**Fix**: Use environment variables or service discovery

#### 2. No Circuit Breaker Pattern
**Risk**: Cascading failures when services are down
**Impact**: Single service failure brings down dependent services
**Fix**: Implement Pybreaker or similar circuit breaker

#### 3. Blocking Inter-Service Calls
**Location**: Synchronous `requests.get()` calls
**Risk**: Thread pool exhaustion under load
**Impact**: Degraded performance, timeouts
**Fix**: Use async HTTP client (httpx) or message queues

#### 4. Missing Transaction Boundaries
**Risk**: Partial updates on failures
**Impact**: Data inconsistency
**Fix**: Wrap multi-step operations in transactions

#### 5. No Rate Limiting on OTP Endpoints
**Risk**: Brute force attacks on OTP verification
**Impact**: Account takeover, service abuse
**Fix**: Implement rate limiting (Redis-based)

### Medium Risk Issues

#### 6. Password Reset Flow Incomplete
**Missing**: Token validation endpoint
**Risk**: Password reset cannot be completed
**Impact**: Users cannot recover accounts
**Fix**: Implement `/password-reset/validate-token` endpoint

#### 7. No Input Validation Between Services
**Risk**: Invalid data passed between services
**Impact**: Runtime errors, data corruption
**Fix**: Add request validation on all service endpoints

#### 8. Missing Database Indexes
**Location**: Various tables lack performance indexes
**Risk**: Slow queries under load
**Impact**: Performance degradation
**Fix**: Add indexes on frequently queried columns

#### 9. Inconsistent Error Handling
**Risk**: Different error formats across services
**Impact**: Poor API consumer experience
**Fix**: Standardize error response format

### Low Risk Issues

#### 10. Dead Code
**Location**: Unused imports, commented code
**Impact**: Code maintainability
**Fix**: Remove unused code

#### 11. Hardcoded Configuration
**Location**: Magic numbers, default values
**Impact**: Configuration inflexibility
**Fix**: Move to environment variables

#### 12. Missing API Documentation
**Impact**: Developer experience
**Fix**: Add comprehensive OpenAPI docs

### Database Design Issues

#### 13. No Foreign Key Constraints Between Services
**Risk**: Data integrity issues
**Impact**: Orphaned records, inconsistent data
**Fix**: Consider data consistency patterns (sagas, event sourcing)

#### 14. Denormalized Shared Tables
**Location**: `abt_dev` shared by multiple services
**Risk**: Tight coupling between services
**Impact**: Deployment coordination issues
**Fix**: Evaluate service boundaries

### Security Issues

#### 15. Secrets in Version Control
**Location**: `.env` files potentially committed
**Risk**: Credential exposure
**Impact**: Security breaches
**Fix**: Use secret management systems

#### 16. No HTTPS Enforcement
**Risk**: Man-in-the-middle attacks
**Impact**: Data interception
**Fix**: Enforce HTTPS in production

## New Developer Onboarding Guide

### Recommended Learning Order

1. **Start with Auth Service**: Understand user lifecycle and JWT authentication
2. **Catalog Service**: Learn product data models and CRUD operations
3. **Cart Service**: Understand session management and cart persistence
4. **Checkout Service**: Complex business logic with dual OTP verification
5. **Payment Service**: External API integration and webhook handling
6. **Order Service**: Transaction management and inter-service communication
7. **Review Service**: Event-driven architecture and outbox pattern
8. **Notification Service**: Multi-channel communication patterns
9. **Inventory Service**: Stock management and reservation logic
10. **Profile/Support Services**: Simpler CRUD operations

### Before Making Changes

**High-Risk Services**:
- Auth Service: Affects all user authentication
- Payment Service: Financial transactions
- Checkout Service: Complex business logic

**Shared Libraries**: None identified (each service independent)

**Migration Precautions**:
- Database schema changes require coordination
- Test migrations on staging environment first
- Backup data before schema changes

**API Contract Risks**:
- Changes to request/response formats break frontend
- Version APIs when making breaking changes
- Document all API changes

**Database Modification Risks**:
- Shared tables (`abt_dev`) affect multiple services
- Index changes impact query performance
- Data type changes may cause data loss

### Safe Development Practices

**Service Isolation**:
- Develop services independently
- Use local databases for development
- Mock external service calls when possible

**DTO Validation**:
- Use Pydantic models for all request/response data
- Validate data at service boundaries
- Return detailed validation errors

**Transaction Handling**:
- Wrap multi-step operations in transactions
- Handle rollback on failures
- Avoid long-running transactions

**Logging Standards**:
- Log all API requests with request IDs
- Include user context in logs
- Log errors with full stack traces
- Never log sensitive data (passwords, tokens)

**Error Handling Standards**:
- Use consistent error response format
- Return appropriate HTTP status codes
- Include error codes for programmatic handling
- Log errors for debugging

**API Response Conventions**:
- Use standardized response wrapper
- Include success/message/data fields
- Return detailed error information
- Maintain backward compatibility

### How To Add New Microservice

1. **Create Service Structure**:
   - Create new directory with service name
   - Set up Python virtual environment
   - Initialize FastAPI application
   - Create basic folder structure (main.py, routes/, models/, etc.)

2. **Setup Routes**:
   - Define API endpoints in routes/
   - Implement request/response models
   - Add authentication middleware if needed
   - Create OpenAPI documentation

3. **Configure Database**:
   - Create database schema file
   - Set up SQLAlchemy models
   - Configure database connection
   - Run initial migrations

4. **Register Service Discovery**:
   - Add service URL to environment variables
   - Update dependent services with new URLs
   - Add health check endpoints

5. **Add Authentication**:
   - Integrate JWT validation if needed
   - Add role-based access control
   - Implement service-to-service tokens

6. **Setup Logging**:
   - Configure structured logging
   - Add request tracing
   - Set up log aggregation

7. **Add Health Checks**:
   - Implement /health endpoint
   - Add database connectivity checks
   - Include dependency health checks

8. **Dockerize Service**:
   - Create Dockerfile
   - Add docker-compose configuration
   - Configure environment variables

9. **Deployment Setup**:
   - Add Kubernetes manifests
   - Configure CI/CD pipelines
   - Set up monitoring and alerting

## Final Engineering Summary

### Microservice Dependency Map

```
Auth Service
├── Called by: All services (authentication)
└── Calls: None

Catalog Service  
├── Called by: Frontend, Cart, Checkout
└── Calls: None

Cart Service
├── Called by: Frontend, Checkout
└── Calls: Catalog (product details)

Inventory Service
├── Called by: Checkout
└── Calls: None

Checkout Service
├── Called by: Frontend
└── Calls: Inventory, Order, Payment, Notification

Payment Service
├── Called by: Checkout, Order
└── Calls: Razorpay API

Order Service
├── Called by: Checkout, Frontend
└── Calls: Payment

Notification Service
├── Called by: All services
└── Calls: SendGrid, Twilio, Meta APIs

Profile Service
├── Called by: Frontend, Checkout
└── Calls: None

Support Service
├── Called by: Frontend
└── Calls: None

Review Service
├── Called by: Frontend
└── Calls: None (outbox events)
```

### Shared Libraries List
- None identified (each service has independent dependencies)

### Common Utilities List
- JWT token utilities (auth services)
- Password hashing (bcrypt)
- OTP generation and validation
- Database connection pooling
- HTTP client for inter-service calls
- Standardized response formatting

### Dead Code List
- Unused imports in various services
- Commented-out code blocks
- Empty exception handlers
- Unreachable code paths

### Duplicate Logic List
- Response formatting (should be standardized)
- Error handling patterns
- Database connection setup
- JWT validation middleware

### Missing Validations
- Input sanitization on all endpoints
- Rate limiting on public APIs
- Request size limits
- SQL injection prevention (ORM handles this)

### Missing Error Handling
- Database connection failures
- External API timeouts
- Invalid JWT tokens
- Malformed request payloads

### Technical Debt
- Inconsistent code formatting
- Mixed sync/async patterns
- Hardcoded configuration values
- Lack of comprehensive testing

### Refactor Opportunities
- Extract common utilities to shared library
- Standardize API response formats
- Implement circuit breaker pattern
- Add comprehensive input validation

### Scalability Risks
- Synchronous inter-service calls
- Shared database tables
- No horizontal scaling configuration
- Single points of failure

### Security Risks
- Secrets in version control
- No rate limiting
- No HTTPS enforcement
- Insufficient input validation

### Performance Bottlenecks
- N+1 query issues
- Missing database indexes
- Blocking HTTP calls
- No caching layer

### Database Design Issues
- No foreign keys between services
- Denormalized shared tables
- Missing constraints
- Inconsistent naming conventions

### Production Readiness Score: 6/10
- ✅ Microservices architecture
- ✅ Database isolation
- ✅ JWT authentication
- ✅ Payment integration
- ⚠️ No monitoring/observability
- ⚠️ No automated testing
- ⚠️ No CI/CD pipelines
- ⚠️ Secrets management issues
- ⚠️ No horizontal scaling
- ⚠️ Synchronous communication bottlenecks

### Maintainability Score: 7/10
- ✅ Clear service boundaries
- ✅ FastAPI framework
- ✅ SQLAlchemy ORM
- ✅ OpenAPI documentation
- ⚠️ Inconsistent code patterns
- ⚠️ Technical debt accumulation
- ⚠️ Limited automated testing

### Scalability Score: 5/10
- ✅ Microservices design
- ✅ Database per service
- ⚠️ Synchronous communication
- ⚠️ Shared database tables
- ⚠️ No load balancing
- ⚠️ No container orchestration

### Security Score: 6/10
- ✅ JWT authentication
- ✅ Password hashing
- ✅ Role-based access
- ⚠️ Secrets in code
- ⚠️ No rate limiting
- ⚠️ No HTTPS enforcement
- ⚠️ Missing input validation

### Reliability Score: 7/10
- ✅ Transaction handling
- ✅ Error response standardization
- ✅ OTP security measures
- ⚠️ No circuit breakers
- ⚠️ Synchronous failure cascades
- ⚠️ No retry mechanisms