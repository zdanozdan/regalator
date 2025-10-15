@echo off
REM Windows Asset Update Script for Regalator
REM This script updates static and media files for nginx on Windows

echo Updating assets for Windows nginx...

REM Check if we're in the right directory
if not exist "regalator\manage.py" (
    echo Error: Please run this script from the regalator project root directory
    pause
    exit /b 1
)

REM Change to Django project directory
cd regalator

echo.
echo Step 1: Collecting updated static files...
python manage.py collectstatic --noinput
if %errorlevel% neq 0 (
    echo Error: Failed to collect static files
    pause
    exit /b 1
)

echo.
echo Step 2: Reloading nginx configuration...
set NGINX_DIR=C:\nginx
set PROJECT_DIR=C:\Users\Administrator\projects\regalator

echo Project directory: %PROJECT_DIR%
echo Static files served from: %PROJECT_DIR%\staticfiles\
echo Media files served from: %PROJECT_DIR%\regalator\media\

if exist "%NGINX_DIR%" (
    echo.
    echo Step 3: Reloading nginx configuration...
    nginx -s reload
    if %errorlevel% neq 0 (
        echo Warning: Failed to reload nginx. You may need to restart nginx manually.
    ) else (
        echo Nginx configuration reloaded successfully!
    )
) else (
    echo Warning: Nginx directory %NGINX_DIR% not found
    echo Please update the NGINX_DIR variable in this script
)

echo.
echo Asset update completed!
echo.
pause
