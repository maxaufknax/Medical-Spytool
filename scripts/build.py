#!/usr/bin/env python3
"""Build script for Medical Spytool executable."""

import subprocess
import sys
import shutil
from pathlib import Path

def check_requirements():
    """Check if required packages are installed."""
    print("Checking build requirements...")
    
    required_packages = ['pyinstaller']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} is missing")
    
    if missing_packages:
        print("\nInstalling missing packages...")
        for package in missing_packages:
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
    
    return True

def clean_build():
    """Clean previous build artifacts."""
    print("Cleaning previous build artifacts...")
    
    build_dirs = ['build', 'dist', '__pycache__']
    spec_files = ['*.spec']
    
    for build_dir in build_dirs:
        if Path(build_dir).exists():
            shutil.rmtree(build_dir)
            print(f"  Removed {build_dir}/")
    
    # Remove spec files
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"  Removed {spec_file}")

def create_executable():
    """Create executable using PyInstaller."""
    print("Building Medical Spytool executable...")
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", "Medical_Spytool",
        "--add-data", "src;src",
        "--add-data", "dnb_spytool;dnb_spytool",
        "--hidden-import", "tkinter",
        "--hidden-import", "requests",
        "--hidden-import", "beautifulsoup4",
        "--hidden-import", "pandas",
        "--icon", "assets/icon.ico" if Path("assets/icon.ico").exists() else None,
        "src/main.py"
    ]
    
    # Remove None values
    cmd = [arg for arg in cmd if arg is not None]
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ Executable created successfully!")
        print("Find the executable in the 'dist' folder")
        
        # Show file size
        exe_path = Path("dist/Medical_Spytool.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Executable size: {size_mb:.1f} MB")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        sys.exit(1)

def test_executable():
    """Test the created executable."""
    print("Testing executable...")
    
    exe_path = Path("dist/Medical_Spytool.exe")
    if not exe_path.exists():
        print("✗ Executable not found!")
        return False
    
    try:
        # Test with --help flag
        result = subprocess.run([str(exe_path), "--help"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✓ Executable test passed")
            return True
        else:
            print(f"✗ Executable test failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Executable test timed out")
        return False
    except Exception as e:
        print(f"✗ Executable test error: {e}")
        return False

def main():
    """Main build process."""
    print("Medical Spytool Build Script")
    print("=" * 40)
    
    try:
        # Check requirements
        check_requirements()
        
        # Clean previous builds
        clean_build()
        
        # Create executable
        create_executable()
        
        # Test executable
        test_executable()
        
        print("\n" + "=" * 40)
        print("Build completed successfully!")
        print("Executable location: dist/Medical_Spytool.exe")
        
    except KeyboardInterrupt:
        print("\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
