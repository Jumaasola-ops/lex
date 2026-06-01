"""
Process analyzer for detecting suspicious running processes.
"""

from typing import List, Dict
from adb_manager import ADBManager
from exceptions import ProcessAnalyzerException
from utils import log_info, log_error, log_warning
from config import SUSPICIOUS_PATTERNS


class ProcessAnalyzer:
    """Analyzes running processes for suspicious behavior."""
    
    def __init__(self, adb_manager: ADBManager) -> None:
        """
        Initialize Process Analyzer.
        
        Args:
            adb_manager: ADBManager instance
        """
        self.adb = adb_manager
        self.suspicious_processes: List[Dict] = []
    
    def scan_running_processes(self) -> Dict:
        """
        Scan running processes for suspicious activity.
        
        Returns:
            dict: Scan results
        """
        log_info("Scanning running processes...")
        
        results = {
            "total_processes": 0,
            "suspicious_processes": [],
            "high_cpu_usage": [],
            "high_memory_usage": [],
            "background_services": [],
        }
        
        try:
            # Get process list
            processes = self._get_process_list()
            results["total_processes"] = len(processes)
            
            # Analyze each process
            for process in processes:
                # Check for suspicious process names
                if self._is_suspicious_process(process):
                    results["suspicious_processes"].append(process)
                
                # Check for high resource usage
                if process.get("cpu_usage", 0) > 20:
                    results["high_cpu_usage"].append(process)
                
                if process.get("memory_mb", 0) > 100:
                    results["high_memory_usage"].append(process)
                
                # Check for suspicious background services
                if self._is_suspicious_background_service(process):
                    results["background_services"].append(process)
            
            log_info(f"Found {len(results['suspicious_processes'])} suspicious processes")
            return results
            
        except Exception as e:
            raise ProcessAnalyzerException(f"Process scan failed: {str(e)}")
    
    def _get_process_list(self) -> List[Dict]:
        """
        Get list of running processes.
        
        Returns:
            List[Dict]: Process information
        """
        processes = []
        
        try:
            # Get process information using ps command
            returncode, stdout, _ = self.adb.execute_command(
                "ps -A -o pid,ppid,%cpu,%mem,comm 2>/dev/null"
            )
            
            if returncode == 0 and stdout:
                lines = stdout.strip().split('\n')[1:]  # Skip header
                
                for line in lines:
                    if not line.strip():
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 5:
                        try:
                            process = {
                                "pid": parts[0],
                                "ppid": parts[1],
                                "cpu_usage": float(parts[2].rstrip('%')),
                                "memory_usage": parts[3],
                                "name": ' '.join(parts[4:]),
                            }
                            
                            # Calculate memory in MB
                            try:
                                mem_val = float(parts[3].rstrip('%'))
                                # Rough estimate: assume 2GB device
                                process["memory_mb"] = (mem_val / 100) * 2048
                            except:
                                process["memory_mb"] = 0
                            
                            processes.append(process)
                        except:
                            continue
            
            return processes
            
        except Exception as e:
            log_error(f"Failed to get process list: {str(e)}")
            return []
    
    def _is_suspicious_process(self, process: Dict) -> bool:
        """
        Check if process is suspicious.
        
        Args:
            process: Process information
            
        Returns:
            bool: True if suspicious
        """
        process_name = process.get("name", "").lower()
        
        # Check against suspicious patterns
        for pattern in SUSPICIOUS_PATTERNS:
            if pattern in process_name:
                return True
        
        # Check for processes from suspicious packages
        if any(marker in process_name for marker in [
            "trojan", "malware", "virus", "ransomware", "spyware",
            "botnet", "worm", "keylog", "rootkit", "backdoor",
            "exploit", "injection", "hook", "patch",
        ]):
            return True
        
        return False
    
    def _is_suspicious_background_service(self, process: Dict) -> bool:
        """
        Check if background service is suspicious.
        
        Args:
            process: Process information
            
        Returns:
            bool: True if suspicious background service
        """
        process_name = process.get("name", "").lower()
        
        # Services that shouldn't be running in background
        suspicious_services = [
            "root", "daemon", "system", "shell",  # Root-level services
            ".so", "libinjection", "hooker",  # Native injection
        ]
        
        for service in suspicious_services:
            if service in process_name:
                # Check if it's actually suspicious by looking for parent process
                if process.get("ppid", "1") == "1":  # Kernel/init is parent
                    return True
        
        return False
    
    def get_service_dependencies(self, process_name: str) -> Dict:
        """
        Get dependencies and connections for a process.
        
        Args:
            process_name: Name of process
            
        Returns:
            dict: Process dependencies and information
        """
        log_info(f"Analyzing dependencies for: {process_name}")
        
        info = {
            "process_name": process_name,
            "connections": [],
            "open_files": [],
            "memory_map": [],
        }
        
        try:
            # Get process PID
            returncode, stdout, _ = self.adb.execute_command(
                f"pidof {process_name}"
            )
            
            if returncode != 0:
                return info
            
            pid = stdout.strip().split()[0]
            
            # Get open connections
            returncode, stdout, _ = self.adb.execute_command(
                f"netstat 2>/dev/null | grep {pid}"
            )
            
            if returncode == 0 and stdout:
                info["connections"] = stdout.strip().split('\n')
            
            # Get open files
            returncode, stdout, _ = self.adb.execute_command(
                f"lsof -p {pid} 2>/dev/null"
            )
            
            if returncode == 0 and stdout:
                info["open_files"] = [f.strip() for f in stdout.split('\n')[:10]]
            
            return info
            
        except Exception as e:
            log_error(f"Failed to analyze process dependencies: {str(e)}")
            return info


class ProcessAnalyzerException(Exception):
    """Exception raised during process analysis."""
    pass
