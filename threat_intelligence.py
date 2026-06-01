"""
Threat Intelligence Integration Framework.
Author: Asola Junior
Integrates VirusTotal API, abuse.ch feeds, and threat databases for enhanced detection.
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.error

from utils import log_info, log_error, log_warning


class ThreatIntelligenceProvider:
    """Base class for threat intelligence providers."""
    
    def check_hash(self, file_hash: str) -> Tuple[bool, Optional[Dict]]:
        """Check if hash is known malicious."""
        raise NotImplementedError
    
    def check_url(self, url: str) -> Tuple[bool, Optional[Dict]]:
        """Check if URL is known malicious."""
        raise NotImplementedError
    
    def check_ip(self, ip_address: str) -> Tuple[bool, Optional[Dict]]:
        """Check if IP is known malicious."""
        raise NotImplementedError


class VirusTotalProvider(ThreatIntelligenceProvider):
    """VirusTotal API integration for threat intelligence."""
    
    BASE_URL = "https://www.virustotal.com/api/v3"
    RATE_LIMIT_DELAY = 0.2  # seconds between requests
    
    def __init__(self, api_key: str):
        """
        Initialize VirusTotal provider.
        
        Args:
            api_key: VirusTotal API key
        """
        self.api_key = api_key
        self.last_request_time = 0
        self.cache_file = Path("cache/virustotal_cache.json")
        self.cache_file.parent.mkdir(exist_ok=True)
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cached results."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            log_error(f"Failed to save cache: {e}")
    
    def _rate_limit(self):
        """Apply rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def check_hash(self, file_hash: str) -> Tuple[bool, Optional[Dict]]:
        """
        Check hash against VirusTotal.
        
        Args:
            file_hash: SHA256, SHA1, or MD5 hash
            
        Returns:
            Tuple[bool, Dict]: (is_malicious, details)
        """
        # Check cache first
        if file_hash in self.cache:
            cached = self.cache[file_hash]
            if datetime.fromisoformat(cached["timestamp"]) > datetime.now() - timedelta(days=30):
                return cached["malicious"], cached["details"]
        
        try:
            self._rate_limit()
            
            headers = {"x-apikey": self.api_key}
            url = f"{self.BASE_URL}/files/{file_hash}"
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            # Parse results
            attributes = data.get("data", {}).get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})
            
            malicious = stats.get("malicious", 0) > 0
            
            result = {
                "malicious": malicious,
                "detections": stats,
                "names": attributes.get("meaningful_name", ""),
                "type": attributes.get("type_description", ""),
                "timestamp": datetime.now().isoformat(),
            }
            
            # Cache result
            self.cache[file_hash] = {"malicious": malicious, "details": result}
            self._save_cache()
            
            return malicious, result
        
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Not found - likely not malicious
                return False, None
            elif e.code == 401:
                log_error("Invalid VirusTotal API key")
                return False, None
            else:
                log_error(f"VirusTotal API error: {e}")
                return False, None
        
        except Exception as e:
            log_error(f"Error checking hash: {e}")
            return False, None
    
    def check_url(self, url: str) -> Tuple[bool, Optional[Dict]]:
        """
        Check URL against VirusTotal.
        
        Args:
            url: URL to check
            
        Returns:
            Tuple[bool, Dict]: (is_malicious, details)
        """
        try:
            self._rate_limit()
            
            headers = {"x-apikey": self.api_key}
            data = urllib.parse.urlencode({"url": url}).encode()
            
            req = urllib.request.Request(
                f"{self.BASE_URL}/urls",
                data=data,
                headers=headers,
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode())
            
            attributes = result.get("data", {}).get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})
            
            malicious = stats.get("malicious", 0) > 0
            
            details = {
                "malicious": malicious,
                "detections": stats,
                "categories": attributes.get("categories", {}),
                "timestamp": datetime.now().isoformat(),
            }
            
            return malicious, details
        
        except Exception as e:
            log_error(f"Error checking URL: {e}")
            return False, None
    
    def check_ip(self, ip_address: str) -> Tuple[bool, Optional[Dict]]:
        """
        Check IP address against VirusTotal.
        
        Args:
            ip_address: IP to check
            
        Returns:
            Tuple[bool, Dict]: (is_suspicious, details)
        """
        try:
            self._rate_limit()
            
            headers = {"x-apikey": self.api_key}
            url = f"{self.BASE_URL}/ip_addresses/{ip_address}"
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            attributes = data.get("data", {}).get("attributes", {})
            
            suspicious = (
                attributes.get("last_analysis_stats", {}).get("malicious", 0) > 0 or
                attributes.get("last_analysis_stats", {}).get("suspicious", 0) > 0
            )
            
            details = {
                "suspicious": suspicious,
                "country": attributes.get("country", ""),
                "asn": attributes.get("asn", ""),
                "detections": attributes.get("last_analysis_stats", {}),
                "timestamp": datetime.now().isoformat(),
            }
            
            return suspicious, details
        
        except Exception as e:
            log_error(f"Error checking IP: {e}")
            return False, None


