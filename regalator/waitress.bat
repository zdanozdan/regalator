@echo off
REM Simple Waitress server startup script

REM Set production environment variables
set DB_TYPE=mysql
set DB_NAME=regalator
set DB_USER=regalator
set DB_PASSWORD=REgalator2025
set DB_HOST=localhost
set DB_PORT=3306
set DEBUG=False
set SECRET_KEY=your-production-secret-key-change-this
set ALLOWED_HOSTS=127.0.0.1,localhost,regalator.pl

REM Activate virtual environment and start server
call C:\Users\Administrator\projects\regalator\venv\Scripts\activate.bat
waitress-serve --listen=127.0.0.1:8000 regalator.wsgi:application
