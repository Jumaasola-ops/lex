"""
ADB (Android Debug Bridge) Manager for device communication.
"""

import subprocess
import re
from typing import List, Optional, Tuple
from exceptions import (
    ADBException,
    ADBConnectionException,
    ADBDeviceNotFound,
    ADBTimeoutException,
)
from utils import log_info, log_error, log_debug, log_warning
from config import ADB_TIMEOUT, ADB_RETRY_ATTEMPTS


class ADBManager:
    """Manages ADB communication with Android devices."""
    
    def __init__(self, device_id: Optional[str] = None) -> None:
        """
        Initialize ADB Manager.
        
        Args:
            device_id: Optional device ID. If None, uses first connected device.
            
        Raises:
            ADBDeviceNotFound: If no device is connected.
        """
        self.device_id = device_id
        self._verify_adb_installed()
        self._get_device_id()
        log_info(f"ADB Manager initialized with device: {self.device_id}")
    
    def _verify_adb_installed(self) -> None:
        """
        Verify ADB is installed and accessible.
        
        Raises:
            ADBException: If ADB is not found.
        """
        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise ADBException("ADB version check failed")
            log_info("ADB is properly installed")
        except FileNotFoundError:
            raise ADBException(
                "ADB is not installed. Please install Android SDK Platform Tools."
            )
        except subprocess.TimeoutExpired:
            raise ADBTimeoutException("ADB version check timed out")
    
    def _get_device_id(self) -> None:
        """
        Get connected device ID.
        
        Raises:
            ADBDeviceNotFound: If no device is connected.
        """
        if self.device_id:
            return
        
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            lines = result.stdout.strip().split('\n')[1:]
            devices = [
                line.split()[0] for line in lines
                if line.strip() and 'device' in line and 'devices' not in line
            ]
            
            if not devices:
                raise ADBDeviceNotFound(
                    "No Android device connected via USB. "
                    "Please connect your device and enable USB debugging."
                )
            
            self.device_id = devices[0]
            log_info(f"Connected device found: {self.device_id}")
            
        except subprocess.TimeoutExpired:
            raise ADBTimeoutException("Device detection timed out")
    
    def execute_command(
        self,
        command: str,
        retry: int = 0,
    ) -> Tuple[int, str, str]:
        """
        Execute ADB command on device.
        
        Args:
            command: Command to execute on device
            retry: Retry attempt number
            
        Returns:
            Tuple[int, str, str]: (return_code, stdout, stderr)
            
        Raises:
            ADBTimeoutException: If command times out
            ADBConnectionException: If connection is lost
        """
        adb_cmd = ["adb", "-s", self.device_id, "shell", command]
        
        try:
            result = subprocess.run(
                adb_cmd,
                capture_output=True,
                text=True,
                timeout=ADB_TIMEOUT,
            )
            
            log_debug(f"Command executed: {command}")
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            if retry < ADB_RETRY_ATTEMPTS:
                log_warning(f"Command timeout, retrying... ({retry + 1}/{ADB_RETRY_ATTEMPTS})")
                return self.execute_command(command, retry + 1)
            raise ADBTimeoutException(f"Command timed out after {ADB_RETRY_ATTEMPTS} retries")
        
        except Exception as e:
            raise ADBConnectionException(f"Failed to execute command: {str(e)}")
    
    def push_file(self, local_path: str, remote_path: str) -> None:
        """
        Push file to device.
        
        Args:
            local_path: Path to local file
            remote_path: Destination path on device
            
        Raises:
            ADBException: If push fails
        """
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "push", local_path, remote_path],
                capture_output=True,
                text=True,
                timeout=ADB_TIMEOUT * 2,
            )
            
            if result.returncode != 0:
                raise ADBException(f"Failed to push file: {result.stderr}")
            
            log_info(f"File pushed: {local_path} -> {remote_path}")
            
        except subprocess.TimeoutExpired:
            raise ADBTimeoutException("File push timed out")
    
    def pull_file(self, remote_path: str, local_path: str) -> None:
        """
        Pull file from device.
        
        Args:
            remote_path: Path to file on device
            local_path: Local destination path
            
        Raises:
            ADBException: If pull fails
        """
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_id, "pull", remote_path, local_path],
                capture_output=True,
                text=True,
                timeout=ADB_TIMEOUT * 2,
            )
            
            if result.returncode != 0:
                raise ADBException(f"Failed to pull file: {result.stderr}")
            
            log_info(f"File pulled: {remote_path} -> {local_path}")
            
        except subprocess.TimeoutExpired:
            raise ADBTimeoutException("File pull timed out")
    
    def get_installed_packages(self) -> List[str]:
        """
        Get list of installed packages on device.
        
        Returns:
            List[str]: List of package names
            
        Raises:
            ADBException: If command fails
        """
        returncode, stdout, stderr = self.execute_command("pm list packages")
        
        if returncode != 0:
            raise ADBException(f"Failed to list packages: {stderr}")
        
        packages = [
            line.replace("package:", "").strip()
            for line in stdout.strip().split('\n')
            if line.startswith("package:")
        ]
        
        log_info(f"Retrieved {len(packages)} installed packages")
        return packages
    
    def get_package_info(self, package_name: str) -> dict:
        """
        Get detailed information about a package.
        
        Args:
            package_name: Package name
            
        Returns:
            dict: Package information
            
        Raises:
            ADBException: If command fails
        """
        returncode, stdout, stderr = self.execute_command(
            f"dumpsys package {package_name}"
        )
        
        if returncode != 0:
            raise ADBException(f"Failed to get package info: {stderr}")
        
        info = {
            "package_name": package_name,
            "raw_output": stdout,
        }
        
        # Parse relevant information
        for line in stdout.split('\n'):
            if "versionName=" in line:
                info["version"] = line.split("versionName=")[1].split()[0]
            elif "versionCode=" in line:
                info["version_code"] = line.split("versionCode=")[1].split()[0]
        
        return info
    
    def get_device_info(self) -> dict:
        """
        Get device information.
        
        Returns:
            dict: Device information
        """
        device_info = {
            "device_id": self.device_id,
        }
        
        # Get Android version
        returncode, stdout, stderr = self.execute_command("getprop ro.build.version.release")
        if returncode == 0:
            device_info["android_version"] = stdout.strip()
        
        # Get manufacturer
        returncode, stdout, stderr = self.execute_command("getprop ro.manufacturer")
        if returncode == 0:
            device_info["manufacturer"] = stdout.strip()
        
        # Get model
        returncode, stdout, stderr = self.execute_command("getprop ro.model")
        if returncode == 0:
            device_info["model"] = stdout.strip()
        
        log_info(f"Device info: {device_info}")
        return device_info
    
    def get_comprehensive_device_info(self) -> dict:
        """
        Get comprehensive device information including hardware, storage, and system details.
        
        Returns:
            dict: Comprehensive device information
        """
        info = {}
        
        # === DEVICE IDENTIFICATION ===
        info["device_identification"] = {}
        
        # Device ID / Serial
        returncode, stdout, stderr = self.execute_command("getprop ro.serialno")
        if returncode == 0:
            info["device_identification"]["serial_number"] = stdout.strip()
        
        # IMEI (may require root)
        returncode, stdout, stderr = self.execute_command("dumpsys iphonesubinfo | grep 'Device ID'")
        if returncode == 0 and stdout.strip():
            imei = stdout.strip().split()[-1]
            info["device_identification"]["imei"] = imei
        else:
            # Try alternative method
            returncode, stdout, stderr = self.execute_command("getprop gsm.imei")
            if returncode == 0:
                info["device_identification"]["imei"] = stdout.strip()
        
        # Manufacturer
        returncode, stdout, stderr = self.execute_command("getprop ro.manufacturer")
        if returncode == 0:
            info["device_identification"]["manufacturer"] = stdout.strip()
        
        # Brand
        returncode, stdout, stderr = self.execute_command("getprop ro.product.brand")
        if returncode == 0:
            info["device_identification"]["brand"] = stdout.strip()
        
        # Model
        returncode, stdout, stderr = self.execute_command("getprop ro.model")
        if returncode == 0:
            info["device_identification"]["model"] = stdout.strip()
        
        # Device name
        returncode, stdout, stderr = self.execute_command("getprop ro.product.device")
        if returncode == 0:
            info["device_identification"]["device_name"] = stdout.strip()
        
        # === OPERATING SYSTEM ===
        info["operating_system"] = {}
        
        # Android version
        returncode, stdout, stderr = self.execute_command("getprop ro.build.version.release")
        if returncode == 0:
            info["operating_system"]["android_version"] = stdout.strip()
        
        # API Level
        returncode, stdout, stderr = self.execute_command("getprop ro.build.version.sdk")
        if returncode == 0:
            info["operating_system"]["api_level"] = stdout.strip()
        
        # Build number
        returncode, stdout, stderr = self.execute_command("getprop ro.build.display.id")
        if returncode == 0:
            info["operating_system"]["build_number"] = stdout.strip()
        
        # Build fingerprint
        returncode, stdout, stderr = self.execute_command("getprop ro.build.fingerprint")
        if returncode == 0:
            info["operating_system"]["build_fingerprint"] = stdout.strip()
        
        # Host
        returncode, stdout, stderr = self.execute_command("getprop ro.build.host")
        if returncode == 0:
            info["operating_system"]["build_host"] = stdout.strip()
        
        # === HARDWARE SPECS ===
        info["hardware"] = {}
        
        # CPU cores
        returncode, stdout, stderr = self.execute_command("nproc")
        if returncode == 0:
            info["hardware"]["cpu_cores"] = stdout.strip()
        
        # CPU architecture
        returncode, stdout, stderr = self.execute_command("getprop ro.product.cpu.abi")
        if returncode == 0:
            info["hardware"]["cpu_architecture"] = stdout.strip()
        
        # RAM
        returncode, stdout, stderr = self.execute_command("cat /proc/meminfo | grep MemTotal")
        if returncode == 0:
            try:
                ram_kb = int(stdout.split()[1])
                ram_gb = ram_kb / 1024 / 1024
                info["hardware"]["total_ram_gb"] = f"{ram_gb:.2f} GB ({ram_kb} KB)"
            except:
                info["hardware"]["total_ram"] = stdout.strip()
        
        # Available RAM
        returncode, stdout, stderr = self.execute_command("cat /proc/meminfo | grep MemAvailable")
        if returncode == 0:
            try:
                ram_kb = int(stdout.split()[1])
                ram_gb = ram_kb / 1024 / 1024
                info["hardware"]["available_ram_gb"] = f"{ram_gb:.2f} GB"
            except:
                pass
        
        # Battery
        returncode, stdout, stderr = self.execute_command("dumpsys battery | grep -E 'level|temperature|health|status'")
        if returncode == 0 and stdout.strip():
            battery_lines = stdout.strip().split('\n')
            info["hardware"]["battery"] = {}
            for line in battery_lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    info["hardware"]["battery"][key.strip()] = value.strip()
        
        # === STORAGE ===
        info["storage"] = {}
        
        # Total storage
        returncode, stdout, stderr = self.execute_command("df /data | tail -1")
        if returncode == 0:
            parts = stdout.split()
            if len(parts) >= 4:
                try:
                    total_kb = int(parts[1])
                    used_kb = int(parts[2])
                    free_kb = int(parts[3])
                    total_gb = total_kb / 1024 / 1024
                    used_gb = used_kb / 1024 / 1024
                    free_gb = free_kb / 1024 / 1024
                    info["storage"]["data_partition"] = {
                        "total_gb": f"{total_gb:.2f} GB",
                        "used_gb": f"{used_gb:.2f} GB",
                        "free_gb": f"{free_gb:.2f} GB",
                        "usage_percent": f"{(used_kb/total_kb*100):.1f}%"
                    }
                except:
                    pass
        
        # System storage
        returncode, stdout, stderr = self.execute_command("df /system | tail -1")
        if returncode == 0:
            parts = stdout.split()
            if len(parts) >= 4:
                try:
                    total_kb = int(parts[1])
                    used_kb = int(parts[2])
                    total_gb = total_kb / 1024 / 1024
                    used_gb = used_kb / 1024 / 1024
                    info["storage"]["system_partition"] = {
                        "total_gb": f"{total_gb:.2f} GB",
                        "used_gb": f"{used_gb:.2f} GB",
                        "usage_percent": f"{(used_kb/total_kb*100):.1f}%"
                    }
                except:
                    pass
        
        # Internal storage
        returncode, stdout, stderr = self.execute_command("df /storage/emulated | tail -1")
        if returncode == 0:
            parts = stdout.split()
            if len(parts) >= 4:
                try:
                    total_kb = int(parts[1])
                    used_kb = int(parts[2])
                    total_gb = total_kb / 1024 / 1024
                    used_gb = used_kb / 1024 / 1024
                    info["storage"]["internal_storage"] = {
                        "total_gb": f"{total_gb:.2f} GB",
                        "used_gb": f"{used_gb:.2f} GB",
                        "usage_percent": f"{(used_kb/total_kb*100):.1f}%"
                    }
                except:
                    pass
        
        # === NETWORK & CONNECTIVITY ===
        info["connectivity"] = {}
        
        # WiFi MAC
        returncode, stdout, stderr = self.execute_command("getprop ro.wifi.mac")
        if returncode == 0:
            info["connectivity"]["wifi_mac"] = stdout.strip()
        
        # Bluetooth MAC
        returncode, stdout, stderr = self.execute_command("getprop ro.bluetooth.chipset")
        if returncode == 0:
            info["connectivity"]["bluetooth_chipset"] = stdout.strip()
        
        # === SECURITY ===
        info["security"] = {}
        
        # Security patch level
        returncode, stdout, stderr = self.execute_command("getprop ro.build.version.security_patch")
        if returncode == 0:
            info["security"]["security_patch_level"] = stdout.strip()
        
        # SELinux
        returncode, stdout, stderr = self.execute_command("getenforce")
        if returncode == 0:
            info["security"]["selinux_status"] = stdout.strip()
        
        # === SENSORS ===
        info["sensors"] = {}
        
        returncode, stdout, stderr = self.execute_command("dumpsys sensorservice | head -30")
        if returncode == 0:
            sensor_lines = stdout.strip().split('\n')[:15]
            info["sensors"]["list"] = sensor_lines
        
        # === DISPLAY ===
        info["display"] = {}
        
        # Resolution
        returncode, stdout, stderr = self.execute_command("wm size")
        if returncode == 0:
            info["display"]["resolution"] = stdout.strip()
        
        # Density
        returncode, stdout, stderr = self.execute_command("wm density")
        if returncode == 0:
            info["display"]["density"] = stdout.strip()
        
        # === SYSTEM PROPERTIES ===
        info["system_properties"] = {}
        
        # Bootloader
        returncode, stdout, stderr = self.execute_command("getprop ro.bootloader")
        if returncode == 0:
            info["system_properties"]["bootloader"] = stdout.strip()
        
        # Kernel version
        returncode, stdout, stderr = self.execute_command("uname -r")
        if returncode == 0:
            info["system_properties"]["kernel_version"] = stdout.strip()
        
        # Boot mode
        returncode, stdout, stderr = self.execute_command("getprop ro.boot.serialno")
        if returncode == 0:
            info["system_properties"]["boot_serial"] = stdout.strip()
        
        log_info("Comprehensive device info retrieved")
        return info
    
    def is_device_connected(self) -> bool:
        """
        Check if device is still connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            returncode, _, _ = self.execute_command("echo 'ping'")
            return returncode == 0
        except:
            return False
