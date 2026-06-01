"""
Wireless ADB Management for network-based device connectivity.
Author: Asola Junior
Enables ADB over TCP/IP without USB connection.
"""

import socket
import re
from typing import Tuple, Optional, List
from dataclasses import dataclass

from utils import log_info, log_error, log_warning
from adb_manager import ADBManager
from config import ADB_PATH


@dataclass
class WirelessDevice:
    """Wireless device connection info."""
    device_id: str
    ip_address: str
    port: int = 5555
    paired: bool = False
    pairing_code: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.ip_address}:{self.port}"


class WirelessADBManager:
    """Manages ADB connections over TCP/IP networks."""
    
    DEFAULT_PORT = 5555
    PAIRING_PORT = 5037
    CONNECTION_TIMEOUT = 10
    
    def __init__(self):
        """Initialize wireless ADB manager."""
        self.adb = ADBManager()
        self.wireless_devices: List[WirelessDevice] = []
    
    def scan_network(self, network_prefix: str = "192.168.1") -> List[WirelessDevice]:
        """
        Scan network for ADB-enabled devices.
        
        Args:
            network_prefix: Network address to scan (default: 192.168.1.x)
            
        Returns:
            List[WirelessDevice]: List of discovered devices
        """
        log_info(f"Scanning network: {network_prefix}.1-254...")
        discovered = []
        
        # Quick scan of common IPs
        common_ports = [192, 168, 1]  # Typical home network
        
        for host_num in range(1, 255):
            ip = f"{network_prefix}.{host_num}"
            if self._check_adb_port(ip):
                device = WirelessDevice(
                    device_id=f"{ip}:{self.DEFAULT_PORT}",
                    ip_address=ip,
                    port=self.DEFAULT_PORT,
                    paired=False
                )
                discovered.append(device)
                self.wireless_devices.append(device)
                log_info(f"Found ADB device at {ip}:{self.DEFAULT_PORT}")
        
        return discovered
    
    def _check_adb_port(self, ip: str, port: int = 5555) -> bool:
        """
        Check if ADB port is open on host.
        
        Args:
            ip: IP address
            port: Port to check
            
        Returns:
            bool: True if port is open
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def enable_wireless_on_device(self, usb_device_id: str) -> Tuple[bool, str]:
        """
        Enable wireless ADB on a USB-connected device.
        
        Args:
            usb_device_id: USB device identifier
            
        Returns:
            Tuple[bool, str]: (success, message or IP:port)
        """
        try:
            # Get device IP
            ip_output = self.adb.execute_command(
                usb_device_id,
                "ip addr show wlan0 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1"
            ).strip()
            
            if not ip_output:
                return False, "Device not connected to WiFi"
            
            ip_address = ip_output
            
            # Enable ADB over network
            port_output = self.adb.execute_command(
                usb_device_id,
                "getprop service.adb.tcp.port"
            ).strip()
            
            if not port_output:
                # Enable TCP listening on default port
                self.adb.execute_command(usb_device_id, "setprop service.adb.tcp.port 5555")
                # Restart ADB daemon
                self.adb.execute_command(usb_device_id, "stop adbd && start adbd")
                log_info(f"Enabled wireless ADB on {usb_device_id}")
            
            wireless_device = WirelessDevice(
                device_id=f"{ip_address}:{self.DEFAULT_PORT}",
                ip_address=ip_address,
                port=self.DEFAULT_PORT,
                paired=True
            )
            
            self.wireless_devices.append(wireless_device)
            return True, f"{ip_address}:{self.DEFAULT_PORT}"
        
        except Exception as e:
            log_error(f"Failed to enable wireless ADB: {e}")
            return False, str(e)
    
    def connect_wireless(self, ip_address: str, port: int = 5555) -> Tuple[bool, str]:
        """
        Connect to wireless ADB device.
        
        Args:
            ip_address: Device IP address
            port: ADB port (default: 5555)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            device_id = f"{ip_address}:{port}"
            
            # Test connectivity first
            if not self._check_adb_port(ip_address, port):
                return False, f"Cannot reach {device_id}"
            
            # Connect using adb connect
            output = self.adb.execute_command(
                None,
                f"connect {ip_address}:{port}"
            )
            
            if "connected" in output.lower() or "already" in output.lower():
                log_info(f"Connected to wireless device: {device_id}")
                
                # Mark as paired and add to list if not exists
                for device in self.wireless_devices:
                    if device.ip_address == ip_address:
                        device.paired = True
                        return True, f"Connected to {device_id}"
                
                self.wireless_devices.append(WirelessDevice(
                    device_id=device_id,
                    ip_address=ip_address,
                    port=port,
                    paired=True
                ))
                return True, f"Connected to {device_id}"
            else:
                return False, f"Connection failed: {output}"
        
        except Exception as e:
            log_error(f"Connection error: {e}")
            return False, str(e)
    
    def disconnect_wireless(self, device_id: str) -> Tuple[bool, str]:
        """
        Disconnect from wireless device.
        
        Args:
            device_id: Device identifier (IP:port)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            output = self.adb.execute_command(None, f"disconnect {device_id}")
            
            # Remove from wireless devices list
            self.wireless_devices = [d for d in self.wireless_devices 
                                     if d.device_id != device_id]
            
            log_info(f"Disconnected from {device_id}")
            return True, f"Disconnected from {device_id}"
        
        except Exception as e:
            log_error(f"Disconnect error: {e}")
            return False, str(e)
    
    def pair_wireless(self, ip_address: str, pairing_code: str) -> Tuple[bool, str]:
        """
        Pair with wireless device using pairing code.
        Requires Android 11+ on device.
        
        Args:
            ip_address: Device IP address
            pairing_code: 6-digit pairing code from device
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not re.match(r'^\d{6}$', pairing_code):
                return False, "Invalid pairing code format (must be 6 digits)"
            
            # Attempt pairing on pairing port
            device_id = f"{ip_address}:{self.PAIRING_PORT}"
            
            output = self.adb.execute_command(
                None,
                f"pair {device_id}"
            )
            
            # This is simplified - actual pairing requires more interaction
            log_warning("Pairing requires manual code entry on device")
            
            return True, "Follow device instructions to complete pairing"
        
        except Exception as e:
            log_error(f"Pairing error: {e}")
            return False, str(e)
    
    def list_wireless_devices(self) -> List[dict]:
        """
        List all wireless devices.
        
        Returns:
            List[dict]: List of connected devices
        """
        devices = []
        for device in self.wireless_devices:
            devices.append({
                "device_id": device.device_id,
                "ip_address": device.ip_address,
                "port": device.port,
                "paired": device.paired,
            })
        return devices
    
    def get_device_info_wireless(self, device_id: str) -> dict:
        """
        Get device information via wireless connection.
        
        Args:
            device_id: Wireless device identifier (IP:port)
            
        Returns:
            dict: Device information
        """
        try:
            info = {
                "device_id": device_id,
                "model": self.adb.execute_command(device_id, "getprop ro.product.model").strip(),
                "manufacturer": self.adb.execute_command(device_id, "getprop ro.product.manufacturer").strip(),
                "android_version": self.adb.execute_command(device_id, "getprop ro.build.version.release").strip(),
                "api_level": self.adb.execute_command(device_id, "getprop ro.build.version.sdk").strip(),
                "connected": True,
            }
            return info
        except Exception as e:
            log_error(f"Failed to get device info: {e}")
            return {"device_id": device_id, "connected": False, "error": str(e)}
    
    def test_wireless_connection(self, device_id: str) -> bool:
        """
        Test wireless connection to device.
        
        Args:
            device_id: Wireless device identifier
            
        Returns:
            bool: True if connection successful
        """
        try:
            # Simple test: get device model
            output = self.adb.execute_command(
                device_id,
                "getprop ro.product.model"
            )
            return len(output) > 0 and "error" not in output.lower()
        except Exception as e:
            log_error(f"Connection test failed: {e}")
            return False
    
    def enable_wireless_permanently(self, device_id: str) -> Tuple[bool, str]:
        """
        Enable wireless ADB permanently (survives reboot).
        Requires root access.
        
        Args:
            device_id: USB device identifier
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Check if device is rooted
            is_root = "root" in self.adb.execute_command(device_id, "whoami")
            
            if not is_root:
                log_warning("Device not rooted, wireless ADB may not persist")
            
            # Enable service
            self.adb.execute_command(
                device_id,
                "setprop persist.adb.tcp.port 5555"
            )
            
            log_info("Wireless ADB configured for persistence")
            return True, "Wireless ADB enabled (may require restart)"
        
        except Exception as e:
            log_error(f"Failed to configure persistence: {e}")
            return False, str(e)


def main():
    """Example usage of wireless ADB manager."""
    manager = WirelessADBManager()
    
    print("\n1. Scanning network for ADB devices...")
    devices = manager.scan_network("192.168.1")
    print(f"Found {len(devices)} device(s)")
    
    print("\n2. Current wireless devices:")
    for dev in manager.list_wireless_devices():
        print(f"  • {dev['device_id']} (Paired: {dev['paired']})")
    
    print("\nWireless ADB Manager ready.")
    print("Use manager.connect_wireless('192.168.1.100') to connect")
    print("Use manager.disconnect_wireless('192.168.1.100:5555') to disconnect")


if __name__ == "__main__":
    main()
