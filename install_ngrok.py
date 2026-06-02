#!/usr/bin/env python3
"""
Install ngrok binary with extended timeout for slow connections.
"""
import os
import sys
from urllib.request import urlopen
from urllib.error import URLError
import zipfile
import tempfile
from pathlib import Path

def download_ngrok():
    """Download ngrok binary with extended timeout."""
    # Platform detection
    import platform
    system = platform.system()
    machine = platform.machine()
    
    if system == "Windows":
        arch = "windows-amd64" if "64" in machine else "windows-386"
        filename = "ngrok-v3-stable-windows-amd64.zip"
    elif system == "Darwin":
        arch = "darwin-amd64" if machine == "x86_64" else "darwin-arm64"
        filename = f"ngrok-v3-stable-{arch}.zip"
    else:  # Linux
        arch = "linux-amd64" if machine == "x86_64" else "linux-386"
        filename = f"ngrok-v3-stable-{arch}.zip"
    
    url = f"https://bin.ngrok.com/c/bNyj1mQVY4c/{filename}"
    print(f"Downloading ngrok from: {url}")
    print("This may take a few minutes on slow connections...")
    
    try:
        # Use 5 minute timeout
        response = urlopen(url, timeout=300)
        print(f"Download started, received {response.status} OK")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            tmp_path = tmp.name
            downloaded = 0
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                tmp.write(chunk)
                downloaded += len(chunk)
                if downloaded % (1024*1024) == 0:  # Print every 1MB
                    print(f"Downloaded {downloaded / (1024*1024):.1f} MB...")
        
        # Extract ngrok
        extract_dir = Path(os.path.expanduser("~/.ngrok2"))
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Extracting to {extract_dir}...")
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        os.unlink(tmp_path)
        ngrok_path = extract_dir / "ngrok"
        if system == "Windows":
            ngrok_path = extract_dir / "ngrok.exe"
        
        # Make executable on Unix
        if system != "Windows":
            os.chmod(ngrok_path, 0o755)
        
        print(f"✓ ngrok installed successfully at {ngrok_path}")
        return True
        
    except URLError as e:
        print(f"✗ Download failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = download_ngrok()
    sys.exit(0 if success else 1)
