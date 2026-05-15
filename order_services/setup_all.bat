@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ================================
echo ORDER SERVICE SETUP STARTED
echo ================================

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
cd /d "%PROJECT_DIR%"

set "ENV_FILE=%PROJECT_DIR%\.env"

if exist "%ENV_FILE%" (
    for /f "usebackq tokens=1,* delims==" %%a in ("%ENV_FILE%") do (
        set "_k=%%a"
        set "_v=%%b"
        if not "!_k!"=="" if not "!_k:~0,1!"=="#" set "!_k!=!_v!"
    )
)

if not defined DB_HOST set "DB_HOST=localhost"
if not defined DB_PORT set "DB_PORT=3306"
if not defined DB_NAME set "DB_NAME=abt_order_db"
if not defined DB_USER set "DB_USER=root"
if not defined DB_PASS set "DB_PASS=Gaurav@123"
if not defined APP_HOST set "APP_HOST=127.0.0.1"
if not defined APP_PORT set "APP_PORT=8007"
if not defined JWT_SECRET set "JWT_SECRET=your-super-secret-jwt-key-change-in-production"
if not defined JWT_ALGORITHM set "JWT_ALGORITHM=HS256"
if not defined ALLOWED_ORIGINS set "ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000,http://localhost:8080"
if not defined PAYMENT_SERVICE_BASE_URL set "PAYMENT_SERVICE_BASE_URL=http://127.0.0.1:8006"
if not defined INTERNAL_SERVICE_TOKEN set "INTERNAL_SERVICE_TOKEN=dev-internal-token"
if not defined ENABLE_ORDER_NOTIFICATIONS set "ENABLE_ORDER_NOTIFICATIONS=true"
if not defined SMTP_HOST set "SMTP_HOST="
if not defined SMTP_PORT set "SMTP_PORT=587"
if not defined SMTP_USER set "SMTP_USER="
if not defined SMTP_PASS set "SMTP_PASS="
if not defined SMTP_FROM_EMAIL set "SMTP_FROM_EMAIL="
if not defined SMTP_USE_TLS set "SMTP_USE_TLS=true"
if not defined TWILIO_SID set "TWILIO_SID="
if not defined TWILIO_AUTH set "TWILIO_AUTH="
if not defined TWILIO_PHONE set "TWILIO_PHONE="

if not defined DB_URL set "DB_URL=mysql+pymysql://%DB_USER%:%DB_PASS%@%DB_HOST%:%DB_PORT%/%DB_NAME%"

if not exist "%ENV_FILE%" (
    echo Creating default .env file...
    > "%ENV_FILE%" echo DB_HOST=%DB_HOST%
    >> "%ENV_FILE%" echo DB_PORT=%DB_PORT%
    >> "%ENV_FILE%" echo DB_NAME=%DB_NAME%
    >> "%ENV_FILE%" echo DB_USER=%DB_USER%
    >> "%ENV_FILE%" echo DB_PASS=%DB_PASS%
    >> "%ENV_FILE%" echo DB_URL=%DB_URL%
    >> "%ENV_FILE%" echo APP_HOST=%APP_HOST%
    >> "%ENV_FILE%" echo APP_PORT=%APP_PORT%
    >> "%ENV_FILE%" echo JWT_SECRET=%JWT_SECRET%
    >> "%ENV_FILE%" echo JWT_ALGORITHM=%JWT_ALGORITHM%
    >> "%ENV_FILE%" echo ALLOWED_ORIGINS=%ALLOWED_ORIGINS%
    >> "%ENV_FILE%" echo PAYMENT_SERVICE_BASE_URL=%PAYMENT_SERVICE_BASE_URL%
    >> "%ENV_FILE%" echo INTERNAL_SERVICE_TOKEN=%INTERNAL_SERVICE_TOKEN%
    >> "%ENV_FILE%" echo ENABLE_ORDER_NOTIFICATIONS=%ENABLE_ORDER_NOTIFICATIONS%
    >> "%ENV_FILE%" echo TWILIO_SID=%TWILIO_SID%
    >> "%ENV_FILE%" echo TWILIO_AUTH=%TWILIO_AUTH%
    >> "%ENV_FILE%" echo TWILIO_PHONE=%TWILIO_PHONE%
    >> "%ENV_FILE%" echo SMTP_HOST=%SMTP_HOST%
    >> "%ENV_FILE%" echo SMTP_PORT=%SMTP_PORT%
    >> "%ENV_FILE%" echo SMTP_USER=%SMTP_USER%
    >> "%ENV_FILE%" echo SMTP_PASS=%SMTP_PASS%
    >> "%ENV_FILE%" echo SMTP_FROM_EMAIL=%SMTP_FROM_EMAIL%
    >> "%ENV_FILE%" echo SMTP_USE_TLS=%SMTP_USE_TLS%
)

if not exist venv (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create Python virtual environment.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate Python virtual environment.
    pause
    exit /b 1
)

python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

where mysql >nul 2>&1
if errorlevel 1 (
    echo [WARN] mysql.exe not found on PATH. Skipping schema import.
    goto :start_server
)

echo Creating database schema...
set "MYSQL_ARGS=-h %DB_HOST% -P %DB_PORT% -u %DB_USER% --protocol=TCP"
if not "%DB_PASS%"=="" set "MYSQL_ARGS=%MYSQL_ARGS% -p%DB_PASS%"

mysql %MYSQL_ARGS% -e "CREATE DATABASE IF NOT EXISTS %DB_NAME% CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
if errorlevel 1 (
    echo [WARN] Could not create or verify database. Check MySQL credentials in .env.
    goto :start_server
)

if exist schemas.sql (
    mysql %MYSQL_ARGS% "%DB_NAME%" < schemas.sql
    if errorlevel 1 echo [WARN] Schema import reported errors. Server will still start.
) else (
    echo [WARN] schemas.sql not found. Skipping schema import.
)

:start_server
set "SERVICE_URL=http://%APP_HOST%:%APP_PORT%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $response = Invoke-WebRequest -UseBasicParsing -Uri '%SERVICE_URL%/health' -TimeoutSec 2; if ($response.StatusCode -eq 200) { exit 0 } } catch { exit 1 }"
if not errorlevel 1 (
    echo [INFO] Order service is already running on %SERVICE_URL%.
    echo [INFO] Open %SERVICE_URL%/health to verify it.
    goto :done
)

echo Starting order service on %SERVICE_URL%
uvicorn app.main:app --reload --host "%APP_HOST%" --port "%APP_PORT%"

if errorlevel 1 (
    echo [ERROR] Uvicorn exited with an error.
    pause
    exit /b 1
)

:done
endlocal




