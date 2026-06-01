# Android Security Scanner

**Author:** Asola Junior  
**Version:** 1.0.0  
**License:** Educational & Personal Use  
**Status:** Production Ready

---

## Overview

Android Security Scanner is a comprehensive command-line security and privacy analysis tool for Android devices. It provides malware detection, application analysis, and photo metadata management through ADB (Android Debug Bridge) connectivity over USB.

### Core Capabilities

**Malware & Threat Detection**
- Signature-based malware scanning
- Suspicious package pattern recognition
- Obfuscation detection
- Permission risk assessment

**Application Intelligence**
- System vs user-installed app classification
- Hidden/system-level app detection
- Behavioral anomaly identification
- Dangerous permission analysis

**Privacy Management**
- Complete EXIF/metadata extraction
- Metadata sanitization and removal
- Batch processing capabilities
- Image quality preservation

**Device Profiling**
- Complete device specifications
- Package enumeration
- Application inventory
- Connection monitoring

## Features

## System Requirements

| Component | Specification |
|-----------|---------------|
| **OS** | Windows, macOS, or Linux |
| **Python** | 3.8+ |
| **Android Version** | 5.0+ (Best: 5-10) |
| **Python Packages** | See requirements.txt |
| **ADB** | Android SDK Platform Tools |
| **Connection** | USB 2.0+ cable (stable connection) |
| **Storage** | ~100MB free disk space |
| **RAM** | 4GB+ recommended |

