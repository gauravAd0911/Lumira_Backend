@echo off
echo =========================================
echo ðŸš€ FULL PROJECT AUTO SETUP STARTED
echo =========================================

REM 1. Create Virtual Environment
if not exist venv (
    echo ðŸ“¦ Creating virtual environment...
    python -m venv venv
)

REM 2. Activate venv
call venv\Scripts\activate

REM 3. Install Requirements
echo ðŸ“¦ Installing dependencies...
pip install -r requirements.txt

REM 4. Run SQL Script
echo ðŸ›  Running SQL setup...
mysql -u root -pRoot < ecommerce_cart_full.sql

REM 5. Start FastAPI Server
echo ðŸš€ Starting FastAPI server...
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
