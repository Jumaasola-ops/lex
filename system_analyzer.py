"""
System-level analyzer for deep device inspection.
"""

from typing import List, Dict
from adb_manager import ADBManager
from exceptions import SystemAnalyzerException
from utils import log_info, log_error, log_warning


class SystemAnalyzer:
    """Performs deep system-level analysis for security threats."""
    
    def __init__(self, adb_manager: ADBManager) -> None:
        """
        Initialize System Analyzer.
        
        Args:
            adb_manager: ADBManager instance
        """
        self.adb = adb_manager
    
    def analyze_system_integrity(self) -> Dict:
        """
        Analyze system integrity for tampering.
        
        Returns:
            dict: System integrity check results
        """
        log_info("Analyzing system integrity...")
        
        results = {
            "is_rooted": False,
            "has_su_binary": False,
            "has_xposed_framework": False,
            "selinux_status": "unknown",
            "system_modifications": [],
            "suspicious_settings": [],
            "build_properties": {},
        }
        
        try:
            # Check for rooting
            results["is_rooted"] = self._check_if_rooted()
            results["has_su_binary"] = self._check_su_binary()
            results["has_xposed_framework"] = self._check_xposed()
            
            # Check SELinux status
            results["selinux_status"] = self._get_selinux_status()
            
            # Check for system modifications
            results["system_modifications"] = self._check_system_modifications()
            
            # Check for suspicious settings
            results["suspicious_settings"] = self._check_suspicious_settings()
            
            # Get build properties
            results["build_properties"] = self._get_build_properties()
            
            return results
            
        except Exception as e:
            raise SystemAnalyzerException(f"System integrity analysis failed: {str(e)}")
    
    def _check_if_rooted(self) -> bool:
        """Check if device is rooted."""
        try:
            # Test for su access
            returncode, _, _ = self.adb.execute_command("su -c 'id'")
            if returncode == 0:
                log_warning("Device appears to be rooted!")
                return True
            
            # Check for common rooting tools
            rooting_indicators = [
                "/system/xbin/su",
                "/system/bin/su",
                "/system/app/Superuser.apk",
                "/data/app/Superuser.apk",
                "/data/app/SuperSU.apk",
            ]
            
            for indicator in rooting_indicators:
                returncode, _, _ = self.adb.execute_command(f"test -f {indicator} && echo found")
                if returncode == 0:
                    log_warning(f"Rooting tool found: {indicator}")
                    return True
            
            return False
        except:
            return False
    
    def _check_su_binary(self) -> bool:
        """Check for su binary."""
        try:
            returncode, _, _ = self.adb.execute_command(
                "which su && echo 'SU found'"
            )
            return returncode == 0
        except:
            return False
    
    def _check_xposed(self) -> bool:
        """Check for Xposed framework."""
        try:
            returncode, output, _ = self.adb.execute_command(
                "ls -la /system/xposed* 2>/dev/null"
            )
            return returncode == 0 and output.strip() != ""
        except:
            return False
    
    def _get_selinux_status(self) -> str:
        """Get SELinux status."""
        try:
            returncode, stdout, _ = self.adb.execute_command(
                "getenforce"
            )
            if returncode == 0:
                return stdout.strip()
            return "unknown"
        except:
            return "unknown"
    
    def _check_system_modifications(self) -> List[Dict]:
        """Check for system file modifications."""
        modifications = []
        
        try:
            # Check for modified system apps
            returncode, stdout, _ = self.adb.execute_command(
                "find /system/app -name '*.apk' -newer /system/framework/framework.jar 2>/dev/null"
            )
            
            if returncode == 0 and stdout:
                modified_apps = stdout.strip().split('\n')
                for app in modified_apps:
                    if app.strip():
                        modifications.append({
                            "type": "Modified System App",
                            "path": app.strip(),
                            "severity": "HIGH",
                        })
            
            # Check for injected libraries
            returncode, stdout, _ = self.adb.execute_command(
                "find /system/lib -name '*.so' -newer /system/bin/app_process 2>/dev/null | grep -i inject"
            )
            
            if returncode == 0 and stdout:
                injected = stdout.strip().split('\n')
                for lib in injected:
                    if lib.strip():
                        modifications.append({
                            "type": "Injected Library",
                            "path": lib.strip(),
                            "severity": "CRITICAL",
                        })
            
            return modifications
            
        except Exception as e:
            log_error(f"System modification check failed: {str(e)}")
            return modifications
    
    def _check_suspicious_settings(self) -> List[Dict]:
        """Check system settings for suspicious values."""
        suspicious = []
        
        try:
            # Check for unknown device administrators
            returncode, stdout, _ = self.adb.execute_command(
                "dumpsys device_policy"
            )
            
            if returncode == 0:
                if "test" in stdout.lower() or "admin" in stdout.lower():
                    suspicious.append({
                        "setting": "Unknown Device Administrators",
                        "value": "Detected",
                        "severity": "MEDIUM",
                    })
            
            # Check accessibility services
            returncode, stdout, _ = self.adb.execute_command(
                "dumpsys accessibility | grep 'mEnabledServices'"
            )
            
            if returncode == 0 and stdout:
                if len(stdout.strip()) > 50:  # Multiple services
                    suspicious.append({
                        "setting": "Accessibility Services",
                        "value": "Multiple services enabled",
                        "severity": "MEDIUM",
                    })
            
            # Check USB debugging status
            returncode, stdout, _ = self.adb.execute_command(
                "getprop persist.sys.usb.config"
            )
            
            if returncode == 0 and "adb" in stdout.lower():
                suspicious.append({
                    "setting": "USB Debugging",
                    "value": "Enabled",
                    "severity": "LOW",
                })
            
            return suspicious
            
        except Exception as e:
            log_error(f"Suspicious settings check failed: {str(e)}")
            return suspicious
    
    def _get_build_properties(self) -> Dict[str, str]:
        """Get device build properties."""
        properties = {}
        
        try:
            key_properties = [
                "ro.build.fingerprint",
                "ro.build.version.release",
                "ro.build.version.sdk",
                "ro.product.manufacturer",
                "ro.product.model",
                "ro.product.brand",
                "ro.bootloader",
                "ro.build.date.utc",
                "ro.build.tags",
            ]
            
            for prop in key_properties:
                returncode, stdout, _ = self.adb.execute_command(
                    f"getprop {prop}"
                )
                if returncode == 0:
                    properties[prop] = stdout.strip()
            
            return properties
            
        except Exception as e:
            log_error(f"Failed to get build properties: {str(e)}")
            return properties
    
    def check_security_patches(self) -> Dict:
        """Check for missing security patches."""
        log_info("Checking security patch level...")
        
        results = {
            "patch_level": "unknown",
            "days_since_patch": "unknown",
            "is_vulnerable": False,
        }
        
        try:
            returncode, stdout, _ = self.adb.execute_command(
                "getprop ro.build.version.security_patch"
            )
            
            if returncode == 0:
                patch_level = stdout.strip()
                results["patch_level"] = patch_level
                
                # Simple check: patches older than 6 months might be vulnerable
                if patch_level and len(patch_level) >= 7:
                    # Extract year and month
                    try:
                        year_month = patch_level[:7]  # YYYY-MM format
                        from datetime import datetime
                        patch_date = datetime.strptime(year_month, "%Y-%m")
                        current_date = datetime.now()
                        days_diff = (current_date - patch_date).days
                        
                        results["days_since_patch"] = str(days_diff)
                        
                        if days_diff > 180:  # More than 6 months
                            results["is_vulnerable"] = True
                            log_warning(f"Device has old security patches: {days_diff} days old")
                    except:
                        pass
            
            return results
            
        except Exception as e:
            log_error(f"Security patch check failed: {str(e)}")
            return results


class SystemAnalyzerException(Exception):
    """Exception raised during system analysis."""
    pass
