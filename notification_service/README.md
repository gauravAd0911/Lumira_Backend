# Notification Service

FastAPI service for registering user devices and managing notifications.

## What was fixed

The `POST /api/v1/notifications/devices/register` endpoint was failing with:

`sqlalchemy.exc.ProgrammingError: (1146, "Table 'abt_dev.devices' doesn't exist")`

This project now creates the required `devices` and `notifications` tables automatically on app startup by using SQLAlchemy models and `Base.metadata.create_all(...)`.

## Requirements

- Python 3.11+
- MySQL running locally or on a reachable host
- A database named `abt_dev` (or another name configured in `.env`)

## Environment variables

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=replace_me
DB_NAME=abt_dev

TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

## Install and run

### Option 1: use the batch file

```bat
run.bat
```

This script:

- creates the virtual environment if needed
- installs dependencies
- creates the MySQL database if it does not exist
- starts the FastAPI server

### Option 2: run manually

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
mysql -u root -pRoot -e "CREATE DATABASE IF NOT EXISTS abt_dev;"
uvicorn app.main:app --reload
```

## API docs

After the server starts, open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

## Available endpoints

- `POST /api/v1/notifications`
- `POST /api/v1/notifications/devices/register`
- `DELETE /api/v1/notifications/devices/{device_id}`
- `GET /api/v1/notifications?user_id={user_id}`
- `PATCH /api/v1/notifications/{notification_id}/read`

## Example request

```json
POST /api/v1/notifications
{
  "user_id": 102,
  "title": "Order update",
  "message": "Your order has been shipped.",
  "type": "ORDER_SHIPPED"
}
```

```json
POST /api/v1/notifications/devices/register
{
  "user_id": 101,
  "device_token": "fcm_abc123_device_token",
  "platform": "android"
}
```

## Testing mark-as-read in Swagger

1. Create a notification with `POST /api/v1/notifications`.
2. Copy the returned notification `id`.
3. Use that `id` with `PATCH /api/v1/notifications/{notification_id}/read`.

`notification_id` is the notification row id, not the `user_id`.

## Notes

- Tables are created automatically when the app starts.
- `notification_schema.sql` is still available if you want to create the schema manually.
- If MySQL credentials or host settings change, update `.env` before starting the service.
