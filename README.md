# Question Assistant Pro 🚀

An ultra-modern automated question assistance tool for Windows with cutting-edge UI and AI-powered intelligence.

## ✨ Features

### Core Functionality
- 🎯 **Automatic Question Detection** - OCR and computer vision for real-time detection
- 🤖 **AI-Powered Research** - Anthropic Claude API integration for intelligent answers
- 🖱️ **Smart Automation** - Human-like mouse and keyboard simulation
- 🔄 **Background Service** - Runs silently as Windows service
- ⚙️ **Highly Configurable** - Customizable timing, pacing, and behavior

### Ultra-Modern UI
- 🎨 **Glassmorphic Design** - Transparent cards with blur effects
- 💫 **Smooth Animations** - 60 FPS transitions and micro-interactions
- 🌈 **Gradient Backgrounds** - Animated color gradients
- 🔲 **Neumorphic Elements** - Soft UI with realistic shadows
- 📱 **Responsive Layout** - Adapts to different screen sizes

### Security & Safety
- 🔐 **Encrypted Storage** - Secure credential management
- 🛡️ **Admin Privilege Handling** - Safe elevation when required
- ⚠️ **Emergency Stop** - ESC key immediately halts all operations
- 📊 **Comprehensive Testing** - Full security test suite included

## 📋 Prerequisites

1. **Windows 10/11** (64-bit)
2. **Python 3.8 or higher** 
3. **Tesseract OCR** (for text extraction)
4. **Visual C++ Redistributable** (usually pre-installed)
5. **Administrator privileges** (for service installation only)

## 🚀 Quick Start

### Option 1: Simple Installation (Recommended)

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/yourusername/NoProct.io.git
   cd NoProct
   ```

2. **Run the installer** (Choose based on your Python version)
   
   For Python 3.12:
   ```bash
   install_py312.bat
   ```
   
   For other Python versions:
   ```bash
   install.bat
   ```
   
   Or install manually with minimal requirements:
   ```bash
   pip install -r requirements_minimal.txt
   ```

3. **Install Tesseract OCR**
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install to default location: `C:\Program Files\Tesseract-OCR\`
   - The installer will add it to PATH automatically

4. **Launch the application**
   ```bash
   python main.py
   ```

### Option 2: Manual Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## 🎮 How to Use

### First Launch

1. **Start the application**
   ```bash
   python main.py
   ```
   The ultra-modern GUI will launch with animations

2. **Configure settings** (Navigate to Configuration)
   - 📝 **Context**: Enter question context (e.g., "Mathematics", "History")
   - ⏱️ **Duration**: Set session time (5-180 minutes)
   - 🔑 **API Key**: Enter Anthropic API key (optional but recommended)
   
3. **Start monitoring**
   - Click the **▶️ Start** button in the header
   - The app will begin monitoring for questions
   - Status indicator shows 🟢 Running

4. **Stop monitoring**
   - Click **⏹️ Stop** button
   - Or press **ESC** key for emergency stop
   - Or use system tray icon

### Navigation

- **🏠 Dashboard** - Real-time statistics and activity monitoring
- **⚙️ Configuration** - Main settings and API configuration
- **📊 Analytics** - Performance metrics and graphs
- **🔬 Advanced** - Feature toggles and service management
- **📝 Logs** - Application logs and debugging
- **ℹ️ About** - Version info and documentation

### Keyboard Shortcuts

- `Ctrl+S` - Start service
- `Ctrl+X` - Stop service
- `Ctrl+Q` - Quit application
- `F1` - Open about page
- `ESC` - Emergency stop (always active)

## 🔧 Advanced Configuration

### Windows Service Installation

For running as a background service:

1. **Open app as Administrator**
2. Navigate to **Advanced Settings**
3. Click **Install Service**
4. Service will auto-start with Windows

### API Key Setup

Get your Anthropic API key:
1. Visit https://console.anthropic.com/
2. Create an account or sign in
3. Generate an API key
4. Enter in Configuration → API Configuration

### Custom Themes

The app supports custom themes. Edit `config/custom_themes.json`:

```json
{
  "my_theme": {
    "bg": "#0a0a0f",
    "accent": "#6366f1",
    "success": "#10b981"
  }
}
```

## 🏗️ Building Executable

Create a standalone `.exe` file:

```bash
# Build executable
build.bat

