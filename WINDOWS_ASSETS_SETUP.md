# Windows Nginx Asset Configuration Guide

This guide walks you through configuring Django static assets to work with nginx on Windows.

## Current Asset Structure

Your project has the following asset structure:
```
regalator/
├── regalator/
│   ├── wms/static/wms/          # App-specific static files
│   │   ├── css/wms.css
│   │   └── js/barcode.js, stock.js
│   ├── staticfiles/             # Collected static files (Django collectstatic)
│   │   ├── admin/               # Django admin static files
│   │   └── wms/                 # Collected WMS static files
│   └── media/                   # User-uploaded media files
│       ├── assets/
│       ├── avatars/
│       ├── locations/
│       └── products/
```

## Step 1: Update Django Settings for Windows

First, let's update your Django settings to work better with Windows paths:

### Update `regalator/settings.py`

```python
# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Windows-compatible static files directories
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "wms", "static"),
    # Add other app static directories here if needed
]

# Windows-compatible static root
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

## Step 2: Collect Static Files

Run Django's collectstatic command to gather all static files:

```bash
# In your project directory
cd regalator
python manage.py collectstatic --noinput
```

This will copy all static files from `STATICFILES_DIRS` to `STATIC_ROOT`.

## Step 3: Configure Nginx for Windows

### Option A: Use the Windows-optimized nginx.conf

1. Copy `nginx-windows.conf` to your nginx installation directory
2. Rename it to `nginx.conf` (backup the original first)
3. Update the paths in the configuration

### Option B: Update the existing nginx.conf

The current nginx.conf should work, but let's verify the paths are correct.

## Step 4: Directory Structure for Windows Nginx

Your nginx should be configured to serve files from these locations:

```
C:\nginx\                           # Nginx installation directory
├── conf\
│   └── nginx.conf                  # Your configuration file
├── logs\                           # Nginx logs (auto-created)
├── static\                         # Static files (symlink or copy)
│   ├── admin\                      # Django admin files
│   └── wms\                        # Your app files
├── media\                          # Media files (symlink or copy)
│   ├── assets\
│   ├── avatars\
│   ├── locations\
│   └── products\
└── html\                           # Default nginx directory
```

## Step 5: Create Windows Batch Scripts

I'll create batch scripts to help you manage assets on Windows.

## Step 6: Test the Configuration

1. Start Django development server: `python manage.py runserver 8000`
2. Start nginx: `nginx.exe`
3. Test static files: `http://localhost/static/wms/css/wms.css`
4. Test media files: `http://localhost/media/assets/uncategorized/regalator.png`

## Troubleshooting

### Common Issues

1. **404 for static files**: Check that `STATIC_ROOT` contains the files
2. **Permission denied**: Run nginx as Administrator
3. **Path not found**: Verify the `alias` paths in nginx.conf
4. **Django not serving files**: Ensure `DEBUG=False` in production

### Debug Steps

1. Check nginx error log: `logs/error.log`
2. Check nginx access log: `logs/access.log`
3. Verify file permissions on Windows
4. Test Django static files directly: `http://localhost:8000/static/wms/css/wms.css`

## Production Considerations

1. **Set DEBUG=False** in Django settings
2. **Use absolute paths** in nginx configuration
3. **Enable gzip compression** (already configured)
4. **Set proper cache headers** (already configured)
5. **Use HTTPS** for production

## File Permissions on Windows

Ensure nginx has read access to:
- Static files directory
- Media files directory
- Logs directory (write access)

Run nginx as Administrator or configure proper Windows permissions.
