#!/bin/bash
# Regalator WMS - Unix/Linux/macOS Installation Script
# Run this script to automatically set up the project

echo "============================================================"
echo "  Regalator WMS - Installation (Unix/Linux/macOS)"
echo "============================================================"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found!"
    echo "Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"
echo ""

# Run the installation script
python3 install.py

if [ $? -ne 0 ]; then
    echo ""
    echo "============================================================"
    echo "  ERROR: Installation failed!"
    echo "============================================================"
    echo ""
    echo "If you see any errors, please check:"
    echo "  - Python version: python3 --version (should be 3.8+)"
    echo "  - Internet connection (required for downloading packages)"
    echo ""
    exit 1
fi

echo ""
echo "============================================================"
echo "  Installation completed!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run migrations:"
echo "     cd regalator"
echo "     python manage.py migrate"
echo ""
echo "  3. Create superuser:"
echo "     python manage.py createsuperuser"
echo ""
echo "  4. Start server:"
echo "     python manage.py runserver"
echo ""

