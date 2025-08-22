import re
from pythainlp.util import normalize

class TextProcessor:
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        # Normalize Thai text if it contains Thai characters
        if re.search(r"[\u0E00-\u0E7F]", text):
            text = normalize(text)
        
        # Remove extra whitespace while preserving sentence boundaries
        cleaned_text = re.sub(r"\s+", " ", text).strip()
        
        # Keep punctuation and sentence structure
        return cleaned_text