**Note:** Compatibility with Android 11+ is reduced due to enhanced security policies. See [Compatibility](#compatibility) section for details.

## Installation

### Step 1: Install Android SDK Platform Tools

#### Windows
```powershell
# Option A: Using Chocolatey (recommended)
choco install android-sdk-platform-tools

# Option B: Manual installation
# Download from: https://developer.android.com/studio/releases/platform-tools
# Extract and add to system PATH
```

#### macOS
```bash
# Using Homebrew
brew install android-platform-tools
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install adb
```

### Step 2: Verify ADB Installation

```bash
adb version
```

### Step 3: Clone/Setup Project

```bash
# Navigate to project directory
cd android-security-scanner

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 4: Enable USB Debugging on Android Device

1. Navigate to **Settings** → **About Phone**
2. Tap **Build Number** 7 times rapidly to unlock Developer Mode
3. Go back to **Settings** → **Developer Options** (now visible)
4. Enable **USB Debugging**
5. Connect device to computer via USB cable
6. Accept the RSA fingerprint dialog on device

### Step 5: Verify Device Connection

```bash
adb devices
```

Expected output:
```
List of attached devices
device_name              device
```

## Usage

### Startup Banner

When you launch the LEX Security Scanner, you'll see a distinctive ASCII art banner displaying the system name and branding:

```
    ██╗     ███████╗██╗  ██╗    ██████╗ ██╗   ██╗    █████╗ ███████╗ ██████╗ ██╗      █████╗ 
    ██║     ██╔════╝╚██╗██╔╝    ██╔══██╗╚██╗ ██╔╝   ██╔══██╗██╔════╝██╔═══██╗██║     ██╔══██╗
    ██║     █████╗   ╚███╔╝     ██████╔╝ ╚████╔╝    ███████║███████╗██║   ██║██║     ███████║
    ██║     ██╔══╝   ██╔██╗     ██╔══██╗  ╚██╔╝     ██╔══██║╚════██║██║   ██║██║     ██╔══██║
    ███████╗███████╗██╔╝ ██╗    ██████╔╝   ██║      ██║  ██║███████║╚██████╔╝███████╗██║  ██║
    ╚══════╝╚══════╝╚═╝  ╚═╝    ╚═════╝    ╚═╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝

    Android Security Intelligence System
    2026-06-01 HH:MM:SS
```

**LEX_BY ASOLA** - Built by Asola Junior

The banner is displayed in vibrant ANSI colors:
- **Red** - LEX portion
- **Green** - BY portion  
- **Yellow** - ASOLA portion
- **Cyan** - System description
- **Magenta** - Timestamp
- **Blue** - Separator lines

This ASCII art is automatically shown every time you run the scanner, providing instant recognition of the LEX security intelligence system.

### Basic Command Syntax

```bash
python main.py <command> [options] [arguments]
```

### Command Reference

#### Security Operations

**Full Security Scan**
```bash
python main.py full-scan
```
Comprehensive scan combining all security checks.

**Malware Detection**
```bash
python main.py scan-malware
```
Scans against known malware signatures and suspicious patterns.

**Application Analysis**
```bash
python main.py analyze-apps
```
Analyzes installed applications for suspicious behavior and permissions.

---

#### Metadata Management

**Extract Metadata**
```bash
python main.py extract-metadata <image_path>
```
Displays all EXIF and metadata information from an image.

**Remove Metadata (Single)**
```bash
python main.py remove-metadata <input_image> [output_path]
```
Removes all metadata from a single image.

**Batch Metadata Removal**
```bash
python main.py batch-clean <input_dir> <output_dir> [extensions]
```
Processes multiple images in a directory.

**Example:**
```bash
python main.py batch-clean ./photos ./cleaned_photos .jpg,.png
```

---

#### Package Management

**List All Packages**
```bash
# All packages
python main.py list-packages

# System packages only
python main.py list-packages --system

# User packages only
python main.py list-packages --user
```

**App Details**
```bash
python main.py app-info <package_name>
```

**Example:**
```bash
python main.py app-info com.android.chrome
```

---

#### Device Information

**Device Specifications**
```bash
python main.py device-info
```

**Help & Documentation**
```bash
python main.py help
python main.py help <command>
```

---

### Quick Aliases (Optional)

For convenience, create command shortcuts:

#### Windows (PowerShell)
```powershell
function android-sec { python main.py @args }
```

#### macOS/Linux (Bash)
```bash
alias android-sec="python main.py"
```

Then use: `android-sec full-scan`

## Architecture

### Project Structure

```
android-security-scanner/
├── main.py                  # Application entry point
├── command_interface.py     # Command router & handler
├── adb_manager.py           # ADB abstraction layer
├── malware_scanner.py       # Threat detection engine
├── app_analyzer.py          # Application analysis module
├── malware_remover.py       # Threat remediation module
├── metadata_handler.py      # Image metadata processor
├── process_analyzer.py      # Process analysis module
├── system_analyzer.py       # System information module
├── file_crawler.py          # File system scanner
├── config.py                # Configuration & constants
├── exceptions.py            # Custom exception classes
├── utils.py                 # Utility functions
├── requirements.txt         # Python dependencies
├── tests.py                 # Unit tests
├── run.bat                  # Windows launcher
├── run.sh                   # Unix launcher
├── logs/                    # Runtime logs
├── malware_db/              # Malware signatures
└── downloads/               # Download directory
```

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `adb_manager.py` | Device communication and command execution |
| `malware_scanner.py` | Signature-based threat detection |
| `app_analyzer.py` | App classification and analysis |
| `metadata_handler.py` | EXIF/metadata extraction and removal |
| `malware_remover.py` | Threat remediation and lock removal |
| `command_interface.py` | CLI command routing and validation |
| `config.py` | Global configuration and signatures |

---

## Configuration

### Customization Options

Edit `config.py` to modify default behavior:

```python
# ADB timeout in seconds
ADB_TIMEOUT = 30

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = "INFO"

# Malware signature database
KNOWN_MALWARE_SIGNATURES = {
    # malware_name: [signatures]
}

# Suspicious package patterns
SUSPICIOUS_PATTERNS = [
    "lockscreen", "locker", "ransomware", 
    "scareware", "warning", "alert"
]

# System package prefixes to whitelist
SYSTEM_PACKAGES = ["android", "com.android", "com.google"]
```

### Environment Variables

```bash
# Set custom log level
export LOG_LEVEL=DEBUG

# Set device ID for multi-device scenarios
export ANDROID_DEVICE_ID=device_serial
```

---

## Security & Privacy

### Important Security Considerations

**⚠️ Data Security**
- All scans execute locally on your device
- No data transmission to external servers
- Network operations are device-only
- Logs stored locally in `logs/` directory

**⚠️ Device Safety**
- Only enable USB Debugging on trusted computers
- Sensitive operations require explicit confirmation
- Backup important data before using remediation features
- Never expose device to untrusted networks while debugging enabled

**⚠️ Access Requirements**
- USB connection required
- ADB access to device file system
- Permission to enumerate installed packages
- Access to system settings and properties

---

## Troubleshooting

### Issue: ADB Not Found

**Symptoms:**
```
adb: command not found
```

**Solutions:**
```bash
# Verify installation
adb version

# Add to PATH (Windows - PowerShell Admin)
$env:Path += ";C:\path\to\android-sdk\platform-tools"

# Verify again
adb devices
```

---

### Issue: Device Not Recognized

**Symptoms:**
```
List of attached devices
```
(Device list is empty)

**Solutions:**
```bash
# Restart ADB server
adb kill-server
adb start-server

# Check physical connection
adb devices

# Linux: Fix USB permissions
sudo chmod a+rw /dev/bus/usb/*/*

# macOS: Restart after connection
adb reconnect
```

---

### Issue: Permission Denied

**Solutions:**
1. Verify USB Debugging is **enabled** in Developer Options
2. Check device for authorization dialog and tap **Allow**
3. Restart both device and ADB server
4. Try different USB port
5. Update device drivers (Windows)

---

### Issue: Slow Scan Performance

**Optimizations:**
```python
# In config.py, reduce scan scope:
SUSPICIOUS_PATTERNS = [  # Fewer patterns
    "lockscreen", "ransomware"
]

# Or filter by app type
python main.py list-packages --user  # User apps only
```

**Hardware Considerations:**
- Use USB 2.0+ cable (not USB-C adapters)
- Keep device close to computer
- Disable antivirus temporary scanning during scan
- Close other USB intensive applications

---

## Architecture Decisions

### Why USB-Only?
- Reliable, authenticated connection
- Immediate termination capability
- Hardware-level access guarantees

### Why Signature-Based Detection?
- Fast performance
- No ML dependencies
- Transparent detection logic
- Easy to update signatures

### Why Modular Design?
- Easy testing and maintenance
- Clear separation of concerns
- Reusable components
- Extensible architecture

---

## Quality Standards

**Code Quality**
- ✅ PEP 8 compliant
- ✅ Type hints on all functions
- ✅ Comprehensive error handling
- ✅ Structured logging
- ✅ Modular architecture

**Testing**
- ✅ Unit tests included
- ✅ Cross-device testing recommended
- ✅ Edge case handling

**Documentation**
- ✅ Inline code comments
- ✅ Function docstrings
- ✅ Usage examples
- ✅ Configuration guide

---

## Known Limitations

| Limitation | Details |
|-----------|---------|
| **Android 11+** | Enhanced SELinux policies reduce effectiveness |
| **Samsung Devices** | Knox security may block some operations |
| **Signature-Based** | Cannot detect novel threats |
| **USB Dependent** | Requires continuous USB connection |
| **App Obfuscation** | May miss well-obfuscated malware |

---

## Roadmap

**Planned Enhancements**
- [ ] Wireless ADB support
- [ ] Machine learning-based detection
- [ ] Real-time process monitoring
- [ ] Automated threat quarantine
- [ ] Web dashboard UI
- [ ] Scheduled scanning
- [ ] Network traffic analysis
- [ ] Custom signature upload

**Compatibility Expansion**
- [ ] iOS support assessment
- [ ] Additional Android versions testing
- [ ] Device-specific optimizations
- [ ] ARM/x86 processor variants

---

## Compatibility

### Tested Devices & Versions

| Android Version | Compatibility | Notes |
|-----------------|---------------|-------|
| 5.0 - 10 | ✅ Excellent | Full feature support |
| 11 - 12 | ⚠️ Good | Some SELinux restrictions |
| 13+ | ⚠️ Limited | Enhanced security policies |
| Stock Android | ✅ Best | Fewest restrictions |
| Samsung (Knox) | ❌ Limited | Security policies block many operations |
| Google Pixel | ✅ Good | Standard Android behavior |

### Device Compatibility Notes

**Best Performance:**
- Stock Android devices
- Android 5-10
- Non-customized ROM

**Known Issues:**
- Samsung devices with Knox may fail lock removal
- Android 13+ has reduced malware database access
- Some manufacturer skins override system settings

---

## Support & Contributing

### Getting Help

1. **Documentation**: Check this README and QUICKSTART.md
2. **Logs**: Review `logs/` directory for detailed error messages
3. **Commands**: Run `python main.py help <command>` for usage

### Contributing Guidelines

To improve this tool:

1. **Testing**: Test on multiple Android versions and devices
2. **Malware Signatures**: Help maintain and update threat database
3. **Bug Reports**: Include device info and logs
4. **Features**: Suggest improvements with use cases
5. **Performance**: Identify and optimize bottlenecks

### Code Contributions

```bash
# Fork and clone the repository
git clone <your-fork>
cd android-security-scanner

# Create feature branch
git checkout -b feature/your-feature

# Make changes and test
python main.py full-scan

# Commit with clear messages
git commit -m "feat: add feature description"

# Push and create pull request
git push origin feature/your-feature
```

---

## License & Disclaimer

### License
Educational and Personal Use Only

### Legal Disclaimer

⚠️ **IMPORTANT**: This tool is provided "AS-IS" for security research and personal device management only.

**Risks & Warnings:**
- Improper use may brick or permanently damage your device
- Unauthorized access to devices is illegal in most jurisdictions
- Always maintain full backups before using remediation features
- Test extensively on non-critical devices first
- The author assumes no liability for misuse or data loss

**Restrictions:**
- Do not use on devices you do not own
- Do not use for unauthorized access
- Do not bypass security for illegal purposes
- Comply with all applicable laws and regulations

---

## Support Resources

| Resource | Purpose |
|----------|---------|
| **Logs** | Detailed debugging information in `logs/` |
| **Help** | `python main.py help [command]` |
| **Issues** | Device connection troubleshooting |
| **Config** | Customization and optimization |

---

## Version Information

| Item | Details |
|------|---------|
| **Version** | 1.0.0 |
| **Author** | Asola Junior |
| **Release Date** | 2026 |
| **Status** | Production Ready |
| **Python** | 3.8+ |
| **ADB** | Latest Platform Tools |

---

## Acknowledgments

Built with attention to:
- Android security best practices
- Software engineering principles
- User privacy and data security
- Cross-platform compatibility
- Code maintainability and clarity

---

**Android Security Scanner**  
*Developed by Asola Junior*  
*Secure your Android device with confidence and control.*
