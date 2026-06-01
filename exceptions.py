"""
Custom exceptions for Android Security Scanner.
"""


class AndroidSecurityException(Exception):
    """Base exception for Android Security Scanner."""
    pass


class ADBException(AndroidSecurityException):
    """Exception raised for ADB-related errors."""
    pass


class ADBConnectionException(ADBException):
    """Exception raised when ADB connection fails."""
    pass


class ADBDeviceNotFound(ADBException):
    """Exception raised when connected device is not found."""
    pass


class ADBTimeoutException(ADBException):
    """Exception raised when ADB command times out."""
    pass


class MalwareScanException(AndroidSecurityException):
    """Exception raised during malware scanning."""
    pass


class AppAnalysisException(AndroidSecurityException):
    """Exception raised during app analysis."""
    pass


class MetadataException(AndroidSecurityException):
    """Exception raised during metadata operations."""
    pass


class InvalidPhotoException(MetadataException):
    """Exception raised when photo file is invalid."""
    pass


class CommandException(AndroidSecurityException):
    """Exception raised for command-related errors."""
    pass


class InvalidCommandException(CommandException):
    """Exception raised for invalid command syntax."""
    pass


class FileCrawlerException(Exception):
    """Exception raised during file crawling."""
    pass


class ProcessAnalyzerException(Exception):
    """Exception raised during process analysis."""
    pass


class SystemAnalyzerException(Exception):
    """Exception raised during system analysis."""
    pass


class MalwareRemovalException(Exception):
    """Exception raised during malware removal."""
    pass
