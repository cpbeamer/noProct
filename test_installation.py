#!/usr/bin/env python3
"""
Installation Test Script
Tests that all required components are properly installed and configured
"""

import sys
import os
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_python_version():
    """Check Python version"""
    print("\n🐍 Python Version Check:")
    version = sys.version_info
    print(f"  Current: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("  ✅ Python version OK (3.8+)")
        return True
    else:
        print("  ❌ Python 3.8 or higher required")
        return False

def check_imports():
    """Check if all required modules can be imported"""
    print("\n📦 Checking Required Packages:")
    
    packages = {
        "Core": [
            ("tkinter", "GUI framework"),
            ("customtkinter", "Modern GUI components"),
            ("PIL", "Image processing"),
            ("cv2", "Computer vision"),
            ("numpy", "Numerical computing"),
        ],
        "Automation": [
            ("pyautogui", "Mouse/keyboard control"),
            ("pynput", "Input monitoring"),
            ("mss", "Screen capture"),
            ("pytesseract", "OCR engine"),
        ],
        "AI & Web": [
            ("anthropic", "Claude API"),
            ("requests", "HTTP requests"),
            ("bs4", "Web scraping"),
        ],
        "System": [
            ("win32api", "Windows API"),
            ("psutil", "System monitoring"),
            ("cryptography", "Encryption"),
            ("keyring", "Credential storage"),
        ],
        "ML (Optional)": [
            ("sklearn", "Machine learning"),
            ("torch", "Deep learning"),
        ]
    }
    
    all_ok = True
    optional_missing = []
    
    for category, items in packages.items():
        print(f"\n  {category}:")
        for module_name, description in items:
            try:
                if module_name == "cv2":
                    import cv2
                elif module_name == "PIL":
                    from PIL import Image
                elif module_name == "bs4":
                    from bs4 import BeautifulSoup
                elif module_name == "win32api":
                    import win32api
                elif module_name == "sklearn":
                    import sklearn
                elif module_name == "torch":
                    import torch
                else:
                    __import__(module_name)
                print(f"    ✅ {module_name:20} - {description}")
            except ImportError:
                if category == "ML (Optional)":
                    print(f"    ⚠️  {module_name:20} - {description} (optional)")
                    optional_missing.append(module_name)
                else:
                    print(f"    ❌ {module_name:20} - {description}")
                    all_ok = False
    
    if optional_missing:
        print(f"\n  ℹ️  Optional packages not installed: {', '.join(optional_missing)}")
        print("     These are only needed for advanced ML features")
    
    return all_ok

def check_tesseract():
    """Check Tesseract OCR installation"""
    print("\n🔍 Tesseract OCR Check:")
    
    try:
        import pytesseract
        
        # Check default path
        default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if Path(default_path).exists():
            print(f"  ✅ Found at: {default_path}")
            pytesseract.pytesseract.tesseract_cmd = default_path
        
        # Try to get version
        try:
            version = pytesseract.get_tesseract_version()
            print(f"  ✅ Version: {version}")
            return True
        except:
            print("  ⚠️  Tesseract found but couldn't get version")
            print("  ℹ️  Download from: https://github.com/UB-Mannheim/tesseract/wiki")
            return False
            
    except Exception as e:
        print("  ❌ Tesseract not found or not configured")
        print("  ℹ️  Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        return False

def check_project_structure():
    """Check if project structure is intact"""
    print("\n📁 Project Structure Check:")
    
    required_dirs = [
        "src",
        "src/core",
        "src/gui_components",
        "src/detection",
        "src/automation",
        "src/ai",
        "src/utils",
        "tests",
        "config",
        "logs",
        "templates"
    ]
    
    required_files = [
        "main.py",
        "requirements.txt",
        "README.md",
        "src/gui_components/ultra_modern_main.py",
        "src/gui_components/ultra_modern_widgets.py",
        "src/core/config.py",
        "src/core/service_manager.py"
    ]
    
    all_ok = True
    
    print("  Directories:")
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"    ✅ {dir_path}")
        else:
            print(f"    ❌ {dir_path} - Missing")
            all_ok = False
    
    print("\n  Key Files:")
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"    ✅ {file_path}")
        else:
            print(f"    ❌ {file_path} - Missing")
            all_ok = False
    
    return all_ok

def check_permissions():
    """Check file permissions"""
    print("\n🔐 Permissions Check:")
    
    # Check if we can write to logs directory
    try:
        test_file = Path("logs/test_write.tmp")
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("test")
        test_file.unlink()
        print("  ✅ Can write to logs directory")
    except:
        print("  ❌ Cannot write to logs directory")
        return False
    
    # Check if we can write to config directory
    try:
        test_file = Path("config/test_write.tmp")
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("test")
        test_file.unlink()
        print("  ✅ Can write to config directory")
    except:
        print("  ❌ Cannot write to config directory")
        return False
    
    # Check admin privileges
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if is_admin:
            print("  ✅ Running with administrator privileges")
        else:
            print("  ℹ️  Not running as administrator (required for service installation)")
    except:
        print("  ⚠️  Could not check administrator status")
    
    return True

def test_gui_launch():
    """Test if GUI can be launched"""
    print("\n🖼️ GUI Launch Test:")
    
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        print("  ✅ Tkinter GUI framework working")
        
        import customtkinter as ctk
        print("  ✅ CustomTkinter loaded successfully")
        
        # Try importing the main GUI
        try:
            from src.gui_components.ultra_modern_main import UltraModernAssistant
            print("  ✅ Ultra-modern GUI module loaded")
        except ImportError:
            from src.gui_components.enhanced_main import ModernQuestionAssistant
            print("  ✅ Enhanced GUI module loaded (fallback)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ GUI test failed: {e}")
        return False

def main():
    """Run all installation tests"""
    print_header("QUESTION ASSISTANT - INSTALLATION TEST")
    
    results = []
    
    # Run tests
    results.append(("Python Version", check_python_version()))
    results.append(("Package Imports", check_imports()))
    results.append(("Tesseract OCR", check_tesseract()))
    results.append(("Project Structure", check_project_structure()))
    results.append(("File Permissions", check_permissions()))
    results.append(("GUI Framework", test_gui_launch()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n  Results: {passed}/{total} tests passed")
    print()
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status:8} - {test_name}")
    
    print()
    
    if passed == total:
        print("  🎉 All tests passed! The application is ready to run.")
        print("\n  To start the application, run:")
        print("    python main.py")
    else:
        print("  ⚠️  Some tests failed. Please address the issues above.")
        print("\n  Common fixes:")
        print("    1. Run: pip install -r requirements.txt")
        print("    2. Install Tesseract OCR")
        print("    3. Check file permissions")
    
    print("\n" + "="*60)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())