@echo off
cd /d "%~dp0"
echo Starting Tariq Perfume Store...
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" manage.py migrate
  ".venv\Scripts\python.exe" manage.py runserver
) else (
  python manage.py migrate
  python manage.py runserver
)
