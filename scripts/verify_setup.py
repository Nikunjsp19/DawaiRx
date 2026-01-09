#!/usr/bin/env python3
"""Verify Phase 0 setup is complete"""

import sys
import os


def check_python_version():
    """Check Python version >= 3.11"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python 3.11+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_directories():
    """Check required directories exist"""
    required_dirs = [
        "src",
        "tests",
        "config",
        "sample_data",
        "out",
    ]
    missing = []
    for dir_name in required_dirs:
        if not os.path.isdir(dir_name):
            missing.append(dir_name)
    
    if missing:
        print(f"❌ Missing directories: {', '.join(missing)}")
        return False
    
    print(f"✅ All required directories exist")
    return True


def check_modules():
    """Check core modules can be imported"""
    try:
        from src.cli.main import cli
        from src.persistence.config import MONGO_URI
        print("✅ Core modules import successfully")
        return True
    except ImportError as e:
        if "pymongo" in str(e) or "pandas" in str(e):
            print(f"⚠️  Dependencies not installed: {e}")
            print("   Run: make install")
            return False
        print(f"❌ Import error: {e}")
        return False


def check_files():
    """Check required files exist"""
    required_files = [
        "requirements.txt",
        "pyproject.toml",
        "docker-compose.yml",
        "Makefile",
        "README.md",
        ".gitignore",
    ]
    missing = []
    for file_name in required_files:
        if not os.path.isfile(file_name):
            missing.append(file_name)
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    
    print("✅ All required files exist")
    return True


def main():
    """Run all checks"""
    print("🔍 Verifying Phase 0 setup...\n")
    
    checks = [
        ("Python version", check_python_version),
        ("Directories", check_directories),
        ("Files", check_files),
        ("Module imports", check_modules),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"Checking {name}...")
        results.append(check_func())
        print()
    
    if all(results):
        print("✅ Phase 0 setup complete!")
        print("\nNext steps:")
        print("  1. Install dependencies: make install")
        print("  2. Start MongoDB: make docker-up")
        print("  3. Test MongoDB: make mongo-test")
        print("  4. Run tests: make test")
        return 0
    else:
        # Check if it's just missing dependencies
        try:
            import pymongo
            import pandas
        except ImportError:
            print("\n💡 Tip: Install dependencies first with: make install")
        print("❌ Setup incomplete. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

