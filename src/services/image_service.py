import base64
import io
from PIL import Image
from typing import Optional

class ImageService:
    """Simplified image service without OCR"""
    
    async def process_image(self, image_data: bytes) -> dict:
        """Process image and extract metadata"""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Get image metadata
            metadata = {
                "format": image.format,
                "size": image.size,
                "mode": image.mode,
                "size_kb": len(image_data) / 1024
            }
            
            # Compress if needed
            if len(image_data) > 1024 * 1024:  # If larger than 1MB
                image_data = self.compress_image(image_data)
            
            return {
                "metadata": metadata,
                "image_data": base64.b64encode(image_data).decode('utf-8'),
                "extracted_text": None,  # No OCR for now
                "contains_math": False,
                "contains_diagram": True  # Assume all images are educational diagrams
            }
        except Exception as e:
            raise Exception(f"Image processing error: {str(e)}")
    
    def compress_image(self, image_data: bytes, max_size_kb: int = 500) -> bytes:
        """Compress image to reduce size"""
        image = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB if necessary
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        
        # Resize if too large
        max_dimension = 1024
        if image.width > max_dimension or image.height > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        # Save with compression
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        
        return output.getvalue()