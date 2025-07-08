@echo off
cd /d D:\Firm
start "" /min cmd /c "call venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:8000"
