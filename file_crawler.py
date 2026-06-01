"""
Aggressive file system crawler for Android device scanning.
"""

from typing import List, Dict, Tuple, Set
from adb_manager import ADBManager
from exceptions import FileCrawlerException
from utils import log_info, log_error, log_warning, print_warning
from config import DANGEROUS_FILE_PATTERNS, SUSPICIOUS_FILE_EXTENSIONS


class FileCrawler:
    """Crawls and analyzes file system for security threats."""
    
    def __init__(self, adb_manager: ADBManager) -> None:
        """
        Initialize File Crawler.
        
        Args:
            adb_manager: ADBManager instance
        """
        self.adb = adb_manager
        self.suspicious_files: List[Dict] = []
        self.dangerous_dirs = [
            "/data/data/",
            "/data/app/",
            "/system/app/",
            "/system/priv-app/",
            "/system/bin/",
            "/system/xbin/",
            "/data/local/",
            "/data/local/tmp/",
            "/cache/",
            "/sdcard/",
            "/storage/emulated/0/",
        ]
    
    def crawl_system(self) -> Dict:
        """
        Perform aggressive system file crawl.
        
        Returns:
            dict: Crawl results with suspicious files
        """
        log_info("Starting aggressive system file crawl...")
        
        results = {
            "suspicious_files": [],
            "hidden_executables": [],
            "modified_system_files": [],
            "suspicious_scripts": [],
            "total_files_scanned": 0,
        }
        
        try:
            # Crawl each dangerous directory
            for directory in self.dangerous_dirs:
                log_info(f"Crawling directory: {directory}")
                
                try:
                    files = self._list_directory(directory)
                    results["total_files_scanned"] += len(files)
                    
                    # Analyze each file
                    for file_path in files:
                        file_info = self._analyze_file(file_path)
                        
                        if file_info["is_suspicious"]:
                            results["suspicious_files"].append(file_info)
                        
                        if file_info["is_hidden_executable"]:
                            results["hidden_executables"].append(file_info)
                        
                        if file_info["is_script"]:
                            results["suspicious_scripts"].append(file_info)
                        
                        if file_info["is_modified_system"]:
                            results["modified_system_files"].append(file_info)
                
                except Exception as e:
                    log_warning(f"Failed to crawl {directory}: {str(e)}")
            
            log_info(f"File crawl complete. Found {len(results['suspicious_files'])} suspicious files")
            return results
            
        except Exception as e:
            raise FileCrawlerException(f"System crawl failed: {str(e)}")
    
    def _list_directory(self, directory: str) -> List[str]:
        """
        List files in directory recursively.
        
        Args:
            directory: Directory path to scan
            
        Returns:
            List[str]: List of file paths
        """
        try:
            # Use find command for efficient recursive search
            returncode, stdout, stderr = self.adb.execute_command(
                f"find {directory} -type f 2>/dev/null | head -1000"
            )
            
            if returncode == 0 and stdout:
                files = [f.strip() for f in stdout.split('\n') if f.strip()]
                return files
            
            return []
        except:
            return []
    
    def _analyze_file(self, file_path: str) -> Dict:
        """
        Analyze individual file for suspicious characteristics.
        
        Args:
            file_path: Path to file
            
        Returns:
            dict: Analysis results
        """
        analysis = {
            "file_path": file_path,
            "is_suspicious": False,
            "is_hidden_executable": False,
            "is_script": False,
            "is_modified_system": False,
            "risk_level": "LOW",
            "reasons": [],
        }
        
        try:
            # Get file properties
            returncode, output, _ = self.adb.execute_command(
                f"ls -la '{file_path}' 2>/dev/null | grep -v '^d'"
            )
            
            if returncode != 0:
                return analysis
            
            file_name = file_path.split('/')[-1]
            
            # Check file extension
            if any(file_path.endswith(ext) for ext in SUSPICIOUS_FILE_EXTENSIONS):
                analysis["reasons"].append(f"Suspicious file extension: {file_path.split('.')[-1]}")
                analysis["is_suspicious"] = True
            
            # Check for hidden files (starting with dot)
            if file_name.startswith('.'):
                analysis["reasons"].append("Hidden file detected")
                analysis["is_hidden_executable"] = True
            
            # Check for executable permissions in unusual locations
            if 'x' in output and not file_path.startswith("/system/bin/") and not file_path.startswith("/system/xbin/"):
                analysis["reasons"].append("Executable found in unusual location")
                analysis["is_hidden_executable"] = True
            
            # Check for shell scripts
            if file_path.endswith('.sh') or 'script' in file_name.lower():
                analysis["reasons"].append("Shell script detected")
                analysis["is_script"] = True
            
            # Check for modified system files
            if file_path.startswith("/system/") and not file_path.startswith("/system/app/"):
                returncode, _, _ = self.adb.execute_command(
                    f"stat '{file_path}' 2>/dev/null"
                )
                if returncode == 0:
                    analysis["reasons"].append("Modified system file")
                    analysis["is_modified_system"] = True
            
            # Determine risk level
            if analysis["is_hidden_executable"] or analysis["is_modified_system"]:
                analysis["risk_level"] = "HIGH"
            elif analysis["is_suspicious"] or analysis["is_script"]:
                analysis["risk_level"] = "MEDIUM"
            
            return analysis
            
        except Exception as e:
            log_error(f"Error analyzing file {file_path}: {str(e)}")
            return analysis
    
    def scan_for_injected_code(self) -> List[Dict]:
        """
        Scan for code injection in system libraries and binaries.
        
        Returns:
            List[Dict]: Detected injections
        """
        log_info("Scanning for injected code...")
        
        injected_code = []
        
        try:
            # Check system libraries
            returncode, stdout, _ = self.adb.execute_command(
                "find /system/lib* -name '*.so' 2>/dev/null | head -100"
            )
            
            if returncode == 0 and stdout:
                libraries = [lib.strip() for lib in stdout.split('\n') if lib.strip()]
                
                for lib_path in libraries:
                    # Check for suspicious patterns in library names
                    if any(pattern in lib_path for pattern in ["inject", "hook", "patch", "hack"]):
                        injected_code.append({
                            "type": "Suspicious Library",
                            "path": lib_path,
                            "severity": "HIGH",
                        })
                        log_warning(f"Suspicious library detected: {lib_path}")
            
            return injected_code
            
        except Exception as e:
            log_error(f"Code injection scan failed: {str(e)}")
            return []
    
    def scan_for_hidden_partitions(self) -> List[Dict]:
        """
        Scan for hidden or uncommon partitions.
        
        Returns:
            List[Dict]: Hidden partitions found
        """
        log_info("Scanning for hidden partitions...")
        
        hidden_partitions = []
        
        try:
            returncode, stdout, _ = self.adb.execute_command(
                "mount | grep -v '^tmpfs'"
            )
            
            if returncode == 0 and stdout:
                standard_mounts = {
                    "/system", "/vendor", "/data", "/cache", "/boot",
                    "/recovery", "/radio", "/sdcard", "/storage",
                }
                
                mounts = stdout.split('\n')
                for mount_line in mounts:
                    if mount_line.strip():
                        parts = mount_line.split()
                        if len(parts) >= 3:
                            mount_point = parts[2]
                            
                            # Check if mount point is unusual
                            if not any(mount_point.startswith(std) for std in standard_mounts):
                                hidden_partitions.append({
                                    "mount_point": mount_point,
                                    "mount_line": mount_line,
                                    "risk_level": "MEDIUM",
                                })
                                log_warning(f"Hidden partition detected: {mount_point}")
            
            return hidden_partitions
            
        except Exception as e:
            log_error(f"Hidden partition scan failed: {str(e)}")
            return []
