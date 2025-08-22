#!/usr/bin/env python3
"""
Setup Environment Script for LiDAR Learning Project

This script sets up the Python virtual environment and installs required dependencies.
Run this first before using the other scripts.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        if result.stdout.strip():
            print(f"  Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed!")
        print(f"  Error: {e.stderr.strip()}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    print(f"🐍 Checking Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ Python 3.8 or higher is required!")
        return False
    
    print("✓ Python version is compatible")
    return True


def setup_virtual_environment():
    """Create and activate virtual environment."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("⚠ Virtual environment already exists")
        response = input("Do you want to recreate it? (y/N): ").strip().lower()
        if response == 'y':
            print("🗑️ Removing existing virtual environment...")
            import shutil
            shutil.rmtree(venv_path)
        else:
            print("✓ Using existing virtual environment")
            return True
    
    # Create virtual environment
    if not run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
        return False
    
    return True


def install_dependencies():
    """Install required Python packages."""
    # Determine the correct pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = "venv\\Scripts\\pip"
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
    # Upgrade pip first
    if not run_command(f"{pip_path} install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install core dependencies
    dependencies = [
        "laspy[lazrs]",  # LiDAR file reading with LAZ compression support
        "pyyaml",        # YAML file handling
        "numpy",         # Numerical operations
    ]
    
    for dep in dependencies:
        if not run_command(f"{pip_path} install {dep}", f"Installing {dep}"):
            return False
    
    return True


def create_directories():
    """Create necessary project directories."""
    directories = ["data", "output"]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"✓ Created directory: {dir_name}/")
        else:
            print(f"⚠ Directory already exists: {dir_name}/")


def create_gitignore():
    """Create or update .gitignore file."""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# Data files (large LiDAR files)
data/*.laz
data/*.las
data/lidar_la/*.laz
data/lidar_la/*.las

# Output files
output/
out/

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Temporary files
*.tmp
*.temp
"""
    
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        with open(gitignore_path, "w") as f:
            f.write(gitignore_content)
        print("✓ Created .gitignore file")
    else:
        print("⚠ .gitignore already exists")


def show_usage_instructions():
    """Show instructions for using the environment."""
    activation_cmd = "venv\\Scripts\\activate" if os.name == 'nt' else "source venv/bin/activate"
    
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print(f"1. Activate the virtual environment:")
    print(f"   {activation_cmd}")
    print(f"")
    print(f"2. Download LiDAR data:")
    print(f"   python download_lidar.py")
    print(f"")
    print(f"3. Extract metadata:")
    print(f"   python extract_metadata.py")
    print(f"")
    print(f"💡 Or run the complete pipeline:")
    print(f"   python simple_lidar_metadata.py")
    print(f"")
    print(f"📁 Project structure:")
    print(f"   data/     - Downloaded LiDAR files")
    print(f"   output/   - Generated metadata and catalogs")
    print(f"   venv/     - Python virtual environment")


def main():
    """Main setup function."""
    print("LiDAR Learning Project - Environment Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        print("✗ Failed to setup virtual environment!")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("✗ Failed to install dependencies!")
        sys.exit(1)
    
    # Create project directories
    create_directories()
    
    # Create .gitignore
    create_gitignore()
    
    # Show usage instructions
    show_usage_instructions()


if __name__ == "__main__":
    main()
