import re

class TextProcessor:
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        # 1. Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 2. Thai Normalization: Combine Nikhahit + Sara Aa -> Sara Am
        text = text.replace('\u0E4D\u0E32', '\u0E33') 
        text = text.replace('\u0E32\u0E4D', '\u0E33')

        # 3. Collapse multiple spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()

    def __init__(self):
        try:
            from .constants import THAI_DICT
            self.thai_dict = THAI_DICT
        except ImportError:
            self.thai_dict = set()
        self.max_word_len = 20 # Max length to scan for dictionary match

    def tokenize(self, text: str) -> list[str]:
        """
        Tokenize text into words using Maximum Matching with a small embedded dictionary.
        Essential for Thai TextRank to work (since Thai has no spaces).
        """
        if not text:
            return []

        # 1. Pre-split by spaces/newlines first (easy wins)
        chunks = text.split()
        tokens = []

        for chunk in chunks:
            # If chunk is English/Numbers (mostly), just keep it
            if re.match(r'^[a-zA-Z0-9\.\-\,]+$', chunk):
                tokens.append(chunk)
                continue
                
            # Thai MaxMatch Logic
            i = 0
            while i < len(chunk):
                found = False
                # Try to find longest matching word from dictionary
                if self.thai_dict:
                    for j in range(min(len(chunk), i + self.max_word_len), i, -1):
                        word = chunk[i:j]
                        if word in self.thai_dict:
                            tokens.append(word)
                            i = j
                            found = True
                            break
                
                if not found:
                    # If not found in dict, take 1 character
                    tokens.append(chunk[i])
                    i += 1
        
        return tokens

    def segment_sentences(self, text: str) -> list[str]:
        """
        Segment text into sentences using traditional Thai logic (Space delimeted)
        plus newlines and punctuation.
        """
        if not text:
            return []
            
        # 1. Split by newlines first (Paragraphs often imply sentence breaks)
        # Using keepends=False to drop the newline chars
        lines = text.splitlines()
        
        sentences = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 2. Split by standard punctuation if present
            # 3. Also split by space, as Thai uses space for sentence boundaries
            # We filter out empty strings
            chunks = re.split(r'[\s.!?]+', line)
            
            for chunk in chunks:
                if chunk.strip():
                    sentences.append(chunk.strip())
                
        return sentences