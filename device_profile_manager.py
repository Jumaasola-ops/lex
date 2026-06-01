"""
Device Profile Manager - Generates unique device profiles with QR codes and reports.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib
from adb_manager import ADBManager
from system_analyzer import SystemAnalyzer
from utils import print_success, print_error, print_info, log_info


class DeviceProfileManager:
    """Manages device profiles with unique URLs and data collection."""
    
    def __init__(self, adb_manager: ADBManager):
        """
        Initialize profile manager.
        
        Args:
            adb_manager: ADB manager instance
        """
        self.adb_manager = adb_manager
        self.system_analyzer = SystemAnalyzer(adb_manager)
        self.profiles_dir = Path("reports/profiles")
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_device_profile(self) -> Optional[Dict[str, Any]]:
        """
        Generate a comprehensive device profile with unique ID.
        
        Returns:
            Dict with device profile data or None on error
        """
        try:
            # Generate unique profile ID
            profile_id = str(uuid.uuid4())[:8]
            
            print_info("Collecting device information...")
            
            # Collect device specs
            device_info = self.adb_manager.get_device_info()
            
            # Collect network information
            network_info = self._get_network_info()
            
            # Collect location data
            location_info = self._get_location_data()
            
            # Collect hardware specs
            hardware_info = self._get_hardware_specs()
            
            # Collect connectivity info
            connectivity_info = self._get_connectivity_info()
            
            # Build profile
            profile = {
                "profile_id": profile_id,
                "timestamp": datetime.now().isoformat(),
                "device_specs": device_info,
                "network_info": network_info,
                "location_data": location_info,
                "hardware_specs": hardware_info,
                "connectivity": connectivity_info,
                "installed_apps_count": self._get_installed_apps_count(),
                "system_packages_count": self._get_system_packages_count(),
            }
            
            return profile
            
        except Exception as e:
            print_error(f"Failed to generate profile: {str(e)}")
            return None
    
    def _get_network_info(self) -> Dict[str, str]:
        """Get network information."""
        try:
            network = {}
            
            # Get IP address
            ip_result = self.adb_manager.execute_adb_command("shell ip addr show")
            if ip_result:
                # Extract IPv4 address
                lines = ip_result.split('\n')
                for line in lines:
                    if 'inet ' in line and 'docker' not in line:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            network['ip_address'] = parts[1].split('/')[0]
                            break
            
            # Get WiFi info
            wifi_result = self.adb_manager.execute_adb_command("shell dumpsys connectivity | grep -A 20 'WIFI'")
            if wifi_result and 'connected' in wifi_result.lower():
                network['wifi_status'] = 'Connected'
            
            # Get carrier/network operator
            carrier_result = self.adb_manager.execute_adb_command("shell getprop gsm.nitz.time")
            network['carrier_info'] = carrier_result.strip() if carrier_result else 'Unknown'
            
            return network
        except Exception as e:
            log_info(f"Network info error: {str(e)}")
            return {}
    
    def _get_location_data(self) -> Dict[str, Any]:
        """Get GPS location data and geo coordinates."""
        try:
            location = {
                "gps_enabled": False,
                "latitude": None,
                "longitude": None,
                "accuracy": None,
                "altitude": None,
                "provider": None,
                "last_known_location": None,
            }
            
            # Check if GPS is enabled
            gps_result = self.adb_manager.execute_adb_command("shell settings get secure location_mode")
            if gps_result and gps_result.strip() != '0':
                location['gps_enabled'] = True
            
            # Get last known location from GPS provider
            gps_loc = self._extract_gps_coordinates()
            if gps_loc:
                location.update(gps_loc)
                location['provider'] = 'GPS'
                return location
            
            # Try network provider
            network_loc = self._extract_network_location()
            if network_loc:
                location.update(network_loc)
                location['provider'] = 'Network'
                return location
            
            # Try to get location from any available provider
            all_loc = self._get_all_available_locations()
            if all_loc:
                location.update(all_loc)
                return location
            
            return location
        except Exception as e:
            log_info(f"Location data error: {str(e)}")
            return {}
    
    def _extract_gps_coordinates(self) -> Optional[Dict[str, Any]]:
        """Extract GPS coordinates from device."""
        try:
            # Try to get location via dumpsys
            result = self.adb_manager.execute_adb_command(
                "shell dumpsys location | grep -A 10 'fused location'"
            )
            
            if result and 'latitude' in result.lower():
                coords = self._parse_coordinates_from_string(result)
                if coords:
                    return coords
            
            # Try alternative method
            result = self.adb_manager.execute_adb_command(
                "shell getprop ro.location"
            )
            if result:
                coords = self._parse_coordinates_from_string(result)
                if coords:
                    return coords
            
            return None
        except Exception as e:
            log_info(f"GPS extraction error: {str(e)}")
            return None
    
    def _extract_network_location(self) -> Optional[Dict[str, Any]]:
        """Extract network-based location."""
        try:
            # Try to get network location from location services
            result = self.adb_manager.execute_adb_command(
                "shell dumpsys location | grep -A 5 'network location provider'"
            )
            
            if result:
                coords = self._parse_coordinates_from_string(result)
                if coords:
                    return coords
            
            return None
        except Exception as e:
            log_info(f"Network location extraction error: {str(e)}")
            return None
    
    def _get_all_available_locations(self) -> Optional[Dict[str, Any]]:
        """Get all available location information from device."""
        try:
            result = self.adb_manager.execute_adb_command(
                "shell dumpsys location"
            )
            
            if result:
                # Look for any latitude/longitude in the output
                coords = self._parse_coordinates_from_string(result)
                if coords:
                    return coords
            
            return None
        except Exception as e:
            log_info(f"Location services error: {str(e)}")
            return None
    
    def _parse_coordinates_from_string(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse latitude, longitude, and other coordinates from text.
        
        Args:
            text: Text containing coordinate data
            
        Returns:
            Dictionary with parsed coordinates or None
        """
        import re
        
        coords = {}
        
        # Try to find latitude
        lat_match = re.search(r'latitude[=:\s]+(-?\d+\.?\d*)', text, re.IGNORECASE)
        if lat_match:
            try:
                coords['latitude'] = float(lat_match.group(1))
            except ValueError:
                pass
        
        # Try to find longitude
        lon_match = re.search(r'longitude[=:\s]+(-?\d+\.?\d*)', text, re.IGNORECASE)
        if lon_match:
            try:
                coords['longitude'] = float(lon_match.group(1))
            except ValueError:
                pass
        
        # Try to find accuracy
        acc_match = re.search(r'accuracy[=:\s]+(\d+\.?\d*)', text, re.IGNORECASE)
        if acc_match:
            try:
                coords['accuracy'] = float(acc_match.group(1))
            except ValueError:
                pass
        
        # Try to find altitude
        alt_match = re.search(r'altitude[=:\s]+(-?\d+\.?\d*)', text, re.IGNORECASE)
        if alt_match:
            try:
                coords['altitude'] = float(alt_match.group(1))
            except ValueError:
                pass
        
        return coords if coords else None
    
    def _get_hardware_specs(self) -> Dict[str, str]:
        """Get hardware specifications."""
        try:
            specs = {}
            
            # CPU info
            cpu_result = self.adb_manager.execute_adb_command("shell getprop ro.hardware")
            specs['processor'] = cpu_result.strip() if cpu_result else 'Unknown'
            
            # RAM
            ram_result = self.adb_manager.execute_adb_command("shell getprop ro.build.characteristics")
            specs['build_characteristics'] = ram_result.strip() if ram_result else 'Unknown'
            
            # Screen DPI
            dpi_result = self.adb_manager.execute_adb_command("shell wm density")
            specs['screen_dpi'] = dpi_result.strip() if dpi_result else 'Unknown'
            
            # Display resolution
            res_result = self.adb_manager.execute_adb_command("shell wm size")
            specs['display_resolution'] = res_result.strip() if res_result else 'Unknown'
            
            # Battery
            battery_result = self.adb_manager.execute_adb_command("shell dumpsys battery | grep level")
            if battery_result:
                parts = battery_result.strip().split(':')
                if len(parts) > 1:
                    specs['battery_level'] = parts[1].strip()
            
            return specs
        except Exception as e:
            log_info(f"Hardware specs error: {str(e)}")
            return {}
    
    def _get_connectivity_info(self) -> Dict[str, str]:
        """Get connectivity information (4G/5G/WiFi capabilities)."""
        try:
            connectivity = {
                "wifi": False,
                "bluetooth": False,
                "nfc": False,
                "5g_capable": False,
                "4g_capable": False,
            }
            
            # Check features
            features_result = self.adb_manager.execute_adb_command("shell pm list features")
            if features_result:
                features = features_result.lower()
                connectivity['wifi'] = 'android.hardware.wifi' in features
                connectivity['bluetooth'] = 'android.hardware.bluetooth' in features
                connectivity['nfc'] = 'android.hardware.nfc' in features
            
            # Check for 5G
            radio_result = self.adb_manager.execute_adb_command("shell getprop ro.telephony.use_old_mnc_mcc_format")
            connectivity['4g_capable'] = True  # Default for most phones
            
            return connectivity
        except Exception as e:
            log_info(f"Connectivity info error: {str(e)}")
            return {}
    
    def _get_installed_apps_count(self) -> int:
        """Get count of installed apps."""
        try:
            result = self.adb_manager.execute_adb_command("shell pm list packages | wc -l")
            return int(result.strip()) if result else 0
        except:
            return 0
    
    def _get_system_packages_count(self) -> int:
        """Get count of system packages."""
        try:
            result = self.adb_manager.execute_adb_command("shell pm list packages -s | wc -l")
            return int(result.strip()) if result else 0
        except:
            return 0
    
    def save_profile(self, profile: Dict[str, Any]) -> Optional[Path]:
        """
        Save profile to JSON file.
        
        Args:
            profile: Profile dictionary
            
        Returns:
            Path to saved file or None
        """
        try:
            filename = f"device_profile_{profile['profile_id']}.json"
            filepath = self.profiles_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(profile, f, indent=2)
            
            return filepath
        except Exception as e:
            print_error(f"Failed to save profile: {str(e)}")
            return None
    
    def generate_unique_url(self, profile: Dict[str, Any]) -> str:
        """
        Generate a unique URL for the device profile.
        
        Args:
            profile: Profile dictionary
            
        Returns:
            Unique URL string
        """
        profile_id = profile['profile_id']
        device_hash = hashlib.sha256(
            f"{profile.get('device_specs', {}).get('model', '')}{profile.get('timestamp', '')}"
            .encode()
        ).hexdigest()[:8]
        
        # Create legitimate URL structure
        url = f"https://lex-device-profiles.io/view/{profile_id}/{device_hash}"
        return url
    
    def generate_report(self, profile: Dict[str, Any]) -> str:
        """
        Generate a comprehensive HTML report.
        
        Args:
            profile: Profile dictionary
            
        Returns:
            HTML report string
        """
        profile_id = profile['profile_id']
        url = self.generate_unique_url(profile)
        timestamp = profile['timestamp']
        device_specs = profile.get('device_specs', {})
        hardware = profile.get('hardware_specs', {})
        connectivity = profile.get('connectivity', {})
        network = profile.get('network_info', {})
        location = profile.get('location_data', {})
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>LEX Device Profile - {profile_id}</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f1419; color: #e0e0e0; padding: 20px; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: #1a1e27; border-radius: 10px; padding: 30px; }}
                .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #00ff00; padding-bottom: 20px; }}
                .header h1 {{ color: #00ff00; font-size: 32px; margin-bottom: 10px; }}
                .header p {{ color: #888; }}
                .profile-id {{ background: #2a2e37; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .profile-id strong {{ color: #00ff00; }}
                .section {{ margin: 20px 0; }}
                .section-title {{ color: #00ffff; font-size: 18px; font-weight: bold; margin-bottom: 15px; border-left: 3px solid #00ffff; padding-left: 10px; }}
                .data-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
                .data-item {{ background: #242a35; padding: 12px; border-radius: 5px; }}
                .data-label {{ color: #888; font-size: 12px; text-transform: uppercase; }}
                .data-value {{ color: #00ff00; font-size: 14px; font-weight: bold; margin-top: 5px; }}
                .url-section {{ background: #1f2329; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center; }}
                .url-section a {{ color: #00ffff; text-decoration: none; word-break: break-all; }}
                .qr-code {{ text-align: center; margin: 20px 0; }}
                .qr-code img {{ max-width: 300px; }}
                .footer {{ text-align: center; color: #666; margin-top: 30px; padding-top: 20px; border-top: 1px solid #333; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>LEX_BY ASOLA Device Profile</h1>
                    <p>Comprehensive Device Intelligence Report</p>
                </div>
                
                <div class="profile-id">
                    <strong>Profile ID:</strong> {profile_id}<br>
                    <strong>Generated:</strong> {timestamp}<br>
                    <strong>Status:</strong> <span style="color: #00ff00;">✓ Active</span>
                </div>
                
                <div class="section">
                    <div class="section-title">Device Specifications</div>
                    <div class="data-grid">
                        <div class="data-item">
                            <div class="data-label">Manufacturer</div>
                            <div class="data-value">{device_specs.get('manufacturer', 'Unknown')}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">Model</div>
                            <div class="data-value">{device_specs.get('model', 'Unknown')}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">Android Version</div>
                            <div class="data-value">{device_specs.get('version', 'Unknown')}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">Build Number</div>
                            <div class="data-value">{device_specs.get('build', 'Unknown')}</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">Hardware Information</div>
                    <div class="data-grid">
                        <div class="data-item">
                            <div class="data-label">Processor</div>
                            <div class="data-value">{hardware.get('processor', 'Unknown')}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">Display Resolution</div>
                            <div class="data-value">{hardware.get('display_resolution', 'Unknown')}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">Screen DPI</div>
                            <div class="data-value">{hardware.get('screen_dpi', 'Unknown')}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">Battery Level</div>
                            <div class="data-value">{hardware.get('battery_level', 'Unknown')}</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">Connectivity & Network</div>
                    <div class="data-grid">
                        <div class="data-item">
                            <div class="data-label">WiFi</div>
                            <div class="data-value">{'✓ Enabled' if connectivity.get('wifi') else '✗ Disabled'}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">Bluetooth</div>
                            <div class="data-value">{'✓ Enabled' if connectivity.get('bluetooth') else '✗ Disabled'}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">4G Capable</div>
                            <div class="data-value">{'✓ Yes' if connectivity.get('4g_capable') else '✗ No'}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">5G Capable</div>
                            <div class="data-value">{'✓ Yes' if connectivity.get('5g_capable') else '✗ No'}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">NFC</div>
                            <div class="data-value">{'✓ Enabled' if connectivity.get('nfc') else '✗ Disabled'}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">IP Address</div>
                            <div class="data-value">{network.get('ip_address', 'Unknown')}</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">Location & GPS Coordinates</div>
                    <div class="data-grid">
                        <div class="data-item">
                            <div class="data-label">GPS Status</div>
                            <div class="data-value">{'✓ Enabled' if location.get('gps_enabled') else '✗ Disabled'}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">Location Provider</div>
                            <div class="data-value">{location.get('provider', 'Unknown')}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">Latitude</div>
                            <div class="data-value">{location.get('latitude', 'N/A')}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">Longitude</div>
                            <div class="data-value">{location.get('longitude', 'N/A')}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">Altitude</div>
                            <div class="data-value">{location.get('altitude', 'N/A')} meters</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">Accuracy</div>
                            <div class="data-value">{location.get('accuracy', 'N/A')} meters</div>
                        </div>
                    </div>
                    <div style="margin-top: 15px; padding: 12px; background: #2a2e37; border-radius: 5px; border-left: 3px solid #00ff00;">
                        <strong style="color: #00ff00;">Geo Coordinates:</strong><br>
                        <span style="color: #888; font-size: 12px;">
                            {f"{location.get('latitude', 'N/A')}, {location.get('longitude', 'N/A')}" if location.get('latitude') and location.get('longitude') else "Location data not available"}
                        </span>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">Application Statistics</div>
                    <div class="data-grid">
                        <div class="data-item">
                            <div class="data-label">Total Installed Apps</div>
                            <div class="data-value">{profile.get('installed_apps_count', 0)}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">System Packages</div>
                            <div class="data-value">{profile.get('system_packages_count', 0)}</div>
                        </div>
                    </div>
                </div>
                
                <div class="url-section">
                    <strong>Profile URL:</strong><br>
                    <a href="{url}" target="_blank">{url}</a>
                </div>
                
                <div class="footer">
                    <p>LEX_BY ASOLA Device Profile Report | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Built by Asola Junior | Android Security Intelligence System</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def save_report(self, profile: Dict[str, Any]) -> Optional[Path]:
        """
        Save HTML report to file.
        
        Args:
            profile: Profile dictionary
            
        Returns:
            Path to saved report or None
        """
        try:
            html_content = self.generate_report(profile)
            filename = f"device_report_{profile['profile_id']}.html"
            filepath = self.profiles_dir / filename
            
            with open(filepath, 'w') as f:
                f.write(html_content)
            
            return filepath
        except Exception as e:
            print_error(f"Failed to save report: {str(e)}")
            return None
