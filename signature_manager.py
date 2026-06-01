"""
Automated Malware Signature Database Management.
Author: Asola Junior
Manages updates, versioning, and validation of malware signatures.
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import urllib.request
import urllib.error

from utils import log_info, log_error, log_warning
from config import MALWARE_DB_DIR


class SignatureManager:
    """Manages malware signature database updates and validation."""
    
    def __init__(self):
        """Initialize signature manager."""
        self.db_dir = MALWARE_DB_DIR
        self.sig_file = self.db_dir / "signatures.json"
        self.version_file = self.db_dir / "version.json"
        self.signatures = {}
        self.version_info = {
            "version": "1.0.0",
            "last_updated": None,
            "signature_count": 0,
            "update_frequency": "weekly",
        }
        self._load_signatures()
    
    def _load_signatures(self) -> None:
        """Load signatures from disk."""
        try:
            if self.sig_file.exists():
                with open(self.sig_file, 'r') as f:
                    self.signatures = json.load(f)
                log_info("Signatures loaded from disk")
            
            if self.version_file.exists():
                with open(self.version_file, 'r') as f:
                    self.version_info = json.load(f)
        except Exception as e:
            log_error(f"Failed to load signatures: {e}")
            self.signatures = {}
    
    def _save_signatures(self) -> None:
        """Save signatures to disk."""
        try:
            self.sig_file.parent.mkdir(exist_ok=True)
            with open(self.sig_file, 'w') as f:
                json.dump(self.signatures, f, indent=2)
            
            self.version_info["signature_count"] = sum(
                len(sigs) for sigs in self.signatures.values()
            )
            self.version_info["last_updated"] = datetime.now().isoformat()
            
            with open(self.version_file, 'w') as f:
                json.dump(self.version_info, f, indent=2)
            
            log_info(f"Signatures saved: {self.version_info['signature_count']} total")
        except Exception as e:
            log_error(f"Failed to save signatures: {e}")
    
    def add_signature(self, category: str, signature: str) -> None:
        """
        Add individual signature.
        
        Args:
            category: Malware category
            signature: Signature pattern
        """
        if category not in self.signatures:
            self.signatures[category] = []
        
        if signature not in self.signatures[category]:
            self.signatures[category].append(signature)
            log_info(f"Added signature: {category} - {signature}")
    
    def add_signatures_batch(self, updates: Dict[str, List[str]]) -> None:
        """
        Add multiple signatures.
        
        Args:
            updates: Dict of category -> signatures list
        """
        for category, sigs in updates.items():
            if category not in self.signatures:
                self.signatures[category] = []
            
            # Add new signatures only
            for sig in sigs:
                if sig not in self.signatures[category]:
                    self.signatures[category].append(sig)
        
        self._save_signatures()
        log_info(f"Batch update: {len(updates)} categories updated")
    
    def remove_signature(self, category: str, signature: str) -> bool:
        """
        Remove signature.
        
        Args:
            category: Malware category
            signature: Signature pattern
            
        Returns:
            bool: True if removed, False if not found
        """
        if category in self.signatures:
            if signature in self.signatures[category]:
                self.signatures[category].remove(signature)
                self._save_signatures()
                return True
        return False
    
    def update_signatures(self, new_signatures: Dict[str, List[str]]) -> Tuple[bool, str]:
        """
        Update entire signature database.
        
        Args:
            new_signatures: Complete new signature database
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Validate new signatures
            if not self._validate_signatures(new_signatures):
                return False, "Signature validation failed"
            
            # Backup current signatures
            backup_file = self.sig_file.with_suffix('.bak')
            if self.sig_file.exists():
                self.sig_file.rename(backup_file)
            
            # Update signatures
            self.signatures = new_signatures
            self._save_signatures()
            
            log_info("Signature database updated successfully")
            return True, f"Updated {self.version_info['signature_count']} signatures"
        
        except Exception as e:
            log_error(f"Update failed: {e}")
            return False, str(e)
    
    def _validate_signatures(self, sigs: Dict[str, List[str]]) -> bool:
        """
        Validate signature database structure.
        
        Args:
            sigs: Signatures to validate
            
        Returns:
            bool: True if valid
        """
        if not isinstance(sigs, dict):
            return False
        
        for category, sig_list in sigs.items():
            if not isinstance(category, str):
                return False
            if not isinstance(sig_list, list):
                return False
            for sig in sig_list:
                if not isinstance(sig, str):
                    return False
        
        return True
    
    def check_update_needed(self) -> bool:
        """
        Check if signature update is needed.
        
        Returns:
            bool: True if update needed
        """
        if "last_updated" not in self.version_info:
            return True
        
        last_update = self.version_info["last_updated"]
        if not last_update:
            return True
        
        try:
            update_time = datetime.fromisoformat(last_update)
            age_days = (datetime.now() - update_time).days
            
            # Update if older than 7 days (configurable)
            return age_days >= 7
        except:
            return True
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dict: Statistics about signature database
        """
        stats = {
            "total_signatures": sum(len(sigs) for sigs in self.signatures.values()),
            "categories": len(self.signatures),
            "last_updated": self.version_info.get("last_updated"),
            "version": self.version_info.get("version"),
            "category_breakdown": {}
        }
        
        for category, sigs in self.signatures.items():
            stats["category_breakdown"][category] = len(sigs)
        
        return stats
    
    def export_signatures(self, output_file: str) -> bool:
        """
        Export signatures to file.
        
        Args:
            output_file: Output file path
            
        Returns:
            bool: True if successful
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(self.signatures, f, indent=2)
            log_info(f"Signatures exported to {output_file}")
            return True
        except Exception as e:
            log_error(f"Export failed: {e}")
            return False
    
    def import_signatures(self, input_file: str) -> bool:
        """
        Import signatures from file.
        
        Args:
            input_file: Input file path
            
        Returns:
            bool: True if successful
        """
        try:
            with open(input_file, 'r') as f:
                new_sigs = json.load(f)
            
            if self._validate_signatures(new_sigs):
                self.signatures = new_sigs
                self._save_signatures()
                log_info(f"Signatures imported from {input_file}")
                return True
            else:
                log_error("Imported signatures failed validation")
                return False
        except Exception as e:
            log_error(f"Import failed: {e}")
            return False


