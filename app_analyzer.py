"""
App analysis module for suspicious and hidden app detection.
"""

from typing import List, Dict, Tuple
from adb_manager import ADBManager
from exceptions import AppAnalysisException
from utils import log_info, log_error, log_warning
from config import SYSTEM_PACKAGES, SUSPICIOUS_PATTERNS


class AppAnalyzer:
    """Analyzes Android apps for suspicious behavior and hidden status."""
    
    def __init__(self, adb_manager: ADBManager) -> None:
        """
        Initialize App Analyzer.
        
        Args:
            adb_manager: ADBManager instance
        """
        self.adb = adb_manager
        self.analysis_results: Dict = {}
    
    def analyze_apps(self) -> Dict:
        """
        Perform comprehensive app analysis.
        
        Returns:
            dict: Analysis results
            
        Raises:
            AppAnalysisException: If analysis fails
        """
        log_info("Starting app analysis...")
        
        try:
            results = {
                "system_apps": 0,
                "user_apps": 0,
                "hidden_apps": [],
                "suspicious_apps": [],
                "dangerous_permissions": [],
            }
            
            # Get all packages
            all_packages = self.adb.get_installed_packages()
            
            # Separate system and user apps
            system_apps = [p for p in all_packages if self._is_system_package(p)]
            user_apps = [p for p in all_packages if not self._is_system_package(p)]
            
            results["system_apps"] = len(system_apps)
            results["user_apps"] = len(user_apps)
            
            log_info(f"System apps: {len(system_apps)}, User apps: {len(user_apps)}")
            
            # Analyze user apps
            for app in user_apps:
                # Check for suspicious characteristics
                if self._is_suspicious_app(app):
                    suspicious_info = self._get_suspicious_indicators(app)
                    results["suspicious_apps"].append({
                        "package": app,
                        "indicators": suspicious_info,
                    })
                
                # Check for hidden status
                if self._is_hidden_app(app):
                    results["hidden_apps"].append(app)
            
            # Check for dangerous permissions
            dangerous = self._check_dangerous_permissions(user_apps)
            results["dangerous_permissions"].extend(dangerous)
            
            log_info("App analysis complete")
            return results
            
        except Exception as e:
            raise AppAnalysisException(f"App analysis failed: {str(e)}")
    
    def _is_system_package(self, package_name: str) -> bool:
        """
        Check if package is a system package.
        
        Args:
            package_name: Package name to check
            
        Returns:
            bool: True if system package
        """
        for system_pkg in SYSTEM_PACKAGES:
            if package_name.startswith(system_pkg):
                return True
        return False
    
    def _is_suspicious_app(self, package_name: str) -> bool:
        """
        Check if app has suspicious characteristics.
        
        Args:
            package_name: Package name to check
            
        Returns:
            bool: True if suspicious
        """
        pkg_lower = package_name.lower()
        
        for pattern in SUSPICIOUS_PATTERNS:
            if pattern in pkg_lower:
                return True
        
        return False
    
    def _get_suspicious_indicators(self, package_name: str) -> List[str]:
        """
        Get list of suspicious indicators for app.
        
        Args:
            package_name: Package name to analyze
            
        Returns:
            List[str]: List of indicators
        """
        indicators = []
        pkg_lower = package_name.lower()
        
        for pattern in SUSPICIOUS_PATTERNS:
            if pattern in pkg_lower:
                indicators.append(f"Contains pattern: '{pattern}'")
        
        # Check for obfuscated names (random strings)
        if self._is_obfuscated_name(package_name):
            indicators.append("Potentially obfuscated package name")
        
        return indicators
    
    def _is_obfuscated_name(self, package_name: str) -> bool:
        """
        Check if package name appears obfuscated.
        
        Args:
            package_name: Package name to check
            
        Returns:
            bool: True if potentially obfuscated
        """
        import re
        
        # Check for random character patterns
        if re.search(r'[a-z]{1,3}\.[a-z]{1,3}$', package_name):
            return True
        
        # Check for single-letter segments
        segments = package_name.split('.')
        if len(segments) >= 3 and all(len(seg) <= 2 for seg in segments):
            return True
        
        return False
    
    def _is_hidden_app(self, package_name: str) -> bool:
        """
        Detect if app is hidden from launcher.
        
        Args:
            package_name: Package name to check
            
        Returns:
            bool: True if hidden
        """
        try:
            returncode, output, _ = self.adb.execute_command(
                f"pm dump {package_name} | grep hidden"
            )
            
            if returncode == 0 and "true" in output.lower():
                return True
            
            return False
        except:
            return False
    
    def _check_dangerous_permissions(self, packages: List[str]) -> List[Dict]:
        """
        Check packages for dangerous permissions.
        
        Args:
            packages: List of package names to check
            
        Returns:
            List[Dict]: List of packages with dangerous permissions
        """
        dangerous_perms = [
            "android.permission.ACCESS_FINE_LOCATION",
            "android.permission.CAMERA",
            "android.permission.RECORD_AUDIO",
            "android.permission.READ_CONTACTS",
            "android.permission.READ_CALL_LOG",
            "android.permission.READ_SMS",
            "android.permission.SEND_SMS",
            "android.permission.MODIFY_AUDIO_SETTINGS",
            "android.permission.WRITE_EXTERNAL_STORAGE",
        ]
        
        results = []
        
        for pkg in packages:
            try:
                returncode, output, _ = self.adb.execute_command(
                    f"dumpsys package {pkg} | grep permission"
                )
                
                if returncode == 0:
                    found_perms = []
                    for perm in dangerous_perms:
                        if perm in output:
                            found_perms.append(perm)
                    
                    if found_perms:
                        results.append({
                            "package": pkg,
                            "permissions": found_perms,
                        })
            except:
                pass
        
        return results
    
    def get_app_info(self, package_name: str) -> Dict:
        """
        Get detailed information about an app.
        
        Args:
            package_name: Package name to get info for
            
        Returns:
            dict: App information
            
        Raises:
            AppAnalysisException: If retrieval fails
        """
        try:
            info = {
                "package_name": package_name,
                "is_system": self._is_system_package(package_name),
                "is_suspicious": self._is_suspicious_app(package_name),
                "is_hidden": self._is_hidden_app(package_name),
            }
            
            # Get package info
            try:
                info["details"] = self.adb.get_package_info(package_name)
            except:
                pass
            
            return info
            
        except Exception as e:
            raise AppAnalysisException(f"Failed to get app info: {str(e)}")
    
    def display_analysis_results(self, results: Dict) -> None:
        """
        Display analysis results in formatted output.
        
        Args:
            results: Analysis results dictionary
        """
        print(f"\n{'='*60}")
        print("  APP ANALYSIS RESULTS")
        print(f"{'='*60}\n")
        
        print(f"System Apps: {results['system_apps']}")
        print(f"User Apps: {results['user_apps']}")
        
        if results["hidden_apps"]:
            print(f"\n⚠ HIDDEN APPS ({len(results['hidden_apps'])}):")
            for app in results["hidden_apps"]:
                print(f"  • {app}")
        else:
            print("\n✓ No hidden apps detected")
        
        if results["suspicious_apps"]:
            print(f"\n⚠ SUSPICIOUS APPS ({len(results['suspicious_apps'])}):")
            for app_info in results["suspicious_apps"]:
                print(f"  • {app_info['package']}")
                for indicator in app_info["indicators"]:
                    print(f"    - {indicator}")
        else:
            print("\n✓ No suspicious apps detected")
        
        if results["dangerous_permissions"]:
            print(f"\n⚠ APPS WITH DANGEROUS PERMISSIONS ({len(results['dangerous_permissions'])}):")
            for item in results["dangerous_permissions"]:
                print(f"  • {item['package']}")
                for perm in item['permissions']:
                    print(f"    - {perm}")
        else:
            print("\n✓ No dangerous permissions found")
