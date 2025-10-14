@echo off
REM Regalator WMS - Windows Installation Script
REM Run this script to automatically set up the project

echo ============================================================
echo   Regalator WMS - Installation (Windows)
echo ============================================================
echo.

python install.py

if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo   ERROR: Installation failed!
    echo ============================================================
    echo.
    echo If you see "ModuleNotFoundError: No module named 'setuptools'"
    echo Don't worry! The install.py script handles everything.
    echo.
    echo Make sure you have Python 3.8+ installed:
    echo   python --version
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ============================================================
echo   Installation completed!
echo ============================================================
echo.
echo Next steps:
echo   1. Activate virtual environment:
echo      venv\Scripts\activate
echo.
echo   2. Run migrations:
echo      cd regalator
echo      python manage.py migrate
echo.
echo   3. Create superuser:
echo      python manage.py createsuperuser
echo.
echo   4. Start server:
echo      python manage.py runserver
echo.
pause

