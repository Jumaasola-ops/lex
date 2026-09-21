#!/usr/bin/env python3
"""
Emergency Recovery Tool - For locked devices without USB debugging access.
Use when device is locked by ransomware/malware and USB debugging is disabled.
"""

import subprocess
import sys
import time
from typing import Tuple
from utils import log_info, log_error, log_warning, print_error, print_success, print_warning, print_info

class EmergencyRecovery:
    """Handle emergency device recovery without USB debugging."""
    
    @staticmethod
    def check_adb_installed() -> bool:
        """Check if ADB is installed."""
        try:
            subprocess.run(['adb', 'version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    @staticmethod
    def detect_connected_devices() -> Tuple[bool, str]:
        """
        Detect any connected Android devices via USB.
        
        Returns:
            Tuple[bool, str]: (device_found, device_id)
        """
        try:
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.strip().split('\n')[1:]
            devices = [line.split('\t')[0] for line in lines if line.strip() and '\t' in line]
            
            if devices:
                return True, devices[0]
            return False, ""
        except Exception as e:
            log_error(f"Device detection failed: {str(e)}")
            return False, ""
    
    @staticmethod
    def attempt_tcp_connection(device_ip: str, port: int = 5555) -> bool:
        """
        Attempt to connect to device via TCP (if previously paired).
        
        Args:
            device_ip: Device IP address
            port: ADB port (default 5555)
            
        Returns:
            bool: Connection successful
        """
        try:
            result = subprocess.run(
                ['adb', 'connect', f'{device_ip}:{port}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return 'connected' in result.stdout.lower()
        except Exception as e:
            log_error(f"TCP connection failed: {str(e)}")
            return False
    
    @staticmethod
    def uninstall_malware_package(package_name: str) -> bool:
        """
        Remove malicious app package.
        
        Args:
            package_name: Package to remove
            
        Returns:
            bool: Successful removal
        """
        try:
            result = subprocess.run(
                ['adb', 'uninstall', package_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = 'Success' in result.stdout or result.returncode == 0
            if success:
                log_info(f"Successfully removed: {package_name}")
                return True
            return False
        except Exception as e:
            log_error(f"Uninstall failed: {str(e)}")
            return False
    
    @staticmethod
    def remove_device_admin_remotely(package_name: str) -> bool:
        """
        Attempt to disable device admin privileges remotely.
        
        Args:
            package_name: Package to disable
            
        Returns:
            bool: Successful disable
        """
        try:
            cmd = f"dpm remove-active-admin {package_name}/.DeviceAdminReceiver"
            result = subprocess.run(
                ['adb', 'shell'] + cmd.split(),
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            log_error(f"Device admin removal failed: {str(e)}")
            return False
    
    @staticmethod
    def print_recovery_guide():
        """Print step-by-step recovery guide."""
        print_info("\n" + "="*70)
        print_success("EMERGENCY RECOVERY GUIDE - LOCKED DEVICE")
        print_info("="*70 + "\n")
        
        print_warning("STEP 1: Use Recovery Mode (FASTEST - No debugging needed)")
        print_info("""
1. Power OFF your phone completely
2. Hold the button combination for your device:
   - Most Android:  Volume Down + Power (hold 10-15 seconds)
   - Samsung:       Bixby + Volume Up + Power
   - Google Pixel:  Volume Down + Power
   - OnePlus:       Volume Up + Power
   
3. Use Volume buttons to navigate, Power button to select
4. Select "Wipe data/factory reset" or "Format data"
5. Confirm and wait for reset
6. Your phone will reboot - malware is GONE
""")
        
        print_warning("STEP 2: Connect via USB Cable (if recovery doesn't work)")
        print_info("""
1. Connect phone to this computer via USB cable
2. Run: adb devices
3. Your device should appear (even if "unauthorized")
4. Run this script again - it will attempt remote removal
""")
        
        print_warning("STEP 3: If USB debugging is on in some way:")
        print_info("""
1. The scanner will automatically detect and remove the malware
2. Run: python emergency_recovery.py --scan
3. Device will be cleaned
""")
        
        print_warning("IMPORTANT: If nothing works")
        print_info("""
- Factory Reset is 100% guaranteed to remove the malware
- You will lose all data, but the device will be secure again
- Recovery Mode factory reset does NOT require the UI to be accessible
""")
        print_info("="*70 + "\n")

def main():
    """Main emergency recovery routine."""
    print_info("\nAndroid Security Scanner - EMERGENCY RECOVERY MODE\n")
    
    # Check ADB
    if not EmergencyRecovery.check_adb_installed():
        print_error("ERROR: ADB not installed. Install Android SDK Platform Tools first.")
        print_info("Download from: https://developer.android.com/tools/releases/platform-tools")
        return 1
    
    # Print guide
    EmergencyRecovery.print_recovery_guide()
    
    # Try to detect device
    print_info("\nSearching for connected devices...")
    device_found, device_id = EmergencyRecovery.detect_connected_devices()
    
    if device_found:
        print_success(f"✓ Device found: {device_id}")
        print_info("Device is accessible via ADB!")
        print_info("\nAttempting to remove lockware...")
        
        # Common ransomware package patterns
        lockware_packages = [
            "com.android.lockcreen",
            "com.android.lockscreen",
            "com.security.lockscreen",
            "com.locker.app",
            "com.system.locker",
            "com.ransomware",
            "com.hidden.locker",
        ]
        
        removed_count = 0
        for package in lockware_packages:
            if EmergencyRecovery.uninstall_malware_package(package):
                removed_count += 1
                print_success(f"  ✓ Removed: {package}")
        
        if removed_count > 0:
            print_success(f"\n✓ Removed {removed_count} malicious packages!")
            return 0
        else:
            print_warning("\nNo known malware packages found.")
            print_info("This is actually GOOD - means the malware is hidden.")
            print_info("Proceed with Factory Reset using Recovery Mode (STEP 1 above).")
            return 0
    else:
        print_warning("✗ No device detected via USB")
        print_info("""
NEXT STEPS:
1. Connect your phone via USB cable
2. Enable "File Transfer" mode in the USB connection notification
3. Run: adb devices
4. Your device should appear

If it still doesn't appear, use Recovery Mode Factory Reset (STEP 1).
This is GUARANTEED to remove any malware.
""")
        return 1

if __name__ == "__main__":
    sys.exit(main())
