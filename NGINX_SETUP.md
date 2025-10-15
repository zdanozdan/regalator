# Nginx Configuration Setup

This project includes two nginx configuration files optimized for different environments:

## Files

- `nginx.conf` - Cross-platform configuration (works on both Linux and Windows)
- `nginx-windows.conf` - Windows-optimized configuration for native Windows nginx

## Usage

### Docker Environment (Recommended)

Use the standard `nginx.conf` file with Docker Compose:

```bash
docker-compose up
```

The configuration is automatically mounted and used by the nginx container.

### Native Windows Installation

If you're running nginx directly on Windows (not in Docker), use the Windows-optimized configuration:

1. Install nginx for Windows
2. Copy `nginx-windows.conf` to your nginx installation directory
3. Rename it to `nginx.conf` (backup the original first)
4. Start nginx

### Key Differences

#### Cross-platform (`nginx.conf`)
- Uses relative paths (`./static/`, `./media/`)
- Includes Windows-specific optimizations but works on all platforms
- Uses `web:8000` for Docker container communication
- Uses `mime.types` (relative path)

#### Windows-optimized (`nginx-windows.conf`)
- Single worker process for Windows stability
- Uses `127.0.0.1:8000` for local Django connection
- Disables `sendfile` and `tcp_nopush` for Windows compatibility
- Uses `select` event model for better Windows performance

## Directory Structure

Make sure your project has the following structure:

```
regalator/
├── nginx.conf (or nginx-windows.conf)
├── static/
├── media/
└── logs/ (will be created automatically)
```

## SSL/HTTPS Setup

To enable HTTPS:

1. Uncomment the HTTPS server block in the configuration
2. Place your SSL certificates in the `ssl/` directory
3. Update the certificate paths in the configuration
4. Restart nginx

## Troubleshooting

### Common Issues

1. **Permission errors on Windows**: Run nginx as Administrator
2. **Path not found**: Ensure the `static/` and `media/` directories exist
3. **Port conflicts**: Change the listen port if 80 is already in use
4. **Django connection failed**: Ensure Django is running on the correct port

### Logs

Check the following log files for errors:
- `logs/error.log` - nginx error log
- `logs/access.log` - nginx access log

## Performance Tuning

### Windows
- Use `nginx-windows.conf` for better Windows performance
- Consider increasing `worker_connections` if you have high traffic
- Monitor memory usage with single worker process

### Linux/Docker
- The standard `nginx.conf` is optimized for containerized environments
- Multiple worker processes are handled by Docker

## Security

Both configurations include:
- Rate limiting for API and login endpoints
- Security headers (XSS protection, content type options, etc.)
- File upload size limits (100MB)
- Proper proxy headers for Django

For production, ensure you:
- Enable HTTPS
- Use strong SSL certificates
- Configure proper firewall rules
- Regularly update nginx
