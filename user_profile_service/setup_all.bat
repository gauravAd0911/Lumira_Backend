@echo off
title 🚀 Fully Auto Setup (No Prompt)

echo =========================================
echo 🚀 AUTO SETUP STARTED (NO PASSWORD ASK)
echo =========================================

REM ===============================
REM CONFIG (SET YOUR DB USER HERE)
REM ===============================
set DB_USER=root
set DB_PASS=Root
set DB_NAME=abt_dev

REM ===============================
REM 1. CREATE VENV
REM ===============================
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate

REM ===============================
REM 2. INSTALL REQUIREMENTS
REM ===============================
pip install --upgrade pip
pip install -r requirements.txt

REM ===============================
REM 3. CREATE .env
REM ===============================
if not exist .env (
    echo DATABASE_URL=mysql+pymysql://%DB_USER%:%DB_PASS%@localhost:3306/%DB_NAME%> .env
)

REM ===============================
REM 4. CREATE DATABASE (NO ROOT)
REM ===============================
echo 🗄️ Creating database using app user...

mysql -u %DB_USER% -p%DB_PASS% -e "CREATE DATABASE IF NOT EXISTS %DB_NAME%;"

if %errorlevel% neq 0 (
    echo ❌ FAILED: Check DB_USER / DB_PASS
    echo 👉 You must create this user once manually
    pause
    exit /b
)

REM ===============================
REM 5. RUN SQL
REM ===============================
mysql -u %DB_USER% -p%DB_PASS% %DB_NAME% < sql\user_profile_service.sql

REM ===============================
REM 6. RUN SERVER
REM ===============================
uvicorn app.main:app --reload

pause