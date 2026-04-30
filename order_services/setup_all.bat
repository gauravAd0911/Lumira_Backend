@echo off
echo ================================
echo ORDER SERVICE SETUP STARTED
echo ================================

IF NOT EXIST venv (
    python -m venv venv
)

call venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt

echo Creating database schema...
mysql -u root -p < schemas.sql

echo Starting server...
uvicorn app.main:app --reload

pause
