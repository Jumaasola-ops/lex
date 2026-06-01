"""
Configuration and constants for Android Security Scanner.
"""

import os
from pathlib import Path
from typing import List, Dict

# Project paths
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
DOWNLOADS_DIR = BASE_DIR / "downloads"
MALWARE_DB_DIR = BASE_DIR / "malware_db"

# Create directories if they don't exist
LOGS_DIR.mkdir(exist_ok=True)
DOWNLOADS_DIR.mkdir(exist_ok=True)
MALWARE_DB_DIR.mkdir(exist_ok=True)

# Logging
LOG_FILE = LOGS_DIR / "security_scanner.log"
LOG_LEVEL = "INFO"

# ADB Configuration
ADB_TIMEOUT = 30  # seconds
ADB_RETRY_ATTEMPTS = 3

# Malware Signatures Database (Production-ready signatures)
KNOWN_MALWARE_SIGNATURES: Dict[str, List[str]] = {
    "Banking Trojans": [
        "com.android.banker", "com.android.security", "com.zeus",
        "com.android.phone.rpc", "trojan.banker", "com.android.update",
    ],
    "Ransomware": [
        "com.android.locker", "ransomware", "com.android.crypt",
        "simplocker", "cryptolocker", "cerber", "com.android.encrypt",
    ],
    "Spyware": [
        "com.spy", "spyware", "keylogger", "com.android.spy",
        "com.logger", "com.monitor.app", "com.track", "surveillance",
    ],
    "Adware": [
        "com.adware", "ad.fraud", "com.ads.click", "mobilead",
        "pushpush", "leadbolt", "doubleclick.fraud",
    ],
    "Rootkit": [
        "rootkit", "com.android.root", "su.binary", "superuser.hack",
        "com.exploit", "kernel.exploit",
    ],
    "Botnet": [
        "botnet", "com.android.bot", "worm", "propagate.app",
        "com.remote.control", "c2.server",
    ],
    "PUP (Potentially Unwanted Programs)": [
        "com.pushpush", "com.fraudclick", "com.gmoneyapp",
        "inmobi.advert", "admob.fraud",
    ],
}

# Aggressive Suspicious Package Names (for hidden apps detection)
SUSPICIOUS_PATTERNS: List[str] = [
    "hidden", "secret", "spy", "tracker", "monitor", "hack", "crack",
    "malware", "virus", "trojan", "worm", "botnet", "ransomware",
    "keylog", "logger", "stealth", "shadow", "ghost", "invisible",
    "admin", "system.service", "update.app", "security.service",
    "phoneme", "phonebk", "loader", "inject", "hook", "patch",
    "exploit", "vulnerability", "xploit", "payload", "backdoor",
    "root", "su.app", "superuser", "kingo", "towelroot",
]

# Extended System Apps That Should Not Be Flagged
SYSTEM_PACKAGES: List[str] = [
    "android", "com.android", "com.google.android", "com.google.android.gms",
    "com.google.android.apps", "com.sec", "com.samsung", "com.motorola",
    "com.htc", "com.sony", "com.lge", "com.lg", "com.huawei", "com.xiaomi",
    "com.oppo", "com.vivo", "com.oneplus", "com.nokia", "com.asus",
]

# Dangerous File Patterns
DANGEROUS_FILE_PATTERNS: List[str] = [
    ".dex", ".apk", ".elf", ".so",  # Executable files
    "system/bin", "system/xbin", "data/local",  # System directories
    "/data/data/", "/sdcard/", "/system/app/",
]

# Suspicious File Extensions
SUSPICIOUS_FILE_EXTENSIONS: List[str] = [
    ".dex", ".odex", ".apk", ".elf", ".so", ".sh", ".jar", ".zip",
    ".rar", ".7z", ".exe", ".dll", ".msi", ".bin", ".dat",
]

# System Apps That Should Not Be Flagged
SYSTEM_PACKAGES: List[str] = [
    "android",
    "com.android",
    "com.google.android",
    "com.google.android.gms",
    "com.google.android.apps",
    "com.sec",  # Samsung
    "com.samsung",
    "com.motorola",
    "com.htc",
    "com.sony",
    "com.lge",
]

# Photo Metadata Fields
CRITICAL_METADATA_FIELDS: List[str] = [
    "GPS",
    "GPSInfo",
    "DateTime",
    "DateTimeOriginal",
    "DateTimeDigitized",
    "Artist",
    "Copyright",
    "UserComment",
    "Exif",
    "IFDOffset",
]

# Command Configuration
COMMAND_PREFIX = "android-security"
COMMAND_TIMEOUT = 60  # seconds
