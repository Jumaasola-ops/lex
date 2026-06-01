# Android Security Scanner

A comprehensive command-based security and privacy tool for Android devices, designed to scan for malware, detect hidden apps, and manage photo metadata via USB cable connection using ADB (Android Debug Bridge).

## Features

✓ **Malware Detection**
- Scan against known malware signatures database
- Detect suspicious package patterns
- Identify potentially obfuscated app names
- Check for risky permissions

✓ **App Analysis**
- Distinguish between system and user-installed apps
- Detect hidden/system-level apps
- Identify suspicious app behavior
- Analyze dangerous permission usage

✓ **Photo Metadata Management**
- Extract complete EXIF and metadata information
- Remove all sensitive metadata from photos
- Batch process multiple photos
- Preserve image quality after cleaning

✓ **Device Information**
- Get detailed device specifications
- List installed packages
- Retrieve app information
- Monitor device connection status

## Requirements

- **OS**: Windows, macOS, or Linux
- **Python**: 3.8 or higher
- **Android Device**: Android 5.0+
- **USB Debugging**: Enabled on Android device
- **ADB**: Android SDK Platform Tools installed
- **Cable**: USB cable for device connection

## Installation

### 1. Install Android SDK Platform Tools

**Windows:**
```powershell
# Using Chocolatey
choco install android-sdk-platform-tools

# Or download from:
# https://developer.android.com/studio/releases/platform-tools
```

**macOS:**
```bash
# Using Homebrew
brew install android-platform-tools
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install adb

# Or download platform tools manually
```

### 2. Setup Python Environment

```bash
# Clone or download the project
cd android-security-scanner

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Enable USB Debugging on Android Device

1. Go to **Settings → About Phone**
2. Tap **Build Number** 7 times to enable Developer Mode
3. Go to **Settings → Developer Options**
4. Enable **USB Debugging**
5. Connect device to computer via USB

### 4. Verify ADB Connection

```bash
adb devices
```

You should see your device listed as "device".

## Usage

### Command-Line Interface

The tool uses a custom command interface. Basic syntax:

```bash
python main.py <command> [arguments]
```

Or create an alias for easier access:

```bash
# Windows (PowerShell)
function android-security { python main.py @args }

# macOS/Linux (Bash)
alias android-security="python main.py"
```

### Available Commands

#### 1. Full Security Scan
Comprehensive scan of your device:
```bash
python main.py full-scan
```

#### 2. Malware Scanning
Scan for malware and suspicious packages:
```bash
python main.py scan-malware
```

Output includes:
- Known malware threats
- Suspicious package names
- Apps with dangerous permissions
- Potentially hidden apps

#### 3. App Analysis
Analyze installed applications:
```bash
python main.py analyze-apps
```

Output includes:
- Count of system vs user apps
- Hidden apps detection
- Suspicious app indicators
- Dangerous permission analysis

#### 4. Extract Photo Metadata
View all metadata from a photo:
```bash
python main.py extract-metadata <path_to_photo>
```

Example:
```bash
python main.py extract-metadata photo.jpg
```

#### 5. Remove Photo Metadata
Remove metadata from a single photo:
```bash
python main.py remove-metadata <input_photo> [output_path]
```

Example:
```bash
python main.py remove-metadata photo.jpg cleaned_photo.jpg
```

#### 6. Batch Clean Metadata
Remove metadata from multiple photos:
```bash
python main.py batch-clean <input_dir> <output_dir> [extensions]
```

Example:
```bash
python main.py batch-clean ./photos ./cleaned_photos .jpg,.png
```

#### 7. List Packages
List installed packages:
```bash
# All packages
python main.py list-packages

# System packages only
python main.py list-packages --system

# User-installed packages only
python main.py list-packages --user
```

#### 8. Get App Information
Get detailed info about a specific app:
```bash
python main.py app-info <package_name>
```

Example:
```bash
python main.py app-info com.android.chrome
```

#### 9. Device Information
Display device details:
```bash
python main.py device-info
```

#### 10. Help
Display help information:
```bash
python main.py help
python main.py help <command>
```

## Project Structure

```
android-security-scanner/
├── main.py                 # Entry point
├── command_interface.py    # Custom command handler
├── adb_manager.py          # ADB communication wrapper
├── malware_scanner.py      # Malware detection engine
├── app_analyzer.py         # App analysis module
├── metadata_handler.py     # Photo metadata operations
├── config.py               # Configuration and constants
├── exceptions.py           # Custom exception classes
├── utils.py                # Utility functions
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Configuration

Edit `config.py` to customize:

- **ADB Timeout**: `ADB_TIMEOUT` (seconds)
- **Malware Database**: `KNOWN_MALWARE_SIGNATURES` (dict)
- **Suspicious Patterns**: `SUSPICIOUS_PATTERNS` (list)
- **System Packages**: `SYSTEM_PACKAGES` (list)
- **Log Level**: `LOG_LEVEL` (INFO, DEBUG, WARNING, ERROR)

## Security Notes

⚠️ **Important**:

1. **Device Permissions**: This tool requires access to device package information and file systems
2. **USB Debugging**: Only enable USB debugging on trusted computers
3. **Data Privacy**: All scans are performed locally; no data is sent to external servers
4. **Backup**: Consider backing up important data before malware removal
5. **Root Access**: Some features require device to be connected via USB

## Troubleshooting

### ADB not found
```bash
# Verify ADB is installed
adb version

# Add ADB to PATH if needed
# Windows: Add Android SDK platform-tools to system PATH
```

### Device not recognized
```bash
# Check USB connection
adb devices

# Try restarting ADB server
adb kill-server
adb start-server

# Check USB permissions (Linux)
sudo chmod a+rw /dev/bus/usb/*/*
```

### Permission Denied
- Ensure USB Debugging is enabled
- Try disconnecting and reconnecting device
- Restart ADB service

### Slow scans
- Reduce number of packages to check (modify `config.py`)
- Disable certain checks if not needed
- Ensure stable USB connection

## Code Quality

- **PEP 8** compliant code
- **Type hints** for all functions
- **Comprehensive error handling**
- **Logging** for all operations
- **Modular design** for maintainability
- **No external executables** - pure Python/ADB approach

## Limitations

- Malware detection is signature-based (not heuristic)
- Some apps may hide their true functionality
- Requires USB connection (not wireless)
- Depends on accurate malware database
- Limited by device permissions

## Future Enhancements

- [ ] Real-time monitoring
- [ ] Wireless ADB support
- [ ] Machine learning-based detection
- [ ] Custom malware database updates
- [ ] Web UI interface
- [ ] Scheduled scanning
- [ ] Automatic quarantine/removal
- [ ] Network traffic analysis

## Contributing

To improve this tool:

1. Test thoroughly on different Android versions
2. Update malware signatures regularly
3. Report bugs and issues
4. Suggest new features
5. Optimize performance

## License

This project is for educational and personal use only.

## Disclaimer

**Use at your own risk.** This tool performs operations on your Android device. 
Improper use may affect device functionality. Always backup important data before 
using any security scanning or removal features.

## Support

For issues, questions, or suggestions:
- Check the troubleshooting section
- Review logs in the `logs/` directory
- Ensure device is properly connected

---

**Android Security Scanner v1.0**
*Secure your Android device with confidence.*
