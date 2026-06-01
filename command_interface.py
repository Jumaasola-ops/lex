"""
Command interface for custom command handling.
"""

import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional, List
from adb_manager import ADBManager
from malware_scanner import MalwareScanner
from app_analyzer import AppAnalyzer
from metadata_handler import MetadataHandler
from malware_remover import MalwareRemover
from exceptions import (
    AndroidSecurityException,
    InvalidCommandException,
    ADBDeviceNotFound,
)
from utils import (
    log_info,
    log_error,
    print_section_header,
    print_success,
    print_error,
    print_info,
    print_warning,
)


class CommandInterface:
    """Handles custom command interface for Android Security Scanner."""
    
    def __init__(self) -> None:
        """Initialize Command Interface."""
        self.commands: Dict[str, Callable] = {
            "scan-malware": self.cmd_scan_malware,
            "aggressive-scan": self.cmd_aggressive_scan,
            "remove-lockware": self.cmd_remove_lockware,
            "remove-lock-screen": self.cmd_remove_lock_screen,
            "cripple-ransomware": self.cmd_cripple_ransomware,
            "cleanup-threats": self.cmd_cleanup_threats,
            "quarantine-app": self.cmd_quarantine_app,
            "crawl-files": self.cmd_crawl_files,
            "analyze-processes": self.cmd_analyze_processes,
            "check-system": self.cmd_check_system,
            "analyze-apps": self.cmd_analyze_apps,
            "extract-metadata": self.cmd_extract_metadata,
            "remove-metadata": self.cmd_remove_metadata,
            "batch-clean": self.cmd_batch_clean,
            "device-info": self.cmd_device_info,
            "list-packages": self.cmd_list_packages,
            "app-info": self.cmd_app_info,
            "full-scan": self.cmd_full_scan,
            "create-profile": self.cmd_create_profile,
            "help": self.cmd_help,
        }
        
        self.adb: Optional[ADBManager] = None
        self.malware_scanner: Optional[MalwareScanner] = None
        self.malware_remover: Optional[MalwareRemover] = None
        self.app_analyzer: Optional[AppAnalyzer] = None
        self.metadata_handler = MetadataHandler()
    
    def initialize(self, device_id: Optional[str] = None) -> bool:
        """
        Initialize connection with Android device.
        
        Args:
            device_id: Optional device ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print_section_header("Initializing Connection")
            self.adb = ADBManager(device_id)
            self.malware_scanner = MalwareScanner(self.adb)
            self.malware_remover = MalwareRemover(self.adb)
            self.app_analyzer = AppAnalyzer(self.adb)
            
            device_info = self.adb.get_device_info()
            print_success(f"Connected to device: {device_info['device_id']}")
            print_info(f"Android Version: {device_info.get('android_version', 'Unknown')}")
            print_info(f"Manufacturer: {device_info.get('manufacturer', 'Unknown')}")
            print_info(f"Model: {device_info.get('model', 'Unknown')}\n")
            
            return True
            
        except ADBDeviceNotFound as e:
            print_error(str(e))
            return False
        except Exception as e:
            print_error(f"Initialization failed: {str(e)}")
            log_error(f"Initialization error: {str(e)}")
            return False
    
    def execute(self, command: str, args: List[str]) -> bool:
        """
        Execute a command.
        
        Args:
            command: Command name
            args: Command arguments
            
        Returns:
            bool: True if successful, False otherwise
        """
        if command not in self.commands:
            print_error(f"Unknown command: {command}")
            print_info("Use 'help' command to see available commands")
            return False
        
        try:
            if command not in ["help", "create-profile"] and not self.adb:
                if not self.initialize():
                    return False
            
            return self.commands[command](args)
            
        except InvalidCommandException as e:
            print_error(str(e))
            return False
        except AndroidSecurityException as e:
            print_error(f"Error: {str(e)}")
            log_error(f"Command error: {str(e)}")
            return False
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")
            log_error(f"Unexpected error: {str(e)}")
            return False
    
    def cmd_scan_malware(self, args: List[str]) -> bool:
        """
        Scan device for malware.
        
        Command: scan-malware
        """
        print_section_header("Malware Scan")
        
        try:
            results = self.malware_scanner.scan_for_malware()
            self.malware_scanner.display_scan_results(results)
            
            # Summary
            threat_count = (
                len(results["malware_threats"]) +
                len(results["suspicious_packages"]) +
                len(results["hidden_apps"])
            )
            
            if threat_count == 0:
                print_success(f"\nDevice is clean! No threats detected.\n")
            else:
                print_error(f"\n{threat_count} potential threats found.\n")
            
            return True
            
        except Exception as e:
            print_error(f"Malware scan failed: {str(e)}")
            return False
    
    def cmd_aggressive_scan(self, args: List[str]) -> bool:
        """
        Perform aggressive comprehensive scan with file crawling.
        
        Command: aggressive-scan
        """
        print_section_header("AGGRESSIVE COMPREHENSIVE SECURITY SCAN")
        print_info("This scan will perform deep device inspection including:")
        print_info("  1. Malware database checks")
        print_info("  2. File system crawling")
        print_info("  3. Process analysis")
        print_info("  4. System integrity verification\n")
        
        try:
            results = self.malware_scanner.aggressive_scan()
            
            # Display malware results
            self.malware_scanner.display_scan_results(results)
            
            # Display file scan results
            if results.get("file_scan"):
                print_section_header("File System Scan Results")
                file_results = results["file_scan"]
                print(f"Total files scanned: {file_results.get('total_files_scanned', 0)}")
                print(f"Suspicious files found: {len(file_results.get('suspicious_files', []))}")
                print(f"Hidden executables: {len(file_results.get('hidden_executables', []))}")
                print(f"Suspicious scripts: {len(file_results.get('suspicious_scripts', []))}\n")
                
                if file_results.get('suspicious_files'):
                    print("Suspicious Files:")
                    for file_info in file_results['suspicious_files'][:10]:
                        print(f"  • {file_info['file_path']} ({file_info['risk_level']})")
            
            # Display process scan results
            if results.get("process_scan"):
                print_section_header("Process Analysis Results")
                proc_results = results["process_scan"]
                print(f"Total processes scanned: {proc_results.get('total_processes', 0)}")
                print(f"Suspicious processes: {len(proc_results.get('suspicious_processes', []))}")
                print(f"High CPU usage: {len(proc_results.get('high_cpu_usage', []))}")
                print(f"High memory usage: {len(proc_results.get('high_memory_usage', []))}\n")
                
                if proc_results.get('suspicious_processes'):
                    print("Suspicious Processes:")
                    for proc in proc_results['suspicious_processes'][:5]:
                        print(f"  • PID {proc.get('pid')}: {proc.get('name')}")
            
            # Display system integrity results
            if results.get("system_integrity"):
                print_section_header("System Integrity Check")
                sys_results = results["system_integrity"]
                print(f"Device Rooted: {sys_results.get('is_rooted', False)}")
                print(f"SELinux Status: {sys_results.get('selinux_status', 'unknown')}")
                print(f"System Modifications: {len(sys_results.get('system_modifications', []))}\n")
            
            # Summary
            print_section_header("Aggressive Scan Summary")
            malware_threats = len(results.get("malware_threats", []))
            suspicious_pkgs = len(results.get("suspicious_packages", []))
            hidden_apps = len(results.get("hidden_apps", []))
            suspicious_files = len(results.get("file_scan", {}).get('suspicious_files', []))
            suspicious_procs = len(results.get("process_scan", {}).get('suspicious_processes', []))
            
            total_threats = malware_threats + suspicious_pkgs + hidden_apps + suspicious_files + suspicious_procs
            
            if total_threats == 0:
                print_success("✓ DEVICE IS SECURE! No threats detected.\n")
            else:
                print_error(f"✗ FOUND {total_threats} POTENTIAL THREATS:\n")
                print(f"  • Malware threats: {malware_threats}")
                print(f"  • Suspicious packages: {suspicious_pkgs}")
                print(f"  • Hidden apps: {hidden_apps}")
                print(f"  • Suspicious files: {suspicious_files}")
                print(f"  • Suspicious processes: {suspicious_procs}\n")
            
            return total_threats == 0
            
        except Exception as e:
            print_error(f"Aggressive scan failed: {str(e)}")
            return False
    
    def cmd_crawl_files(self, args: List[str]) -> bool:
        """
        Crawl file system for suspicious files.
        
        Command: crawl-files
        """
        print_section_header("File System Crawl")
        
        try:
            from file_crawler import FileCrawler
            crawler = FileCrawler(self.adb)
            results = crawler.crawl_system()
            
            print(f"Total files scanned: {results['total_files_scanned']}")
            print(f"Suspicious files: {len(results['suspicious_files'])}")
            print(f"Hidden executables: {len(results['hidden_executables'])}")
            print(f"Suspicious scripts: {len(results['suspicious_scripts'])}")
            print(f"Modified system files: {len(results['modified_system_files'])}\n")
            
            if results['suspicious_files']:
                print("Suspicious Files Found:")
                for file_info in results['suspicious_files'][:20]:
                    print(f"  • {file_info['file_path']}")
                    print(f"    Risk: {file_info['risk_level']}")
                    for reason in file_info['reasons']:
                        print(f"    - {reason}")
            
            print()
            return True
            
        except Exception as e:
            print_error(f"File crawl failed: {str(e)}")
            return False
    
    def cmd_analyze_processes(self, args: List[str]) -> bool:
        """
        Analyze running processes for suspicious activity.
        
        Command: analyze-processes
        """
        print_section_header("Process Analysis")
        
        try:
            from process_analyzer import ProcessAnalyzer
            analyzer = ProcessAnalyzer(self.adb)
            results = analyzer.scan_running_processes()
            
            print(f"Total processes: {results['total_processes']}")
            print(f"Suspicious processes: {len(results['suspicious_processes'])}")
            print(f"High CPU usage: {len(results['high_cpu_usage'])}")
            print(f"High memory usage: {len(results['high_memory_usage'])}\n")
            
            if results['suspicious_processes']:
                print("Suspicious Processes:")
                for proc in results['suspicious_processes'][:15]:
                    print(f"  • PID {proc['pid']}: {proc['name']}")
                    print(f"    CPU: {proc['cpu_usage']}%")
                    print(f"    Memory: {proc['memory_mb']:.1f}MB")
            
            if results['high_cpu_usage']:
                print(f"\nHigh CPU Usage (>{20}%):")
                for proc in results['high_cpu_usage'][:10]:
                    print(f"  • {proc['name']}: {proc['cpu_usage']}%")
            
            if results['high_memory_usage']:
                print(f"\nHigh Memory Usage (>100MB):")
                for proc in results['high_memory_usage'][:10]:
                    print(f"  • {proc['name']}: {proc['memory_mb']:.1f}MB")
            
            print()
            return True
            
        except Exception as e:
            print_error(f"Process analysis failed: {str(e)}")
            return False
    
    def cmd_check_system(self, args: List[str]) -> bool:
        """
        Check system integrity and security status.
        
        Command: check-system
        """
        print_section_header("System Integrity Check")
        
        try:
            from system_analyzer import SystemAnalyzer
            analyzer = SystemAnalyzer(self.adb)
            
            # System integrity
            integrity = analyzer.analyze_system_integrity()
            print("\nSystem Status:")
            print(f"  • Rooted: {'YES - HIGH RISK' if integrity['is_rooted'] else 'NO - OK'}")
            print(f"  • Su binary found: {integrity['has_su_binary']}")
            print(f"  • Xposed framework: {integrity['has_xposed_framework']}")
            print(f"  • SELinux status: {integrity['selinux_status']}")
            
            if integrity['system_modifications']:
                print(f"\n  ⚠ System Modifications ({len(integrity['system_modifications'])}):")
                for mod in integrity['system_modifications'][:10]:
                    print(f"    • {mod['type']}: {mod['path']}")
            
            if integrity['suspicious_settings']:
                print(f"\n  ⚠ Suspicious Settings ({len(integrity['suspicious_settings'])}):")
                for setting in integrity['suspicious_settings']:
                    print(f"    • {setting['setting']}: {setting['value']}")
            
            # Security patches
            patches = analyzer.check_security_patches()
            print(f"\nSecurity Patches:")
            print(f"  • Patch level: {patches['patch_level']}")
            print(f"  • Days since patch: {patches['days_since_patch']}")
            if patches['is_vulnerable']:
                print(f"  • Status: OUTDATED - Device may be vulnerable!")
            
            print()
            return True
            
        except Exception as e:
            print_error(f"System check failed: {str(e)}")
            return False
    
    def cmd_remove_lockware(self, args: List[str]) -> bool:
        """
        Detect and remove unauthorized lockware apps.
        
        Command: remove-lockware [--auto]
        """
        print_section_header("UNAUTHORIZED LOCKWARE REMOVAL")
        
        try:
            auto_remove = "--auto" in args
            
            if not auto_remove:
                print_warning("⚠ This will detect and remove apps that lock your device")
                print_info("Without --auto flag, suspicious apps will be quarantined instead\n")
            
            # Detect lockware
            lockware = self.malware_remover.detect_unauthorized_lockware()
            
            # Collect all threats
            all_threats = []
            
            print("Scanning for unauthorized lockware...\n")
            
            if lockware.get("device_admin"):
                print(f"⚠ Suspicious Device Admins ({len(lockware['device_admin'])}):")
                for admin in lockware["device_admin"]:
                    print(f"  • {admin['package']}")
                    all_threats.append(admin)
            
            if lockware.get("mdm_tools"):
                print(f"\n⚠ Unauthorized MDM Tools ({len(lockware['mdm_tools'])}):")
                for mdm in lockware["mdm_tools"]:
                    print(f"  • {mdm['package']} - {mdm['reason']}")
                    all_threats.append(mdm)
            
            if lockware.get("ransomware"):
                print(f"\n🚨 RANSOMWARE DETECTED ({len(lockware['ransomware'])}):")
                for ransomware in lockware["ransomware"]:
                    print(f"  • {ransomware['package']} - {ransomware['reason']}")
                    all_threats.append(ransomware)
            
            if lockware.get("hidden_locker"):
                print(f"\n⚠ Hidden Locker Apps ({len(lockware['hidden_locker'])}):")
                for locker in lockware["hidden_locker"]:
                    print(f"  • {locker['package']}")
                    all_threats.append(locker)
            
            if not all_threats:
                print_success("\n✓ No unauthorized lockware detected!\n")
                return True
            
            # Removal confirmation
            print(f"\nTotal threats found: {len(all_threats)}")
            
            if not auto_remove:
                response = input("\nProceed with quarantine/removal? (yes/no): ").strip().lower()
                if response != "yes":
                    print_info("Operation cancelled.\n")
                    return False
            
            # Remove threats
            results = self.malware_remover.batch_remove_threats(all_threats, auto_confirm=auto_remove)
            
            print_section_header("Removal Results")
            self.malware_remover.display_removal_summary(results)
            
            return results["failed"] == 0
            
        except Exception as e:
            print_error(f"Lockware removal failed: {str(e)}")
            return False
    
    def cmd_remove_lock_screen(self, args: List[str]) -> bool:
        """
        Attempt to remove malicious lock screen and unlock device.
        Works against ransomware lock screens, device admin locks, and scareware.
        
        Command: remove-lock-screen
        """
        print_section_header("🔓 LOCK SCREEN REMOVAL - EMERGENCY UNLOCK")
        
        try:
            print_warning("This will attempt to:")
            print_info("  1. Clear malicious launcher")
            print_info("  2. Remove lock screen admin privileges")
            print_info("  3. Disable lock screen apps")
            print_info("  4. Reset security settings")
            print_info("  5. Reset display settings")
            print_info("  6. Remove device owner restrictions")
            print_info("  7. Force navigation to home")
            print_info("  8. Check SIM lock status\n")
            
            # Confirm action
            response = input("Proceed with lock screen removal? (type 'yes' to confirm): ").strip().lower()
            if response != "yes":
                print_info("\nOperation cancelled.\n")
                return False
            
            # Execute lock screen removal
            success, message = self.malware_remover.remove_lock_screen()
            
            if success:
                print_section_header("✓ UNLOCK ATTEMPT COMPLETED")
                print_success("\nNext steps:")
                print_success("  1. Try pressing the Home button")
                print_success("  2. Try touching the screen")
                print_success("  3. Try swiping to unlock")
                print_success("  4. If still locked, try:")
                print_success("     - Recovery Mode: Hold Volume Down + Power")
                print_success("     - Safe Mode: Power + Volume Down at startup\n")
                return True
            else:
                print_error(f"\nUnlock attempt had issues: {message}")
                print_warning("\nIf device is still locked, try:")
                print_info("  • Recovery Mode: Hold Volume Down + Power (10 sec)")
                print_info("  • Safe Mode: Restart and hold Volume Down + Power")
                print_info("  • Factory Reset: Via recovery menu\n")
                return False
            
        except Exception as e:
            print_error(f"Lock screen removal error: {str(e)}")
            return False
    
    def cmd_cripple_ransomware(self, args: List[str]) -> bool:
        """
        Permanently disable ransomware to ensure it cannot lock device again.
        Uses multi-layered permanent disabling approach.
        
        Command: cripple-ransomware <package_name>
        """
        if not args:
            raise InvalidCommandException(
                "Usage: cripple-ransomware <package_name>\n"
                "This will PERMANENTLY DISABLE the ransomware so it CANNOT lock your device again."
            )
        
        package_name = args[0]
        print_section_header("🔒 PERMANENT RANSOMWARE DISABLING")
        
        try:
            print_warning(f"\nTarget: {package_name}")
            print_warning("This will permanently cripple the ransomware using 9-step hardening:\n")
            
            print_info("  1. Force stop the malicious app")
            print_info("  2. Remove device admin privileges")
            print_info("  3. Disable app at system level")
            print_info("  4. Clear app cache and data")
            print_info("  5. Revoke all permissions")
            print_info("  6. Disable auto-start components")
            print_info("  7. Remove from default app settings")
            print_info("  8. Block package reinstallation")
            print_info("  9. Verify permanent disable status\n")
            
            # Confirm action
            response = input("Proceed with PERMANENT DISABLE? (type 'yes' to confirm): ").strip().lower()
            if response != "yes":
                print_info("\nOperation cancelled.\n")
                return False
            
            # Execute permanent crippling
            success, message = self.malware_remover.cripple_permanently(package_name)
            
            if success:
                print_section_header("✓ RANSOMWARE PERMANENTLY CRIPPLED")
                print_success("\nYour device is now protected:")
                print_success(f"  • {package_name} is permanently disabled")
                print_success("  • Cannot lock your screen")
                print_success("  • Cannot run in background")
                print_success("  • Cannot access device permissions")
                print_success("  • Cannot auto-start on reboot\n")
                return True
            else:
                print_error(f"\nCrippling encountered errors: {message}\n")
                return False
            
        except Exception as e:
            print_error(f"Error during permanent disable: {str(e)}")
            return False
    
    def cmd_cleanup_threats(self, args: List[str]) -> bool:
        """
        Detect threats from aggressive scan and remove them.
        
        Command: cleanup-threats [--auto]
        """
        print_section_header("THREAT CLEANUP")
        
        try:
            auto_cleanup = "--auto" in args
            
            # Run aggressive scan to find all threats
            print_info("Running aggressive scan to detect threats...\n")
            scan_results = self.malware_scanner.aggressive_scan()
            
            # Collect removable threats (not just detection)
            threats_to_remove = []
            
            # Malware threats
            threats_to_remove.extend(scan_results.get("malware_threats", []))
            
            # Ransomware from file scan
            if scan_results.get("file_scan"):
                # Add files detected as threats
                pass
            
            if not threats_to_remove:
                print_success("✓ No threats requiring cleanup detected!\n")
                return True
            
            print(f"Found {len(threats_to_remove)} threats\n")
            
            # Confirm removal
            if not auto_cleanup:
                response = input("Proceed with threat removal? (yes/no): ").strip().lower()
                if response != "yes":
                    print_info("Cleanup cancelled.\n")
                    return False
            
            # Remove threats
            results = self.malware_remover.batch_remove_threats(threats_to_remove, auto_confirm=True)
            
            print_section_header("Cleanup Results")
            self.malware_remover.display_removal_summary(results)
            
            return results["failed"] == 0
            
        except Exception as e:
            print_error(f"Threat cleanup failed: {str(e)}")
            return False
    
    def cmd_quarantine_app(self, args: List[str]) -> bool:
        """
        Quarantine a suspicious app without removing it.
        
        Command: quarantine-app <package_name>
        """
        if not args:
            raise InvalidCommandException("Usage: quarantine-app <package_name>")
        
        package_name = args[0]
        print_section_header("Quarantine Application")
        
        try:
            print_info(f"Quarantining: {package_name}\n")
            success, msg = self.malware_remover.quarantine_package(package_name)
            
            if success:
                print_success(msg)
            else:
                print_error(msg)
            
            print()
            return success
            
        except Exception as e:
            print_error(f"Quarantine failed: {str(e)}")
            return False
    
    def cmd_analyze_apps(self, args: List[str]) -> bool:
        """
        Analyze installed apps.
        
        Command: analyze-apps
        """
        print_section_header("App Analysis")
        
        try:
            results = self.app_analyzer.analyze_apps()
            self.app_analyzer.display_analysis_results(results)
            return True
            
        except Exception as e:
            print_error(f"App analysis failed: {str(e)}")
            return False
    
    def cmd_extract_metadata(self, args: List[str]) -> bool:
        """
        Extract metadata from a photo.
        
        Command: extract-metadata <photo_path>
        """
        if not args:
            raise InvalidCommandException(
                "Usage: extract-metadata <photo_path>"
            )
        
        photo_path = args[0]
        print_section_header("Extract Metadata")
        
        try:
            metadata = self.metadata_handler.extract_metadata(photo_path)
            self.metadata_handler.display_metadata(metadata)
            
            print_success(f"\nMetadata extracted successfully.\n")
            return True
            
        except Exception as e:
            print_error(f"Metadata extraction failed: {str(e)}")
            return False
    
    def cmd_remove_metadata(self, args: List[str]) -> bool:
        """
        Remove metadata from a photo.
        
        Command: remove-metadata <photo_path> [output_path]
        """
        if not args:
            raise InvalidCommandException(
                "Usage: remove-metadata <photo_path> [output_path]"
            )
        
        photo_path = args[0]
        output_path = args[1] if len(args) > 1 else None
        
        print_section_header("Remove Metadata")
        
        try:
            success, result = self.metadata_handler.remove_metadata(
                photo_path,
                output_path,
            )
            
            if success:
                print_success(f"Metadata removed successfully!")
                print_info(f"Cleaned photo saved to: {result}\n")
            else:
                print_error(f"Failed to remove metadata: {result}")
            
            return success
            
        except Exception as e:
            print_error(f"Metadata removal failed: {str(e)}")
            return False
    
    def cmd_batch_clean(self, args: List[str]) -> bool:
        """
        Batch remove metadata from multiple photos.
        
        Command: batch-clean <input_dir> <output_dir> [extensions]
        """
        if len(args) < 2:
            raise InvalidCommandException(
                "Usage: batch-clean <input_dir> <output_dir> [extensions]"
            )
        
        input_dir = args[0]
        output_dir = args[1]
        extensions = args[2].split(',') if len(args) > 2 else None
        
        print_section_header("Batch Clean Metadata")
        
        try:
            results = self.metadata_handler.batch_remove_metadata(
                input_dir,
                output_dir,
                extensions,
            )
            
            print(f"\nProcessing Results:")
            print(f"  Total files: {results['total_files']}")
            print(f"  Processed: {results['processed']}")
            print(f"  Failed: {results['failed']}")
            print(f"  Output directory: {results['output_directory']}")
            
            if results["errors"]:
                print(f"\nErrors:")
                for error in results["errors"]:
                    print(f"  • {error}")
            
            print()
            return results["failed"] == 0
            
        except Exception as e:
            print_error(f"Batch cleaning failed: {str(e)}")
            return False
    
    def cmd_device_info(self, args: List[str]) -> bool:
        """
        Display comprehensive device information including IMEI, storage, hardware specs.
        
        Command: device-info
        """
        print_section_header("📱 COMPREHENSIVE DEVICE INFORMATION")
        
        try:
            info = self.adb.get_comprehensive_device_info()
            
            # Device Identification
            if "device_identification" in info:
                print("\n🏷️  DEVICE IDENTIFICATION:")
                for key, value in info["device_identification"].items():
                    print(f"  • {key.replace('_', ' ').title()}: {value}")
            
            # Operating System
            if "operating_system" in info:
                print("\n🔧 OPERATING SYSTEM:")
                for key, value in info["operating_system"].items():
                    print(f"  • {key.replace('_', ' ').title()}: {value}")
            
            # Hardware
            if "hardware" in info:
                print("\n⚙️  HARDWARE SPECS:")
                for key, value in info["hardware"].items():
                    if isinstance(value, dict):
                        print(f"  • {key.replace('_', ' ').title()}:")
                        for subkey, subvalue in value.items():
                            print(f"    - {subkey.replace('_', ' ').title()}: {subvalue}")
                    else:
                        print(f"  • {key.replace('_', ' ').title()}: {value}")
            
            # Storage
            if "storage" in info:
                print("\n💾 STORAGE:")
                for partition, details in info["storage"].items():
                    print(f"  • {partition.replace('_', ' ').title()}:")
                    if isinstance(details, dict):
                        for key, value in details.items():
                            print(f"    - {key.replace('_', ' ').title()}: {value}")
                    else:
                        print(f"    {details}")
            
            # Connectivity
            if "connectivity" in info:
                print("\n📡 CONNECTIVITY:")
                for key, value in info["connectivity"].items():
                    if value:
                        print(f"  • {key.replace('_', ' ').title()}: {value}")
            
            # Security
            if "security" in info:
                print("\n🔒 SECURITY:")
                for key, value in info["security"].items():
                    print(f"  • {key.replace('_', ' ').title()}: {value}")
            
            # Display
            if "display" in info:
                print("\n📺 DISPLAY:")
                for key, value in info["display"].items():
                    print(f"  • {key.replace('_', ' ').title()}: {value}")
            
            # Sensors
            if "sensors" in info and info["sensors"].get("list"):
                print("\n📡 SENSORS:")
                for sensor in info["sensors"]["list"][:10]:
                    print(f"  • {sensor}")
            
            # System Properties
            if "system_properties" in info:
                print("\n⚙️  SYSTEM PROPERTIES:")
                for key, value in info["system_properties"].items():
                    print(f"  • {key.replace('_', ' ').title()}: {value}")
            
            print()
            return True
            
        except Exception as e:
            print_error(f"Failed to get device info: {str(e)}")
            return False
    
    def cmd_list_packages(self, args: List[str]) -> bool:
        """
        List installed packages.
        
        Command: list-packages [--system] [--user]
        """
        print_section_header("Installed Packages")
        
        try:
            parser = argparse.ArgumentParser(add_help=False)
            parser.add_argument('--system', action='store_true')
            parser.add_argument('--user', action='store_true')
            
            parsed_args = parser.parse_args(args) if args else argparse.Namespace()
            
            packages = self.adb.get_installed_packages()
            
            if parsed_args.system:
                packages = [p for p in packages if self._is_system_package(p)]
            elif parsed_args.user:
                packages = [p for p in packages if not self._is_system_package(p)]
            
            print(f"Total packages: {len(packages)}\n")
            for pkg in sorted(packages):
                print(f"  • {pkg}")
            
            print()
            return True
            
        except Exception as e:
            print_error(f"Failed to list packages: {str(e)}")
            return False
    
    def cmd_app_info(self, args: List[str]) -> bool:
        """
        Get information about specific app.
        
        Command: app-info <package_name>
        """
        if not args:
            raise InvalidCommandException(
                "Usage: app-info <package_name>"
            )
        
        package_name = args[0]
        print_section_header(f"App Information: {package_name}")
        
        try:
            info = self.app_analyzer.get_app_info(package_name)
            
            print(f"Package Name: {info['package_name']}")
            print(f"Is System App: {info['is_system']}")
            print(f"Is Suspicious: {info['is_suspicious']}")
            print(f"Is Hidden: {info['is_hidden']}")
            
            if "details" in info:
                print(f"\nPackage Details:")
                for key, value in info["details"].items():
                    print(f"  • {key}: {value}")
            
            print()
            return True
            
        except Exception as e:
            print_error(f"Failed to get app info: {str(e)}")
            return False
    
    def cmd_full_scan(self, args: List[str]) -> bool:
        """
        Perform comprehensive security scan.
        
        Command: full-scan
        """
        print_section_header("Comprehensive Security Scan")
        
        print_info("This scan will:")
        print_info("  1. Scan for malware")
        print_info("  2. Analyze apps for suspicious behavior")
        print_info("  3. Check for hidden apps\n")
        
        all_passed = True
        
        # Malware scan
        print_section_header("Step 1: Malware Scan")
        malware_results = self.malware_scanner.scan_for_malware()
        self.malware_scanner.display_scan_results(malware_results)
        
        # App analysis
        print_section_header("Step 2: App Analysis")
        app_results = self.app_analyzer.analyze_apps()
        self.app_analyzer.display_analysis_results(app_results)
        
        # Summary
        print_section_header("Scan Summary")
        
        malware_threats = len(malware_results["malware_threats"])
        suspicious_apps = len(app_results["suspicious_apps"])
        hidden_apps = len(app_results["hidden_apps"])
        
        total_issues = malware_threats + suspicious_apps + hidden_apps
        
        if total_issues == 0:
            print_success("✓ Device is secure! No threats detected.\n")
        else:
            print_error(f"✗ Found {total_issues} potential issues:\n")
            print(f"  • Malware threats: {malware_threats}")
            print(f"  • Suspicious apps: {suspicious_apps}")
            print(f"  • Hidden apps: {hidden_apps}\n")
            all_passed = False
        
        return all_passed
    
    def cmd_create_profile(self, args: List[str]) -> bool:
        """
        Create comprehensive device profile with unique URL and QR code.
        
        Command: create-profile
        Generates device profile with all specs, location, network info, and creates a shareable link with QR code.
        """
        print_section_header("WIRELESS DEVICE PROFILE COLLECTOR")
        print_info("Starting wireless profile collection server...\n")
        
        try:
            from device_profile_server import DeviceProfileServer
            from qr_generator import QRCodeGenerator
            import time
            
            # Initialize server
            server = DeviceProfileServer(port=5000)
            
            # Get local IP
            local_ip = server.get_local_ip()
            server_url = server.get_server_url(local_ip)
            
            print_success(f"✓ Server started on {local_ip}:5000\n")
            
            # Start server in background thread
            server_thread = server.start_server_thread()
            time.sleep(2)  # Give server time to start
            
            # Generate QR code
            qr_generator = QRCodeGenerator()
            qr_path = qr_generator.generate_qr_code(server_url, f"wireless_profile_qr.png")
            
            # Display sharing information
            print_section_header("SHARE THIS LINK WITH OTHER DEVICES")
            print(f"\n📱 Share this URL with any device:\n")
            print(f"   {server_url}\n")
            
            if qr_path:
                print(f"📲 Or scan this QR code: {qr_path}\n")
            
            print_section_header("IMPORTANT INSTRUCTIONS")
            print_info("\n1. Open the link on ANY device (phone, tablet, etc.)")
            print_info("2. Allow location/geolocation when prompted")
            print_info("3. The device will automatically:")
            print_info("   ✓ Collect GPS coordinates")
            print_info("   ✓ Gather device specifications")
            print_info("   ✓ Capture network information")
            print_info("   ✓ Detect hardware capabilities")
            print_info("   ✓ Determine screen resolution")
            print_info("   ✓ Record connection type (4G/5G/WiFi)")
            print_info("4. Profile will be submitted automatically\n")
            
            print_section_header("DEVICE PROFILES RECEIVED")
            print_info("Listening for incoming device profiles...")
            print_info("Press Ctrl+C to stop and view results\n")
            
            # Keep server running and display received profiles
            try:
                while True:
                    time.sleep(1)
                    if server.received_profiles:
                        print("\n" + "="*60)
                        print(f"✓ PROFILES RECEIVED: {len(server.received_profiles)}")
                        print("="*60 + "\n")
                        server.display_profiles()
                        print()
            except KeyboardInterrupt:
                print("\n\n" + "="*60)
                print("STOPPING SERVER")
                print("="*60 + "\n")
                
                # Display final summary
                if server.received_profiles:
                    print_section_header("FINAL PROFILE SUMMARY")
                    server.display_profiles()
                    
                    # Save summary
                    summary_path = Path("reports/profiles/wireless_summary.json")
                    summary_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(summary_path, 'w') as f:
                        json.dump({
                            'server_url': server_url,
                            'profiles_count': len(server.received_profiles),
                            'profiles': server.received_profiles,
                            'timestamp': datetime.now().isoformat()
                        }, f, indent=2)
                    
                    print_success(f"\n✓ Summary saved to: {summary_path}\n")
                else:
                    print_warning("⚠ No device profiles received\n")
                
                return True
            
        except Exception as e:
            print_error(f"Profile server error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def cmd_help(self, args: List[str]) -> bool:
        """
        Display help information.
        
        Command: help [command]
        """
        print_section_header("Android Security Scanner - Help")
        
        if args:
            command = args[0]
            if command in self.commands:
                print(f"Command: {command}")
                print(f"Help: {self.commands[command].__doc__}\n")
            else:
                print_error(f"Unknown command: {command}\n")
        else:
            print("Available Commands:\n")
            for cmd_name, cmd_func in sorted(self.commands.items()):
                doc = cmd_func.__doc__ or "No description"
                doc = doc.strip().split('\n')[0]
                print(f"  • {cmd_name:<20} - {doc}")
            
            print("\nUsage: android-security <command> [arguments]")
            print("Use 'help <command>' for more details about a command\n")
        
        return True
    
    def _is_system_package(self, package_name: str) -> bool:
        """Helper to check if package is system package."""
        from config import SYSTEM_PACKAGES
        for system_pkg in SYSTEM_PACKAGES:
            if package_name.startswith(system_pkg):
                return True
        return False