class AbuseChProvider(ThreatIntelligenceProvider):
    """abuse.ch threat feed integration."""
    
    URLHAUS_API = "https://urlhaus-api.abuse.ch/v1"
    MALWAREBAZAAR_API = "https://api.abuse.ch/api/v1"
    
    def __init__(self):
        """Initialize abuse.ch provider."""
        self.cache_file = Path("cache/abusech_cache.json")
        self.cache_file.parent.mkdir(exist_ok=True)
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cached results."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            log_error(f"Failed to save cache: {e}")
    
    def check_hash(self, file_hash: str) -> Tuple[bool, Optional[Dict]]:
        """Check hash against abuse.ch malware bazaar."""
        try:
            if file_hash in self.cache:
                return self.cache[file_hash]["malicious"], self.cache[file_hash].get("details")
            
            data = urllib.parse.urlencode({
                "query": "get_info",
                "hash": file_hash
            }).encode()
            
            with urllib.request.urlopen(
                f"{self.MALWAREBAZAAR_API}",
                data=data,
                timeout=10
            ) as response:
                result = json.loads(response.read().decode())
            
            if result.get("query_status") == "ok":
                details = result.get("data", {})
                
                self.cache[file_hash] = {
                    "malicious": True,
                    "details": {
                        "sha256": details.get("sha256_hash"),
                        "tags": details.get("tags", []),
                        "first_seen": details.get("first_seen"),
                    }
                }
                self._save_cache()
                return True, self.cache[file_hash]["details"]
            
            return False, None
        
        except Exception as e:
            log_error(f"Error checking hash with abuse.ch: {e}")
            return False, None
    
    def check_url(self, url: str) -> Tuple[bool, Optional[Dict]]:
        """Check URL against URLhaus."""
        try:
            data = urllib.parse.urlencode({
                "query": "host",
                "url": url
            }).encode()
            
            with urllib.request.urlopen(
                f"{self.URLHAUS_API}/url/",
                data=data,
                timeout=10
            ) as response:
                result = json.loads(response.read().decode())
            
            if result.get("query_status") == "ok":
                urls = result.get("urls", [])
                
                if urls:
                    return True, {
                        "malicious": True,
                        "urls": urls,
                        "timestamp": datetime.now().isoformat(),
                    }
            
            return False, None
        
        except Exception as e:
            log_error(f"Error checking URL with abuse.ch: {e}")
            return False, None
    
    def check_ip(self, ip_address: str) -> Tuple[bool, Optional[Dict]]:
        """Check IP address against abuse.ch."""
        # abuse.ch doesn't have direct IP checking API
        return False, None


class ThreatIntelligenceAggregator:
    """Aggregates threat intelligence from multiple sources."""
    
    def __init__(self, vt_api_key: Optional[str] = None):
        """
        Initialize threat intelligence aggregator.
        
        Args:
            vt_api_key: VirusTotal API key (optional)
        """
        self.providers: Dict[str, ThreatIntelligenceProvider] = {}
        
        if vt_api_key:
            self.providers["virustotal"] = VirusTotalProvider(vt_api_key)
            log_info("VirusTotal provider enabled")
        
        self.providers["abusech"] = AbuseChProvider()
        log_info("abuse.ch provider enabled")
    
    def check_file_hash(self, file_hash: str) -> Dict[str, Any]:
        """
        Check file hash across all providers.
        
        Args:
            file_hash: SHA256, SHA1, or MD5 hash
            
        Returns:
            Dict with aggregated results
        """
        results = {
            "hash": file_hash,
            "malicious": False,
            "detections": {},
            "providers": {},
        }
        
        for name, provider in self.providers.items():
            try:
                is_malicious, details = provider.check_hash(file_hash)
                
                if is_malicious:
                    results["malicious"] = True
                
                results["providers"][name] = {
                    "malicious": is_malicious,
                    "details": details,
                }
            
            except Exception as e:
                log_error(f"Error with {name} provider: {e}")
        
        return results
    
    def check_url(self, url: str) -> Dict[str, Any]:
        """
        Check URL across all providers.
        
        Args:
            url: URL to check
            
        Returns:
            Dict with aggregated results
        """
        results = {
            "url": url,
            "malicious": False,
            "detections": {},
            "providers": {},
        }
        
        for name, provider in self.providers.items():
            try:
                is_malicious, details = provider.check_url(url)
                
                if is_malicious:
                    results["malicious"] = True
                
                results["providers"][name] = {
                    "malicious": is_malicious,
                    "details": details,
                }
            
            except Exception as e:
                log_error(f"Error with {name} provider: {e}")
        
        return results
    
    def check_apk_safety(self, apk_hash: str) -> Tuple[bool, str]:
        """
        Quick check if APK is known malicious.
        
        Args:
            apk_hash: APK file hash
            
        Returns:
            Tuple[bool, str]: (is_safe, verdict)
        """
        result = self.check_file_hash(apk_hash)
        
        if result["malicious"]:
            return False, "APK flagged as malicious by threat intelligence"
        
        return True, "APK appears safe (not in threat databases)"


def main():
    """Test threat intelligence integration."""
    print("\nThreat Intelligence Framework")
    print("=" * 50)
    
    # Initialize with abuse.ch only (no VirusTotal API key)
    aggregator = ThreatIntelligenceAggregator()
    
    print("\nProviders enabled:", list(aggregator.providers.keys()))
    print("\nUsage examples:")
    print("  is_safe, verdict = aggregator.check_apk_safety(hash)")
    print("  url_result = aggregator.check_url('https://example.com')")
    print("  hash_result = aggregator.check_file_hash('sha256hash...')")


if __name__ == "__main__":
    main()