# Output will be in dist/ folder
```

The executable includes all dependencies and can run on any Windows machine.

## 📁 Project Structure

```
NoProct.io/
├── src/
│   ├── core/                    # Core functionality
│   │   ├── config.py           # Configuration management
│   │   ├── service_manager.py  # Windows service handler
│   │   └── exceptions.py       # Custom exceptions
│   ├── gui_components/          # UI components
│   │   ├── ultra_modern_main.py # Main ultra-modern GUI
│   │   ├── ultra_modern_widgets.py # Custom modern widgets
│   │   ├── themes.py           # Theme management
│   │   └── system_tray.py     # System tray integration
│   ├── detection/              # Detection systems
│   │   ├── detector.py        # Question detection
│   │   └── ml_detector.py     # ML-based detection
│   ├── automation/             # Automation tools
│   │   └── controller.py      # Mouse/keyboard control
│   ├── ai/                     # AI integration
│   │   └── researcher.py      # Claude API integration
│   └── utils/                  # Utilities
│       ├── logger.py          # Logging system
│       ├── security.py        # Security features
│       └── statistics.py      # Stats tracking
├── tests/                      # Test suites
│   ├── test_security_comprehensive.py
│   ├── test_service_security.py
│   └── run_security_tests.py
├── config/                     # Configuration files
├── logs/                       # Application logs
├── templates/                  # Detection templates
├── main.py                    # Entry point
├── uninstall.py              # Uninstaller
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## 🧪 Testing

### Run Security Tests

```bash
# Run all security tests
python tests/run_security_tests.py

# Run specific test suite
python -m unittest tests.test_security_comprehensive

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Manual Testing

1. **Test detection**: Open a webpage with questions
2. **Test automation**: Enable "Test Mode" in Advanced Settings
3. **Test API**: Use "Test Connection" in Configuration

## 🔍 Troubleshooting

### Common Issues

#### Python 3.12 Compatibility
If you're using Python 3.12 and encounter installation errors:
```bash
# Use the Python 3.12 specific installer
install_py312.bat

# Or use minimal requirements
pip install -r requirements_minimal.txt

# If numpy fails, install the compatible version
pip install numpy==1.26.2
```

#### "Tesseract not found"
- Install from: https://github.com/UB-Mannheim/tesseract/wiki
- Verify installation: `tesseract --version`
- Add to PATH if needed

#### "Module not found"
```bash
# Ensure virtual environment is activated
venv\Scripts\activate

# For Python 3.12, use:
pip install -r requirements_minimal.txt

# For other versions:
pip install -r requirements.txt --upgrade
```

#### "Permission denied"
- Run as Administrator for service operations
- Check Windows Defender exceptions
- Verify file permissions

#### "API key invalid"
- Check key format: should start with `sk-`
- Verify internet connection
- Check API usage limits

#### UI Issues
- Update graphics drivers
- Try compatibility mode
- Disable hardware acceleration in Advanced Settings

### Log Files

Check logs for detailed error information:
- `logs/app.log` - General application logs
- `logs/service.log` - Service-specific logs
- `logs/error.log` - Error details

## 🔒 Security

### Data Protection
- API keys encrypted with Fernet encryption
- Credentials stored in Windows Credential Manager
- No data sent to external servers (except API calls)

### Privacy
- All processing done locally
- Screenshots not saved to disk
- Configurable data retention

### Uninstallation
Complete removal options:

**Method 1: Use the UI (Recommended)**
1. Launch the application: `python main.py`
2. Navigate to Advanced Settings (🔬 Advanced in sidebar)
3. Scroll to "Application Management" section
4. Click "Uninstall Application" button

**Method 2: Run Python uninstaller**
```bash
cd C:\Users\Cary\Desktop\NoProct.io
python uninstall.py
```

**Method 3: Batch script (requires admin)**
```bash
cd C:\Users\Cary\Desktop\NoProct.io
# Right-click uninstall.bat and "Run as Administrator"
uninstall.bat
```

**Method 4: Manual removal**
1. Delete the NoProct.io folder
2. Remove `%APPDATA%\QuestionAssistant` if it exists
3. Remove any shortcuts from Desktop or Start Menu

## 🆘 Support

### Getting Help
- Check the [Documentation](docs/)
- View [Common Workflows](docs/common-workflows.md)
- Report issues on [GitHub](https://github.com/yourusername/NoProct.io/issues)

### System Requirements
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space
- **Python**: 3.8 or higher
- **Internet**: Required for AI features

## 📜 License

Private use only. Not for distribution.

## ⚠️ Disclaimer

This tool is for educational and legitimate assistance purposes only. Users are responsible for complying with all applicable rules and regulations in their use of this software.

---

**Version**: 3.0.0  
**Last Updated**: 2024  
**Status**: Active Development