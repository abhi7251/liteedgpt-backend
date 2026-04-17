from typing import Optional
import re

class Validators:
    @staticmethod
    def validate_text_input(text: str) -> tuple[bool, Optional[str]]:
        """Validate text input"""
        if not text or not text.strip():
            return False, "Text input cannot be empty"
        
        if len(text) > 5000:
            return False, "Text input too long (max 5000 characters)"
        
        # Check for potential harmful content
        harmful_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'onclick=',
            r'onerror='
        ]
        
        for pattern in harmful_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "Invalid content detected"
        
        return True, None
    
    @staticmethod
    def validate_image(image_data: bytes) -> tuple[bool, Optional[str]]:
        """Validate image data"""
        if not image_data:
            return False, "No image data provided"
        
        # Check file size (max 10MB)
        if len(image_data) > 10 * 1024 * 1024:
            return False, "Image too large (max 10MB)"
        
        # Validate image content and format using Pillow.
        # This avoids Python-version issues with imghdr.
        try:
            from PIL import Image
            from io import BytesIO

            image = Image.open(BytesIO(image_data))
            image.verify()

            # Re-open after verify() because verify() leaves the file in an unusable state.
            image = Image.open(BytesIO(image_data))
            image_type = (image.format or "").lower()
        except Exception:
            return False, "Invalid image format"

        if image_type not in ['jpeg', 'png', 'gif', 'bmp', 'webp']:
            return False, "Invalid image format"
        
        return True, None
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input"""
        # Remove any HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Limit consecutive characters
        text = re.sub(r'(.)\1{10,}', r'\1' * 10, text)
        
        return text.strip()