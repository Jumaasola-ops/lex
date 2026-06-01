"""
Photo metadata extraction and removal module.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image
from PIL.ExifTags import TAGS
from exceptions import MetadataException, InvalidPhotoException
from utils import log_info, log_error, log_warning
from config import CRITICAL_METADATA_FIELDS


class MetadataHandler:
    """Handles photo metadata extraction and removal."""
    
    def __init__(self) -> None:
        """Initialize Metadata Handler."""
        log_info("Metadata Handler initialized")
    
    def extract_metadata(self, photo_path: str) -> Dict:
        """
        Extract metadata from photo.
        
        Args:
            photo_path: Path to photo file
            
        Returns:
            dict: Extracted metadata
            
        Raises:
            InvalidPhotoException: If photo is invalid or not supported
        """
        try:
            if not os.path.exists(photo_path):
                raise InvalidPhotoException(f"Photo file not found: {photo_path}")
            
            image = Image.open(photo_path)
            metadata = {
                "file_name": os.path.basename(photo_path),
                "file_path": photo_path,
                "file_size": os.path.getsize(photo_path),
                "image_format": image.format,
                "image_size": image.size,
                "exif_data": {},
            }
            
            # Extract EXIF data
            try:
                exif_data = image.getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        
                        # Convert bytes to string if necessary
                        if isinstance(value, bytes):
                            try:
                                value = value.decode('utf-8', errors='ignore')
                            except:
                                value = str(value)
                        
                        metadata["exif_data"][tag_name] = str(value)[:200]
            except Exception as e:
                log_warning(f"Could not extract full EXIF data: {str(e)}")
            
            # Extract IFD (Image File Directory) data
            try:
                if hasattr(image, "tag"):
                    metadata["ifd_data"] = dict(image.tag_v2)
            except:
                pass
            
            log_info(f"Metadata extracted from: {photo_path}")
            return metadata
            
        except Exception as e:
            raise InvalidPhotoException(f"Failed to extract metadata: {str(e)}")
    
    def remove_metadata(
        self,
        photo_path: str,
        output_path: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Remove metadata from photo.
        
        Args:
            photo_path: Path to original photo
            output_path: Path for cleaned photo (optional)
            
        Returns:
            Tuple[bool, str]: (success, output_path or error_message)
            
        Raises:
            InvalidPhotoException: If photo is invalid
        """
        try:
            if not os.path.exists(photo_path):
                raise InvalidPhotoException(f"Photo file not found: {photo_path}")
            
            # Generate output path if not provided
            if not output_path:
                file_stem = Path(photo_path).stem
                file_ext = Path(photo_path).suffix
                output_path = str(
                    Path(photo_path).parent / f"{file_stem}_cleaned{file_ext}"
                )
            
            # Open image and remove EXIF data
            image = Image.open(photo_path)
            
            # Create new image without metadata
            data = list(image.getdata())
            image_without_exif = Image.new(image.mode, image.size)
            image_without_exif.putdata(data)
            
            # Save cleaned image
            image_without_exif.save(output_path, quality=95)
            
            log_info(f"Metadata removed and saved to: {output_path}")
            return True, output_path
            
        except Exception as e:
            error_msg = f"Failed to remove metadata: {str(e)}"
            log_error(error_msg)
            raise InvalidPhotoException(error_msg)
    
    def batch_remove_metadata(
        self,
        photo_dir: str,
        output_dir: str,
        extensions: Optional[List[str]] = None,
    ) -> Dict:
        """
        Remove metadata from multiple photos.
        
        Args:
            photo_dir: Directory containing photos
            output_dir: Directory for cleaned photos
            extensions: List of file extensions to process (e.g., ['.jpg', '.png'])
            
        Returns:
            dict: Results of batch operation
        """
        if extensions is None:
            extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
        
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            raise MetadataException(f"Failed to create output directory: {str(e)}")
        
        results = {
            "total_files": 0,
            "processed": 0,
            "failed": 0,
            "errors": [],
            "output_directory": output_dir,
        }
        
        try:
            for file in os.listdir(photo_dir):
                file_path = os.path.join(photo_dir, file)
                
                if not os.path.isfile(file_path):
                    continue
                
                if not any(file.lower().endswith(ext) for ext in extensions):
                    continue
                
                results["total_files"] += 1
                
                try:
                    output_path = os.path.join(output_dir, file)
                    success, path = self.remove_metadata(file_path, output_path)
                    
                    if success:
                        results["processed"] += 1
                        log_info(f"Processed: {file}")
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"{file}: {path}")
                
                except Exception as e:
                    results["failed"] += 1
                    error_msg = f"{file}: {str(e)}"
                    results["errors"].append(error_msg)
                    log_error(error_msg)
            
            log_info(
                f"Batch processing complete: {results['processed']} processed, "
                f"{results['failed']} failed"
            )
            return results
            
        except Exception as e:
            raise MetadataException(f"Batch processing failed: {str(e)}")
    
    def display_metadata(self, metadata: Dict) -> None:
        """
        Display metadata in formatted output.
        
        Args:
            metadata: Metadata dictionary
        """
        print(f"\n{'='*60}")
        print("  PHOTO METADATA")
        print(f"{'='*60}\n")
        
        print(f"File: {metadata['file_name']}")
        print(f"Path: {metadata['file_path']}")
        print(f"Size: {metadata['file_size']} bytes")
        print(f"Format: {metadata['image_format']}")
        print(f"Dimensions: {metadata['image_size']}")
        
        if metadata["exif_data"]:
            print(f"\nEXIF Data ({len(metadata['exif_data'])} fields):")
            for key, value in metadata["exif_data"].items():
                print(f"  • {key}: {value}")
        else:
            print("\nNo EXIF data found")
    
    def get_critical_metadata(self, photo_path: str) -> List[Tuple[str, str]]:
        """
        Extract only critical privacy-sensitive metadata.
        
        Args:
            photo_path: Path to photo file
            
        Returns:
            List[Tuple[str, str]]: List of (field_name, value) tuples
        """
        try:
            metadata = self.extract_metadata(photo_path)
            
            critical_data = []
            for field in CRITICAL_METADATA_FIELDS:
                if field in metadata["exif_data"]:
                    critical_data.append((field, metadata["exif_data"][field]))
            
            return critical_data
            
        except Exception as e:
            log_error(f"Failed to get critical metadata: {str(e)}")
            return []
