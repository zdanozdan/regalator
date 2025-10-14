from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
import subprocess
import sys
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)


def create_venv():
    """Create virtual environment and install dependencies"""
    venv_path = "venv"
    
    if os.path.exists(venv_path):
        print(f"Virtual environment already exists at {venv_path}")
        return
    
    print("Creating virtual environment...")
    subprocess.check_call([sys.executable, "-m", "venv", venv_path])
    
    # Determine pip path based on OS
    if sys.platform == "win32":
        pip_path = os.path.join(venv_path, "Scripts", "pip")
        python_path = os.path.join(venv_path, "Scripts", "python")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
        python_path = os.path.join(venv_path, "bin", "python")
    
    print("Upgrading pip...")
    subprocess.check_call([python_path, "-m", "pip", "install", "--upgrade", "pip"])
    
    print("Installing requirements...")
    subprocess.check_call([pip_path, "install", "-r", "requirements.txt"])
    
    print("\n✓ Virtual environment created successfully!")
    print(f"\nTo activate the virtual environment:")
    if sys.platform == "win32":
        print(f"  {venv_path}\\Scripts\\activate")
    else:
        print(f"  source {venv_path}/bin/activate")


setup(
    name="regalator-wms",
    version="1.0.0",
    author="Regalator Team",
    author_email="support@regalator.com",
    description="A comprehensive Warehouse Management System with Subiekt GT integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/regalator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Topic :: Office/Business",
        "Topic :: Office/Business :: Financial :: Accounting",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-django>=4.5.0",
            "coverage>=7.3.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
        ],
        "production": [
            "gunicorn>=21.0.0",
            "whitenoise>=6.5.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="warehouse management system wms django subiekt inventory",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/regalator/issues",
        "Source": "https://github.com/yourusername/regalator",
        "Documentation": "https://github.com/yourusername/regalator/blob/main/README.md",
    },
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
    entry_points={
        'console_scripts': [
            'regalator-setup-venv=setup:create_venv',
        ],
    },
) 