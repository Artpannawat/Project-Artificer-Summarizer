import re

class TextProcessor:
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        # 1. Normalize line breaks: Replace single newlines with spaces, keep double newlines (paragraphs)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        # 2. Normalize whitespace (remove zero-width spaces, multiple spaces)
        text = re.sub(r"[\u200b\u200c\u200d\uFEFF]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        
        return text

    def segment_sentences(self, text: str) -> list[str]:
        """
        Segment text into sentences using PyThaiNLP for Thai support.
        """
        if not text:
            return []
            
        try:
            from pythainlp.tokenize import sent_tokenize
            # engine='crfcut' is usually accurate for sentence boundary detection
            sentences = sent_tokenize(text, engine='crfcut')
            return [s.strip() for s in sentences if s.strip()]
        except ImportError:
            # Fallback if PyThaiNLP is missing
            print("WARNING: PyThaiNLP not found, using basic segmentation fallback.")
            chunks = re.split(r'(?<=[.!?])\s+', text)
            return [c.strip() for c in chunks if c.strip()]
        except Exception as e:
            print(f"Segmentation Error: {e}")
            return [text]

    def tokenize_words(self, text: str) -> list[str]:
        """
        Tokenize text into words using PyThaiNLP (newmm engine).
        """
        if not text:
            return []
            
        try:
            from pythainlp.tokenize import word_tokenize
            # newmm is the standard dictionary-based tokenizer for Thai
            words = word_tokenize(text, engine='newmm', keep_whitespace=False)
            return [w for w in words if w.strip()]
        except ImportError:
            return text.split()