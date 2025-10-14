#!/usr/bin/env python3
"""
Regalator WMS Installation Script
Creates virtual environment and installs all dependencies

This script uses ONLY Python standard library (subprocess, sys, os, shutil)
and does NOT require setuptools, pip, or any other external packages.

Run this script with your system Python to set up the project:
    python3 install.py    (Linux/macOS)
    python install.py     (Windows)
"""

import subprocess
import sys
import os

def main():
    """Main installation function"""
    print("=" * 60)
    print("  Regalator WMS - Installation Script")
    print("=" * 60)
    print()
    
    venv_path = "venv"
    
    # Check if venv already exists
    if os.path.exists(venv_path):
        response = input(f"Virtual environment already exists at '{venv_path}'. Recreate? (y/N): ")
        if response.lower() != 'y':
            print("Installation cancelled.")
            return
        
        print(f"Removing existing virtual environment...")
        import shutil
        shutil.rmtree(venv_path)
    
    # Create virtual environment
    print("\n[1/4] Creating virtual environment...")
    subprocess.check_call([sys.executable, "-m", "venv", venv_path])
    print("✓ Virtual environment created")
    
    # Determine paths based on OS
    if sys.platform == "win32":
        pip_path = os.path.join(venv_path, "Scripts", "pip")
        python_path = os.path.join(venv_path, "Scripts", "python")
        activate_cmd = f"{venv_path}\\Scripts\\activate"
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
        python_path = os.path.join(venv_path, "bin", "python")
        activate_cmd = f"source {venv_path}/bin/activate"
    
    # Upgrade pip
    print("\n[2/4] Upgrading pip...")
    subprocess.check_call([python_path, "-m", "pip", "install", "--upgrade", "pip"])
    print("✓ Pip upgraded")
    
    # Install requirements
    print("\n[3/4] Installing requirements...")
    if os.path.exists("requirements.txt"):
        subprocess.check_call([pip_path, "install", "-r", "requirements.txt"])
        print("✓ Requirements installed")
    else:
        print("⚠ Warning: requirements.txt not found")
    
    # Install development dependencies (optional)
    response = input("\n[4/4] Install development dependencies? (y/N): ")
    if response.lower() == 'y':
        subprocess.check_call([pip_path, "install", "-e", ".[dev]"])
        print("✓ Development dependencies installed")
    
    # Success message
    print("\n" + "=" * 60)
    print("  Installation completed successfully!")
    print("=" * 60)
    print("\nTo activate the virtual environment, run:")
    print(f"  {activate_cmd}")
    print("\nTo start the development server:")
    print(f"  {activate_cmd}")
    print("  cd regalator")
    print("  python manage.py migrate")
    print("  python manage.py runserver")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during installation: {e}")
        sys.exit(1)

