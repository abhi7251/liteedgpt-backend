import base64
import io
from PIL import Image
from typing import Optional
import re

class ImageService:
    """Image service with optional OCR extraction."""
    
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

            extracted_text = self._extract_text(image_data)
            contains_math = self._detect_math_content(extracted_text)
            contains_diagram = self._detect_diagram_content(extracted_text, metadata)
            
            return {
                "metadata": metadata,
                "image_data": base64.b64encode(image_data).decode('utf-8'),
                "extracted_text": extracted_text,
                "contains_math": contains_math,
                "contains_diagram": contains_diagram
            }
        except Exception as e:
            raise Exception(f"Image processing error: {str(e)}")

    def _extract_text(self, image_data: bytes) -> Optional[str]:
        """Extract text from image using optional OCR backends.

        Priority:
        1) pytesseract (if installed and tesseract binary is available)
        2) no OCR fallback (returns None)
        """
        try:
            import importlib
            pytesseract = importlib.import_module("pytesseract")

            image = Image.open(io.BytesIO(image_data))
            # Improve OCR quality by converting to grayscale and mild contrast.
            image = image.convert('L')
            text = pytesseract.image_to_string(image)
            cleaned = (text or '').strip()
            return cleaned if cleaned else None
        except Exception:
            return None

    def _detect_math_content(self, extracted_text: Optional[str]) -> bool:
        """Heuristic detection for math-heavy images."""
        if not extracted_text:
            return False

        math_patterns = [
            r"\d+\s*[+\-*/=]\s*\d+",
            r"\b(sin|cos|tan|log|sqrt|pi)\b",
            r"\b(x|y|z)\s*[=<>]",
            r"\b\d+\s*%\b",
            r"\bcm\b|\bmm\b|\bkg\b|\bm/s\b",
        ]

        text = extracted_text.lower()
        return any(re.search(pattern, text) for pattern in math_patterns)

    def _detect_diagram_content(self, extracted_text: Optional[str], metadata: dict) -> bool:
        """Heuristic detection for diagram-like content."""
        if extracted_text and len(extracted_text.split()) > 20:
            return False

        # Low-text images are often diagrams/photos in homework contexts.
        return True
    
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