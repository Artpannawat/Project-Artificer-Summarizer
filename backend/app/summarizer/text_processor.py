import re

class TextProcessor:
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        # Simple normalization (remove zero-width spaces, etc.)
        # Thai characters: \u0E00-\u0E7F
        
        # Remove extra whitespace while preserving sentence boundaries
        cleaned_text = re.sub(r"\s+", " ", text).strip()
        
        # Keep punctuation and sentence structure
        return cleaned_text