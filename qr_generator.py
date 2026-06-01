"""
QR Code Generator - Creates QR codes for device profiles.
"""

from typing import Optional
from pathlib import Path
import subprocess
import json


class QRCodeGenerator:
    """Generates QR codes for device profiles and shareable links."""
    
    def __init__(self):
        """Initialize QR code generator."""
        self.qr_dir = Path("reports/qr_codes")
        self.qr_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_qr_code(self, data: str, filename: str) -> Optional[Path]:
        """
        Generate QR code image using qrcode library.
        
        Args:
            data: Data to encode in QR code
            filename: Output filename
            
        Returns:
            Path to QR code image or None
        """
        try:
            import qrcode
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=2,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save image
            filepath = self.qr_dir / filename
            img.save(filepath)
            
            return filepath
        except ImportError:
            # Fallback if qrcode not installed
            return self._generate_qr_with_external_tool(data, filename)
        except Exception as e:
            print(f"Error generating QR code: {str(e)}")
            return None
    
    def _generate_qr_with_external_tool(self, data: str, filename: str) -> Optional[Path]:
        """
        Fallback: Generate QR code using external tool.
        
        Args:
            data: Data to encode
            filename: Output filename
            
        Returns:
            Path to QR code or None
        """
        try:
            filepath = self.qr_dir / filename
            
            # Try using qrencode if available
            cmd = f'qrencode -o "{filepath}" "{data}"'
            result = subprocess.run(cmd, shell=True, capture_output=True)
            
            if result.returncode == 0 and filepath.exists():
                return filepath
        except Exception as e:
            print(f"QR code generation failed: {str(e)}")
        
        return None
    
    def generate_profile_qr(self, profile_id: str, url: str) -> Optional[Path]:
        """
        Generate QR code for device profile URL.
        
        Args:
            profile_id: Profile ID
            url: Device profile URL
            
        Returns:
            Path to QR code or None
        """
        filename = f"profile_qr_{profile_id}.png"
        return self.generate_qr_code(url, filename)
    
    def get_qr_code_path(self, profile_id: str) -> Path:
        """
        Get path to QR code for a profile.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Path to QR code file
        """
        return self.qr_dir / f"profile_qr_{profile_id}.png"
