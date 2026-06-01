"""
Input Validation & Sanitization Framework.
Author: Asola Junior
Prevents injection attacks and ensures data integrity across all operations.
"""

import re
from typing import Tuple, Optional, List
from pathlib import Path
from urllib.parse import urlparse

from utils import log_warning


class ValidationError(ValueError):
    """Raised when validation fails."""
    pass


class InputValidator:
    """Validates and sanitizes all user input."""
    
    # Regex patterns for validation
    DEVICE_ID_PATTERN = r'^[a-zA-Z0-9._:-]+$'
    PACKAGE_NAME_PATTERN = r'^[a-zA-Z0-9._]+$'
    IP_ADDRESS_PATTERN = r'^(\d{1,3}\.){3}\d{1,3}$'
    PORT_PATTERN = r'^[0-9]{1,5}$'
    SHA256_PATTERN = r'^[a-fA-F0-9]{64}$'
    MD5_PATTERN = r'^[a-fA-F0-9]{32}$'
    
    # Dangerous ADB command patterns to block
    DANGEROUS_ADB_PATTERNS = [
        r';\s*rm\s+',           # rm command
        r'&&\s*rm\s+',
        r'\|\s*rm\s+',          # Pipe to rm
        r'`.*rm.*`',            # Command substitution
        r'\$\(.*rm.*\)',
        r'>\s*/dev/null',       # Redirect to device files
        r'<\s*/dev/',
        r'dd\s+of=',            # Direct device writes
        r'mkfs',                # Filesystem format
        r'format\s+',
    ]
    
    @staticmethod
    def validate_device_id(device_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate device ID format.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Tuple[bool, Optional[str]]: (valid, error_message)
        """
        if not device_id or not isinstance(device_id, str):
            return False, "Device ID must be a non-empty string"
        
        device_id = device_id.strip()
        
        if len(device_id) > 150:
            return False, "Device ID too long (max 150 chars)"
        
        # Check for wireless device format (IP:port)
        if ':' in device_id:
            parts = device_id.split(':')
            if len(parts) != 2:
                return False, "Invalid device format (IP:port expected)"
            
            ip, port = parts
            if not InputValidator._is_valid_ip(ip):
                return False, f"Invalid IP address: {ip}"
            
            if not InputValidator._is_valid_port(port):
                return False, f"Invalid port: {port}"
        
        # Check for USB device format
        elif not re.match(InputValidator.DEVICE_ID_PATTERN, device_id):
            return False, f"Invalid device ID format: {device_id}"
        
        return True, None
    
    @staticmethod
    def validate_package_name(package_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Android package name format.
        
        Args:
            package_name: Package identifier
            
        Returns:
            Tuple[bool, Optional[str]]: (valid, error_message)
        """
        if not package_name or not isinstance(package_name, str):
            return False, "Package name must be a non-empty string"
        
        package_name = package_name.strip()
        
        if len(package_name) > 256:
            return False, "Package name too long (max 256 chars)"
        
        if not re.match(InputValidator.PACKAGE_NAME_PATTERN, package_name):
            return False, f"Invalid package name format: {package_name}"
        
        # Package names must have at least 2 parts
        parts = package_name.split('.')
        if len(parts) < 2:
            return False, "Package name must contain at least 2 parts (e.g., com.example)"
        
        # Each part must start with letter or number
        for part in parts:
            if not part or not part[0].isalnum():
                return False, f"Invalid package name part: {part}"
        
        return True, None
    
    @staticmethod
    def validate_file_path(file_path: str, allow_absolute: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Validate file path to prevent directory traversal attacks.
        
        Args:
            file_path: File path to validate
            allow_absolute: Allow absolute paths
            
        Returns:
            Tuple[bool, Optional[str]]: (valid, error_message)
        """
        if not file_path or not isinstance(file_path, str):
            return False, "File path must be a non-empty string"
        
        file_path = file_path.strip()
        
        # Check for directory traversal
        if '..' in file_path:
            return False, "Path traversal detected (.. not allowed)"
        
        # Check for null bytes
        if '\x00' in file_path:
            return False, "Null bytes not allowed in path"
        
        # Check for absolute path if not allowed
        if not allow_absolute and Path(file_path).is_absolute():
            return False, "Absolute paths not allowed"
        
        # Check length
        if len(file_path) > 4096:
            return False, "File path too long (max 4096 chars)"
        
        return True, None
    
    @staticmethod
    def validate_adb_command(command: str) -> Tuple[bool, Optional[str]]:
        """
        Validate ADB shell command for dangerous patterns.
        
        Args:
            command: Shell command to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (valid, error_message)
        """
        if not command or not isinstance(command, str):
            return False, "Command must be a non-empty string"
        
        command = command.strip()
        
        if len(command) > 2048:
            return False, "Command too long (max 2048 chars)"
        
        # Check for dangerous patterns
        for pattern in InputValidator.DANGEROUS_ADB_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                log_warning(f"Dangerous ADB pattern detected: {pattern}")
                return False, f"Potentially dangerous command detected"
        
        # Check for null bytes
        if '\x00' in command:
            return False, "Null bytes not allowed in command"
        
        # Check for excessive special characters
        special_count = sum(1 for c in command if c in '&|;`$()[]{}')
        if special_count > 10:
            log_warning(f"Excessive special characters in command: {special_count}")
            return False, "Too many special characters in command"
        
        return True, None
    
    @staticmethod
    def validate_ip_address(ip_address: str) -> Tuple[bool, Optional[str]]:
        """
        Validate IPv4 address.
        
        Args:
            ip_address: IP address to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (valid, error_message)
        """
        if not ip_address or not isinstance(ip_address, str):
            return False, "IP address must be a non-empty string"
        
        ip_address = ip_address.strip()
        
        if not re.match(InputValidator.IP_ADDRESS_PATTERN, ip_address):
            return False, f"Invalid IP address format: {ip_address}"
        
        # Validate each octet
        try:
            octets = ip_address.split('.')
            for octet in octets:
                num = int(octet)
                if num < 0 or num > 255:
                    return False, f"Octet out of range: {octet}"
        except ValueError:
            return False, f"Invalid IP address: {ip_address}"
        
        return True, None
    
    @staticmethod
    def validate_port(port: int | str) -> Tuple[bool, Optional[str]]:
        """
        Validate port number.
        
        Args:
            port: Port number (int or str)
            
        Returns:
            Tuple[bool, Optional[str]]: (valid, error_message)
        """
        try:
            port_num = int(port) if isinstance(port, str) else port
            
            if port_num < 1 or port_num > 65535:
                return False, f"Port must be between 1 and 65535: {port_num}"
            
            return True, None
        except (ValueError, TypeError):
            return False, f"Invalid port number: {port}"
    
    @staticmethod
    def validate_hash(hash_value: str, hash_type: str = "sha256") -> Tuple[bool, Optional[str]]:
        """
        Validate hash value format.
        
        Args:
            hash_value: Hash string
            hash_type: Type of hash (sha256, md5)
            
        Returns:
            Tuple[bool, Optional[str]]: (valid, error_message)
        """
        if not hash_value or not isinstance(hash_value, str):
            return False, "Hash must be a non-empty string"
        
        hash_value = hash_value.strip().lower()
        
        if hash_type.lower() == "sha256":
            if not re.match(InputValidator.SHA256_PATTERN, hash_value):
                return False, "Invalid SHA256 hash format (must be 64 hex characters)"
        elif hash_type.lower() == "md5":
            if not re.match(InputValidator.MD5_PATTERN, hash_value):
                return False, "Invalid MD5 hash format (must be 32 hex characters)"
        else:
            return False, f"Unknown hash type: {hash_type}"
        
        return True, None
    
    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, Optional[str]]:
        """
        Validate API key format.
        
        Args:
            api_key: API key string
            
        Returns:
            Tuple[bool, Optional[str]]: (valid, error_message)
        """
        if not api_key or not isinstance(api_key, str):
            return False, "API key must be a non-empty string"
        
        api_key = api_key.strip()
        
        if len(api_key) < 16 or len(api_key) > 256:
            return False, "API key length invalid (16-256 chars expected)"
        
        # API keys should be alphanumeric (and possibly hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
            return False, "API key contains invalid characters"
        
        return True, None
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (valid, error_message)
        """
        if not url or not isinstance(url, str):
            return False, "URL must be a non-empty string"
        
        url = url.strip()
        
        try:
            result = urlparse(url)
            
            if not result.scheme or result.scheme not in ['http', 'https']:
                return False, "URL must use http or https protocol"
            
            if not result.netloc:
                return False, "URL must have a valid domain"
            
            return True, None
        except Exception as e:
            return False, f"Invalid URL: {str(e)}"
    
    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """Helper to validate IP address."""
        valid, _ = InputValidator.validate_ip_address(ip)
        return valid
    
    @staticmethod
    def _is_valid_port(port: str) -> bool:
        """Helper to validate port."""
        valid, _ = InputValidator.validate_port(port)
        return valid
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename by removing dangerous characters.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        # Remove path separators and null bytes
        sanitized = filename.replace('/', '_').replace('\\', '_').replace('\x00', '')
        
        # Remove directory traversal patterns
        sanitized = sanitized.replace('..', '_')
        
        # Remove leading dots and spaces
        sanitized = sanitized.lstrip('. ')
        
        # Replace multiple spaces with single space
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Keep only safe characters
        sanitized = re.sub(r'[^a-zA-Z0-9._\- ]', '', sanitized)
        
        # Limit length
        max_len = 255
        if len(sanitized) > max_len:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            name = name[:max_len - len(ext) - 1]
            sanitized = f"{name}.{ext}" if ext else name
        
        return sanitized or 'file'
    
    @staticmethod
    def sanitize_command(command: str) -> str:
        """
        Sanitize shell command by escaping dangerous characters.
        
        Args:
            command: Original command
            
        Returns:
            str: Sanitized command
        """
        # Remove null bytes
        command = command.replace('\x00', '')
        
        # Escape quotes
        command = command.replace('"', '\\"')
        command = command.replace("'", "\\'")
        
        return command


def main():
    """Test validator."""
    validator = InputValidator()
    
    # Test device ID
    print("\nDevice ID Validation:")
    tests = [
        "emulator-5554",
        "192.168.1.100:5555",
        "invalid::id",
        "../../../etc/passwd",
    ]
    
    for test in tests:
        valid, error = validator.validate_device_id(test)
        print(f"  {test}: {'✓' if valid else '✗'} {error or ''}")
    
    # Test package name
    print("\nPackage Name Validation:")
    tests = [
        "com.example.app",
        "com.malware.trojan",
        "invalid",
        "com..example",
    ]
    
    for test in tests:
        valid, error = validator.validate_package_name(test)
        print(f"  {test}: {'✓' if valid else '✗'} {error or ''}")
    
    print("\nValidator ready for integration.")


if __name__ == "__main__":
    main()
