# Quick Start Guide

## First Time Setup

### Windows
```powershell
# Run the setup script
.\run.bat help

# This will:
# 1. Create virtual environment
# 2. Install dependencies
# 3. Display help
```

### macOS/Linux
```bash
# Make script executable
chmod +x run.sh

# Run the setup script
./run.sh help

# This will:
# 1. Create virtual environment
# 2. Install dependencies
# 3. Display help
```

## Common Commands

### 1. Quick Security Check
```bash
# Windows
run.bat full-scan

# macOS/Linux
./run.sh full-scan
```

### 2. Scan for Malware Only
```bash
# Windows
run.bat scan-malware

# macOS/Linux
./run.sh scan-malware
```

### 3. Analyze Suspicious Apps
```bash
# Windows
run.bat analyze-apps

# macOS/Linux
./run.sh analyze-apps
```

### 4. Clean Photo Metadata
```bash
# Single photo
# Windows
run.bat remove-metadata photo.jpg

# macOS/Linux
./run.sh remove-metadata photo.jpg

# Multiple photos
# Windows
run.bat batch-clean .\photos .\cleaned_photos

# macOS/Linux
./run.sh batch-clean ./photos ./cleaned_photos
```

## Using in VS Code

### Run Tasks
1. Open Command Palette: `Ctrl+Shift+P`
2. Type "Tasks: Run Task"
3. Select desired task:
   - Full Security Scan
   - Scan for Malware
   - Analyze Apps
   - Show Device Info
   - Show Help

### Debug
1. Press `F5` to start debugging
2. Set breakpoints with `F9`
3. Step through code with `F10`

## Troubleshooting First Run

### Python Not Found
- Install Python 3.8+ from python.org
- Add Python to PATH

### ADB Not Found
- Install Android SDK Platform Tools
- Add to PATH environment variable
- Run `adb devices` to verify

### Device Not Connected
```bash
# Check connection
adb devices

# If not found, try:
adb kill-server
adb start-server
```

### Permission Issues (Linux/macOS)
```bash
# Make run script executable
chmod +x run.sh

# Fix USB permissions (Linux)
sudo chmod a+rw /dev/bus/usb/*/*
```

## Environment Variables

Set these for custom behavior:

```bash
# Windows
set ANDROID_DEVICE_ID=device123
set LOG_LEVEL=DEBUG

# macOS/Linux
export ANDROID_DEVICE_ID=device123
export LOG_LEVEL=DEBUG
```

## Project Structure Overview

```
android-security-scanner/
├── main.py                 ← Entry point
├── command_interface.py    ← Command handler
├── adb_manager.py          ← Device communication
├── malware_scanner.py      ← Malware detection
├── app_analyzer.py         ← App analysis
├── metadata_handler.py     ← Photo metadata
├── requirements.txt        ← Dependencies
├── run.bat                 ← Windows launcher
├── run.sh                  ← Unix launcher
└── .vscode/                ← VS Code settings
    ├── tasks.json          ← Task definitions
    └── settings.json       ← Editor settings
```

## Getting Help

```bash
# Show all commands
python main.py help

# Get help for specific command
python main.py help scan-malware
python main.py help remove-metadata
```

## Tips for Best Results

1. **Fresh scan**: Restart device before full scan
2. **Backup photos**: Before using batch-clean
3. **USB location**: Keep device nearby for stable connection
4. **Time**: Full scan may take 5-10 minutes
5. **Permissions**: Ensure USB Debug is enabled

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Check [config.py](config.py) for customization options
3. Review [exceptions.py](exceptions.py) for error handling
4. Explore modules for advanced features

---

**Need help?** Check the README or main.py help command.
