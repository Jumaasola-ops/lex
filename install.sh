#!/bin/bash
# LEX_BY ASOLA Installation Script for macOS/Linux
# Downloads and installs LEX security scanner

echo ""
echo "========================================"
echo "LEX_BY ASOLA Security Scanner Installer"
echo "Built by Asola Junior"
echo "========================================"
echo ""

# Check if Python is installed
echo "[*] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "[-] Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "[+] Python found: $PYTHON_VERSION"

# Check if git is installed
echo "[*] Checking git installation..."
if ! command -v git &> /dev/null; then
    echo "[-] Git is not installed"
    echo "Please install git: sudo apt-get install git (Debian/Ubuntu) or brew install git (macOS)"
    exit 1
fi

GIT_VERSION=$(git --version)
echo "[+] Git found: $GIT_VERSION"

# Create installation directory
INSTALL_DIR="$HOME/.lex"

if [ -d "$INSTALL_DIR" ]; then
    echo "[*] LEX directory already exists at $INSTALL_DIR"
    read -p "Do you want to reinstall? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
    else
        exit 0
    fi
fi

# Clone repository
echo "[*] Downloading LEX from GitHub..."
git clone https://github.com/Jumaasola-ops/lex.git "$INSTALL_DIR"

if [ $? -ne 0 ]; then
    echo "[-] Failed to download LEX"
    exit 1
fi

cd "$INSTALL_DIR"
echo "[+] LEX downloaded successfully"

# Create virtual environment
echo "[*] Creating Python virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "[-] Failed to create virtual environment"
    exit 1
fi

# Activate venv and install dependencies
echo "[*] Installing dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt

if [ $? -ne 0 ]; then
    echo "[-] Failed to install dependencies"
    exit 1
fi

echo "[+] Installation completed successfully!"
echo ""
echo "LEX is installed at: $INSTALL_DIR"
echo ""
echo "Next steps:"
echo "1. Navigate to: cd $INSTALL_DIR"
echo "2. Activate venv: source venv/bin/activate"
echo "3. Run LEX: python main.py help"
echo ""
echo "For more info, visit: https://github.com/Jumaasola-ops/lex"
echo ""
