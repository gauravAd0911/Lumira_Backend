# Order Service

FastAPI service for order placement, tracking, and order history.

## What was fixed

- The API now creates missing database tables on startup.
- `finalize_order` now stores order items in `order_items`.
- Database settings now read from `.env` instead of relying only on a hardcoded URL.
- `setup_all.bat` now uses the correct SQL file name: `schemas.sql`.

## Requirements

- Python 3.11+
- MySQL running locally
- A database named `abt_dev`

## Environment

Create or update `.env` with:

```env
DB_URL=mysql+pymysql://root:Root@localhost/abt_dev

TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
```

## Install

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Database setup

If `abt_dev` does not exist yet, create it first:

```sql
CREATE DATABASE abt_dev;
```

You can optionally apply the provided schema file manually:

```powershell
mysql -u root -p < schemas.sql
```

Even if you skip that step, the app now creates any missing tables during startup.

## Run the API

```powershell
uvicorn app.main:app --reload
```

Swagger UI:

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Health check:

- [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## Finalize order example

```json
{
  "total": 2599,
  "paymentMethod": "UPI",
  "shippingAddress": "Flat 101, Sai Residency, Pune, Maharashtra",
  "itemCount": 2,
  "primaryLabel": "Electronics",
  "items": [
    {
      "productId": 101,
      "productName": "Wireless Mouse",
      "price": 999,
      "quantity": 1,
      "imageUrl": "https://example.com/mouse.jpg"
    },
    {
      "productId": 202,
      "productName": "Mechanical Keyboard",
      "price": 1600,
      "quantity": 1,
      "imageUrl": "https://example.com/keyboard.jpg"
    }
  ]
}
```
