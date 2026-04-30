ðŸ›’ Ecommerce Cart API
A production-ready FastAPI + MySQL shopping cart service.

ðŸ“ Project Structure
ecommerce-cart/
â”œâ”€â”€ app/
â”‚   â”œâ”€â”€ main.py                  # FastAPI app entry point
â”‚   â”œâ”€â”€ core/
â”‚   â”‚   â”œâ”€â”€ config.py            # App settings (env vars)
â”‚   â”‚   â””â”€â”€ database.py          # SQLAlchemy engine & session
â”‚   â”œâ”€â”€ models/
â”‚   â”‚   â””â”€â”€ models.py            # ORM: Product, Cart, CartItem
â”‚   â”œâ”€â”€ schemas/
â”‚   â”‚   â””â”€â”€ schemas.py           # Pydantic request/response models
â”‚   â””â”€â”€ routers/
â”‚       â”œâ”€â”€ cart.py              # All 5 Cart endpoints
â”‚       â””â”€â”€ products.py          # Product CRUD (for testing)
â”œâ”€â”€ ecommerce_cart_full.sql                     # Sample product data
â”œâ”€â”€ alembic.ini                  # DB migrations config
â”œâ”€â”€ requirements.txt
â””â”€â”€ .env.example                 # Environment variable template

âš™ï¸ Setup
1. Clone & Install
bashgit clone <your-repo>
cd ecommerce-cart
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
2. Configure Environment
bashcp .env.example .env
# Edit .env with your MySQL credentials
envDB_HOST=localhost
DB_PORT=3306
DB_NAME=ecommerce_db
DB_USER=root
DB_PASSWORD=yourpassword
3. Create the Database
bashmysql -u root -p -e "CREATE DATABASE ecommerce_db CHARACTER SET utf8mb4;"
4. Start the Server
bashuvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Tables are auto-created on first startup.
5. Seed Sample Products (optional)
bashmysql -u root -p ecommerce_db < ecommerce_cart_full.sql

ðŸ—„ï¸ Database Schema
products         carts            cart_items
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€       â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€       â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
id (PK)          id (PK)          id (PK)
name             user_id          cart_id (FKâ†’carts)
description      is_active        product_id (FKâ†’products)
price            created_at       quantity
stock            updated_at       added_at
image_url                         updated_at
is_active                         UNIQUE(cart_id, product_id)
created_at
updated_at

ðŸ”Œ API Endpoints
Authentication
Pass X-User-Id header to identify the user.
Replace with JWT middleware in production.

Cart Endpoints
GET /api/cart
Fetch the active cart for the current user.
bashcurl -X GET http://localhost:8000/api/cart \
  -H "X-User-Id: user_123"
Response:
json{
  "id": 1,
  "user_id": "user_123",
  "is_active": true,
  "items": [...],
  "total_items": 3,
  "total_price": 1499.97,
  "created_at": "...",
  "updated_at": "..."
}

POST /api/cart/items
Add a product to the cart. Increments quantity if already present.
bashcurl -X POST http://localhost:8000/api/cart/items \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user_123" \
  -d '{"product_id": 1, "quantity": 2}'

PUT /api/cart/items/{product_id}
Set the exact quantity for a cart item.
bashcurl -X PUT http://localhost:8000/api/cart/items/1 \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user_123" \
  -d '{"quantity": 5}'

DELETE /api/cart/items/{product_id}
Remove a specific item from the cart.
bashcurl -X DELETE http://localhost:8000/api/cart/items/1 \
  -H "X-User-Id: user_123"

DELETE /api/cart
Clear all items from the cart.
bashcurl -X DELETE http://localhost:8000/api/cart \
  -H "X-User-Id: user_123"

ðŸ“– Interactive Docs
URLDescriptionhttp://localhost:8000/docsSwagger UIhttp://localhost:8000/redocReDoc

ðŸ”’ Production Checklist

 Replace X-User-Id header with JWT authentication middleware
 Set DEBUG=False in .env
 Restrict CORS origins to your frontend domain
 Use environment secrets manager (not .env file)
 Enable MySQL SSL connections
 Add rate limiting (e.g. slowapi)
 Set up Alembic for schema migrations
 Add unit & integration tests
