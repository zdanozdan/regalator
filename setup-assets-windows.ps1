# Windows Asset Setup PowerShell Script for Regalator
# This script sets up static and media files for nginx on Windows

param(
    [string]$NginxPath = "C:\nginx",
    [string]$ProjectPath = "C:\Users\Administrator\projects\regalator",
    [switch]$Force = $false
)

Write-Host "Setting up assets for Windows nginx..." -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "regalator\manage.py")) {
    Write-Error "Please run this script from the regalator project root directory"
    Write-Host "Expected to find: regalator\manage.py" -ForegroundColor Red
    exit 1
}

# Change to Django project directory
Set-Location "regalator"

Write-Host "`nStep 1: Collecting static files..." -ForegroundColor Yellow
try {
    python manage.py collectstatic --noinput
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to collect static files"
    }
} catch {
    Write-Error "Error: Failed to collect static files"
    exit 1
}

Write-Host "`nStep 2: Checking directory structure..." -ForegroundColor Yellow
if (-not (Test-Path "staticfiles")) {
    Write-Error "Error: staticfiles directory not found after collectstatic"
    exit 1
}

if (-not (Test-Path "media")) {
    Write-Error "Error: media directory not found"
    exit 1
}

Write-Host "`nStep 3: Setting up nginx configuration..." -ForegroundColor Yellow
if (-not (Test-Path $NginxPath)) {
    Write-Warning "Nginx directory $NginxPath not found"
    Write-Host "Please update the NginxPath parameter or install nginx to $NginxPath" -ForegroundColor Red
    Write-Host "Usage: .\setup-assets-windows.ps1 -NginxPath 'C:\your\nginx\path'" -ForegroundColor Cyan
    exit 1
}

# Set up paths for static and media files
$StaticPath = Join-Path $ProjectPath "staticfiles"
$MediaPath = Join-Path $ProjectPath "regalator\media"

Write-Host "Project directory: $ProjectPath" -ForegroundColor Cyan
Write-Host "Static files path: $StaticPath" -ForegroundColor Cyan
Write-Host "Media files path: $MediaPath" -ForegroundColor Cyan

# Verify project paths exist
if (-not (Test-Path $StaticPath)) {
    Write-Warning "Static files directory not found: $StaticPath"
    Write-Host "Make sure you've run 'python manage.py collectstatic' first" -ForegroundColor Red
}

if (-not (Test-Path $MediaPath)) {
    Write-Warning "Media files directory not found: $MediaPath"
}

Write-Host "`nStep 5: Setting up nginx configuration..." -ForegroundColor Yellow
$NginxConfigPath = Join-Path $NginxPath "conf\nginx.conf"
$WindowsConfigPath = "..\nginx-windows.conf"

if (Test-Path $WindowsConfigPath) {
    try {
        Copy-Item -Path $WindowsConfigPath -Destination $NginxConfigPath -Force
        Write-Host "Copied nginx-windows.conf to nginx configuration" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to copy nginx configuration: $_"
    }
} else {
    Write-Warning "nginx-windows.conf not found in parent directory"
}

Write-Host "`nStep 6: Verifying nginx configuration..." -ForegroundColor Yellow
$NginxExe = Join-Path $NginxPath "nginx.exe"
if (Test-Path $NginxExe) {
    try {
        & $NginxExe -t
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Nginx configuration test passed!" -ForegroundColor Green
        } else {
            Write-Warning "Nginx configuration test failed. Please check the configuration."
        }
    } catch {
        Write-Warning "Could not test nginx configuration: $_"
    }
} else {
    Write-Warning "nginx.exe not found at: $NginxExe"
}

Write-Host "`nAsset setup completed!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Start Django: python manage.py runserver 8000" -ForegroundColor White
Write-Host "2. Start nginx: nginx.exe" -ForegroundColor White
Write-Host "3. Test static files: http://localhost/static/wms/css/wms.css" -ForegroundColor White
Write-Host "4. Test media files: http://localhost/media/assets/uncategorized/regalator.png" -ForegroundColor White

Write-Host "`nConfiguration Summary:" -ForegroundColor Cyan
Write-Host "Nginx Path: $NginxPath" -ForegroundColor White
Write-Host "Project Path: $ProjectPath" -ForegroundColor White
Write-Host "Static Files: $StaticPath" -ForegroundColor White
Write-Host "Media Files: $MediaPath" -ForegroundColor White
Write-Host "Config File: $NginxConfigPath" -ForegroundColor White
