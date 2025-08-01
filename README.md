# Regalator WMS

Regalator WMS is a comprehensive Warehouse Management System built with Django, designed to manage warehouse operations including picking, receiving, inventory management, and integration with Subiekt GT accounting system.

## 🚀 Features

### Core WMS Functionality
- **Inventory Management**: Track products, locations, and stock levels
- **Picking Operations**: Manage customer order picking with barcode scanning
- **Receiving Operations**: Handle supplier deliveries and receiving processes
- **Product Groups**: Organize products into logical groups
- **Location Management**: Manage warehouse locations and zones
- **Stock Tracking**: Real-time stock level monitoring with reserved quantities

### Subiekt GT Integration
- **Real-time Synchronization**: Sync products and stock levels with Subiekt GT
- **Bidirectional Data Flow**: Import products from Subiekt and update stock levels
- **Product Groups**: Automatic creation and management of product groups
- **Stock Reconciliation**: Compare WMS vs Subiekt stock levels

### User Interface
- **Modern Bootstrap UI**: Clean, responsive interface
- **HTMX Integration**: Dynamic updates without page reloads
- **Toast Notifications**: Real-time user feedback
- **Barcode Scanning**: Mobile-friendly scanning interface
- **Advanced Filtering**: Powerful search and filter capabilities

### Technical Features
- **Django Framework**: Robust web framework
- **SQLite/PostgreSQL**: Flexible database support
- **HTMX**: Modern AJAX without JavaScript complexity
- **Bootstrap 5**: Responsive design framework
- **Font Awesome**: Professional icons

## 📋 Requirements

### System Requirements
- Python 3.8+
- Django 4.2+
- SQLite or PostgreSQL
- ODBC drivers for Subiekt GT connection

### Python Dependencies
- Django
- pyodbc (for Subiekt connection)
- Pillow (for image handling)
- django-crispy-forms (optional)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/regalator.git
cd regalator
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Database
```bash
cd regalator
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

### 6. Configure Subiekt Connection
Edit `regalator/settings.py` and configure your Subiekt database connection:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'subiekt': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': 'your_subiekt_database',
        'HOST': 'your_server',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    }
}

# Subiekt configuration
SUBIEKT_MAGAZYN_ID = 2  # Default warehouse ID
```

### 7. Run Development Server
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to access the application.

## 📁 Project Structure

```
regalator/
├── regalator/          # Main Django project
│   ├── settings.py     # Django settings
│   ├── urls.py         # Main URL configuration
│   └── wsgi.py         # WSGI configuration
├── wms/                # WMS application
│   ├── models.py       # WMS data models
│   ├── views.py        # WMS views and logic
│   ├── urls.py         # WMS URL routing
│   └── templates/      # HTML templates
├── subiekt/            # Subiekt integration
│   ├── models.py       # Subiekt data models
│   └── routers.py      # Database routing
├── assets/             # Asset management
│   ├── models.py       # Asset models
│   └── views.py        # Asset views
├── media/              # User uploaded files
├── static/             # Static files
└── manage.py           # Django management script
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
SUBIEKT_DATABASE_URL=your-subiekt-connection-string
SUBIEKT_MAGAZYN_ID=2
```

### Subiekt Integration
1. Install ODBC drivers for SQL Server
2. Configure database connection in settings.py
3. Test connection using management commands

## 🚀 Usage

### Management Commands

#### Sync Products with Subiekt
```bash
python manage.py sync_subiekt
```

#### Sync Specific Product
```bash
python manage.py sync_subiekt --product-id 123
```

#### Load Demo Data
```bash
python manage.py load_demo_data
```

### Web Interface

1. **Dashboard**: Overview of warehouse operations
2. **Products**: Manage product catalog and sync with Subiekt
3. **Picking**: Process customer orders with barcode scanning
4. **Receiving**: Handle supplier deliveries
5. **Locations**: Manage warehouse locations
6. **Stock**: Monitor inventory levels

## 🔒 Security

### Production Deployment
1. Set `DEBUG=False` in production
2. Use strong `SECRET_KEY`
3. Configure HTTPS
4. Set up proper database permissions
5. Use environment variables for sensitive data

### Database Security
- Use dedicated database user with minimal permissions
- Encrypt database connections
- Regular backups
- Monitor access logs

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Run Specific App Tests
```bash
python manage.py test wms
python manage.py test subiekt
```

## 📊 Monitoring

### Logs
- Application logs: `logs/regalator.log`
- Error tracking: Configure with your preferred service
- Performance monitoring: Django Debug Toolbar (development)

### Health Checks
- Database connectivity
- Subiekt connection status
- Stock level alerts
- Sync status monitoring

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Style
- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions
- Write tests for new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [HTMX Documentation](https://htmx.org/docs/)
- [Bootstrap Documentation](https://getbootstrap.com/docs/)

### Issues
- Report bugs via GitHub Issues
- Request features via GitHub Issues
- Ask questions via GitHub Discussions

### Community
- Join our Discord server
- Follow us on Twitter
- Subscribe to our newsletter

## 🔄 Changelog

### Version 1.0.0
- Initial release
- Basic WMS functionality
- Subiekt GT integration
- HTMX-powered interface
- Bootstrap 5 UI

## 📞 Contact

- **Email**: support@regalator.com
- **Website**: https://regalator.com
- **GitHub**: https://github.com/yourusername/regalator

---

**Made with ❤️ by the Regalator Team** 