class SignatureUpdater:
    """Handles automatic signature updates."""
    
    # Public signature sources (examples)
    SIGNATURE_SOURCES = {
        "local": "file:///app/malware_db/signatures.json",
        "community": "https://example.com/signatures/community.json",
    }
    
    def __init__(self):
        """Initialize updater."""
        self.manager = SignatureManager()
    
    def check_for_updates(self) -> bool:
        """
        Check if updates are available.
        
        Returns:
            bool: True if updates available
        """
        return self.manager.check_update_needed()
    
    def fetch_remote_signatures(self, source: str) -> Tuple[bool, Dict]:
        """
        Fetch signatures from remote source.
        
        Args:
            source: Source URL
            
        Returns:
            Tuple[bool, Dict]: (success, signatures)
        """
        try:
            with urllib.request.urlopen(source, timeout=10) as response:
                data = json.loads(response.read().decode())
                return True, data
        except urllib.error.URLError as e:
            log_error(f"Failed to fetch signatures: {e}")
            return False, {}
        except Exception as e:
            log_error(f"Error fetching signatures: {e}")
            return False, {}
    
    def perform_update(self, source: str = "local") -> Tuple[bool, str]:
        """
        Perform signature update.
        
        Args:
            source: Update source key
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if source not in self.SIGNATURE_SOURCES:
            return False, f"Unknown source: {source}"
        
        source_url = self.SIGNATURE_SOURCES[source]
        
        log_info(f"Updating signatures from: {source}")
        success, new_sigs = self.fetch_remote_signatures(source_url)
        
        if success:
            return self.manager.update_signatures(new_sigs)
        else:
            return False, "Failed to fetch remote signatures"
    
    def validate_update(self, new_sigs: Dict) -> Tuple[bool, List[str]]:
        """
        Validate update before applying.
        
        Args:
            new_sigs: New signatures to validate
            
        Returns:
            Tuple[bool, List[str]]: (valid, issues found)
        """
        issues = []
        
        # Check structure
        if not isinstance(new_sigs, dict):
            issues.append("Not a dictionary")
        
        # Check categories
        if not new_sigs:
            issues.append("Empty signature database")
        
        # Check for suspicious removals
        old_count = self.manager.version_info.get("signature_count", 0)
        new_count = sum(len(sigs) for sigs in new_sigs.values())
        
        if new_count < old_count * 0.5:  # More than 50% reduction
            issues.append(f"Suspicious reduction: {old_count} -> {new_count}")
        
        return len(issues) == 0, issues
    
    def automatic_update(self, force: bool = False) -> Tuple[bool, str]:
        """
        Automatically update if needed.
        
        Args:
            force: Force update regardless of schedule
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not force and not self.check_for_updates():
            return True, "Signatures up to date"
        
        return self.perform_update()


def main():
    """Example usage."""
    manager = SignatureManager()
    
    # Show statistics
    stats = manager.get_statistics()
    print(f"\nSignature Database Statistics:")
    print(f"  Total signatures: {stats['total_signatures']}")
    print(f"  Categories: {stats['categories']}")
    print(f"  Last updated: {stats['last_updated']}")
    print(f"\nBreakdown:")
    for cat, count in stats['category_breakdown'].items():
        print(f"  • {cat}: {count}")
    
    # Check for updates
    updater = SignatureUpdater()
    if updater.check_for_updates():
        print("\nSignature update recommended!")
    else:
        print("\nSignatures are up to date.")


if __name__ == "__main__":
    main()
