# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup
- Basic WMS functionality
- Subiekt GT integration
- HTMX-powered interface
- Bootstrap 5 UI
- Toast notifications
- Product synchronization
- Inventory management
- Picking operations
- Receiving operations
- Location management
- Product groups
- Barcode scanning support

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [1.0.0] - 2024-01-XX

### Added
- **Core WMS System**
  - Product management with Subiekt GT integration
  - Inventory tracking with real-time stock levels
  - Location management for warehouse organization
  - Product groups for logical categorization

- **Picking Operations**
  - Customer order management
  - Barcode scanning for products and locations
  - Picking order creation and management
  - Real-time picking status updates

- **Receiving Operations**
  - Supplier order management
  - Receiving order creation and processing
  - Barcode scanning for receiving
  - Stock level updates

- **Subiekt GT Integration**
  - Real-time product synchronization
  - Stock level reconciliation
  - Automatic product group creation
  - Bidirectional data flow

- **User Interface**
  - Modern Bootstrap 5 responsive design
  - HTMX for dynamic updates without page reloads
  - Toast notifications for user feedback
  - Advanced filtering and search capabilities
  - Mobile-friendly interface

- **Technical Features**
  - Django 4.2+ framework
  - SQLite/PostgreSQL database support
  - ODBC connection to Subiekt GT
  - Comprehensive test suite
  - CI/CD pipeline with GitHub Actions

### Security
- CSRF protection enabled
- Secure session management
- Input validation and sanitization
- SQL injection prevention
- XSS protection

## [0.9.0] - 2024-01-XX

### Added
- Initial development version
- Basic Django project structure
- Subiekt models and integration
- WMS core models
- Asset management system

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

---

## Version History

- **1.0.0**: First stable release with full WMS functionality
- **0.9.0**: Initial development version

## Migration Guide

### Upgrading from 0.9.0 to 1.0.0

1. **Database Migrations**
   ```bash
   python manage.py migrate
   ```

2. **New Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration Updates**
   - Update Subiekt database connection settings
   - Configure new environment variables
   - Update static files: `python manage.py collectstatic`

4. **Breaking Changes**
   - None in this release

## Support

For support and questions:
- **GitHub Issues**: [https://github.com/yourusername/regalator/issues](https://github.com/yourusername/regalator/issues)
- **Email**: support@regalator.com
- **Documentation**: [README.md](README.md) 