@echo off
echo =========================================
echo 🚀 FULL PROJECT AUTO SETUP STARTED
echo =========================================

REM ==============================
REM 1. Create Virtual Environment
REM ==============================
if not exist venv (
    echo 📦 Creating virtual environment...
    python -m venv venv
) else (
    echo ⚠️ venv already exists
)

REM Activate venv
call venv\Scripts\activate

REM ==============================
REM 2. Upgrade pip
REM ==============================
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM ==============================
REM 3. Install requirements
REM ==============================
if exist requirements.txt (
    echo 📥 Installing requirements...
    pip install -r requirements.txt
) else (
    echo ❌ requirements.txt not found
)

REM Install extra tools
pip install python-dotenv alembic pymysql

REM ==============================
REM 4. Create .env file
REM ==============================
if not exist .env (
    echo 🛠 Creating .env file...

    (
    echo # Database
    echo DATABASE_URL=mysql+pymysql://root:Root@localhost:3306/abt_dev
    echo.
    echo # JWT
    echo JWT_SECRET=your-super-secret-jwt-key-change-in-production
    echo.
    echo # Twilio
    echo TWILIO_ACCOUNT_SID=PASTE_YOUR_SID
    echo TWILIO_AUTH_TOKEN=PASTE_YOUR_TOKEN
    echo TWILIO_PHONE_NUMBER=PASTE_YOUR_NUMBER
    echo.
    echo # OTP
    echo OTP_EXPIRY_MINUTES=5
    ) > .env

    echo ✅ .env created
) else (
    echo ⚠️ .env already exists
)

REM ==============================
REM 5. ✅ Create Database (NEW)
REM ==============================
echo 🛠 Creating database if not exists...

mysql -u root -pRoot -e "CREATE DATABASE IF NOT EXISTS abt_dev;"

if %errorlevel% neq 0 (
    echo ❌ MySQL connection failed. Check password or MySQL service.
    pause
    exit /b
)

echo ✅ Database ready

REM ==============================
REM 6. Setup Alembic
REM ==============================
if not exist alembic (
    echo 🧱 Initializing Alembic...
    alembic init alembic
)

REM Update alembic.ini DB URL
set DB_URL=mysql+pymysql://root:Root@127.0.0.1:3306/abt_dev

powershell -Command "(Get-Content alembic.ini) -replace 'sqlalchemy.url =.*', 'sqlalchemy.url = %DB_URL%' | Set-Content alembic.ini"

echo ✅ alembic.ini updated

REM ==============================
REM 7. Create Migration
REM ==============================
echo 🔄 Creating migration...
alembic revision --autogenerate -m "init" 2>nul

REM ==============================
REM 8. Apply Migration
REM ==============================
echo 📊 Applying migration...
alembic upgrade head

REM ==============================
REM 9. Run Server
REM ==============================
echo 🚀 Starting FastAPI server...
uvicorn auth.main:app --reload

pause