@echo off
REM Windows Asset Setup Script for Regalator
REM This script sets up static and media files for nginx on Windows

echo Setting up assets for Windows nginx...

REM Check if we're in the right directory
if not exist "regalator\manage.py" (
    echo Error: Please run this script from the regalator project root directory
    echo Expected to find: regalator\manage.py
    pause
    exit /b 1
)

REM Change to Django project directory
cd regalator

echo.
echo Step 1: Collecting static files...
python manage.py collectstatic --noinput
if %errorlevel% neq 0 (
    echo Error: Failed to collect static files
    pause
    exit /b 1
)

echo.
echo Step 2: Checking directory structure...
if not exist "staticfiles" (
    echo Error: staticfiles directory not found after collectstatic
    pause
    exit /b 1
)

if not exist "media" (
    echo Error: media directory not found
    pause
    exit /b 1
)

echo.
echo Step 3: Setting up nginx configuration...
REM Use project directory for static files (no copying needed)
set PROJECT_DIR=C:\Users\Administrator\projects\regalator
set NGINX_DIR=C:\Users\Administrator\projects\regalator\nginx-1.28.0

echo Project directory: %PROJECT_DIR%
echo Nginx directory: %NGINX_DIR%

REM Check if nginx directory exists
if not exist "%NGINX_DIR%" (
    echo Warning: Nginx directory %NGINX_DIR% not found
    echo Please install nginx or update the NGINX_DIR variable in this script
    echo Current nginx installation path: %NGINX_DIR%
    pause
)

REM Copy nginx configuration
if exist "%NGINX_DIR%" (
    echo.
    echo Step 4: Setting up nginx configuration...
    if exist "..\nginx-windows.conf" (
        copy /Y "..\nginx-windows.conf" "%NGINX_DIR%\conf\nginx.conf"
        echo Copied nginx-windows.conf to nginx configuration
        echo.
        echo Static files will be served from: %PROJECT_DIR%\staticfiles\
        echo Media files will be served from: %PROJECT_DIR%\regalator\media\
    ) else (
        echo Warning: nginx-windows.conf not found in parent directory
    )
)

echo.
echo Asset setup completed!
echo.
echo Next steps:
echo 1. Start Django: python manage.py runserver 8000
echo 2. Start nginx: nginx.exe
echo 3. Test: http://localhost/static/wms/css/wms.css
echo.
pause
