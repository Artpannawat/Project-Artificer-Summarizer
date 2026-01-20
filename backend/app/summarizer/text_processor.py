import re

class TextProcessor:
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        # 1. Normalize line breaks: Replace single newlines with spaces, keep double newlines (paragraphs)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        # 2. Normalize whitespace (remove zero-width spaces, multiple spaces)
        text = re.sub(r"[\u200b\u200c\u200d\uFEFF]", "", text)
        
        # 3. Thai Normalization: Combine Nikhahit + Sara Aa -> Sara Am (Standardize decomposed chars)
        text = text.replace('\u0E4D\u0E32', '\u0E33') 
        # Also fix reverse order just in case (Sara Aa + Nikhahit) -> Sara Am
        text = text.replace('\u0E32\u0E4D', '\u0E33')

        # 4. Clean spacing
        text = re.sub(r"\s+", " ", text).strip()

        # 5. Fix broken Thai text (PDF extraction often adds spaces between characters: เ ค รื่ อ ง)
        # Regex: Look for space between two Thai characters and remove it
        text = re.sub(r'(?<=[\u0E00-\u0E7F])\s+(?=[\u0E00-\u0E7F])', '', text)
        
        return text

    
    def __init__(self):
        from .constants import THAI_DICT
        self.thai_dict = THAI_DICT
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
        Segment text into partial sentences/phrases using punctuation and spacing.
        Enhanced for Thai/English mixed text to reduce "choppy" output.
        """
        if not text:
            return []
            
        # 1. Clean up excessive whitespace first
        text = re.sub(r' +', ' ', text.strip())
        
        # 2. Split by standard punctuation (.!?) followed by space
        # Lookbehind for punctuation, lookahead for space or end of string
        # Keep punctuation attached to the previous sentence if possible
        chunks = re.split(r'(?<=[.!?])\s+', text)
        
        final_sentences = []
        for chunk in chunks:
            if not chunk.strip():
                continue
                
            # 3. Handling Thai long paragraphs without punctuation
            if len(chunk) > 120:
                # If we stripped spaces, splitting by ' ' won't work.
                # Use tokenize() to recover word boundaries, then group them.
                
                words = self.tokenize(chunk)
                current_sent = []
                current_len = 0
                
                # Intelligent Splitters
                conjunctions = {'ดังนั้น', 'เพราะ', 'แต่', 'อย่างไรก็ตาม', 'นอกจากนี้', 'ทั้งนี้', 'โดย', 'เพื่อ', 'สำหรับ', 'ซึ่ง', 'ที่'}
                
                for word in words:
                    # If current sentence is substantial AND we hit a conjunction OR it's just getting too long
                    should_split = False
                    
                    if current_len > 60: # Minimum length before considering split
                        if word in conjunctions:
                            should_split = True
                        elif current_len > 150: # Hard limit fallback
                            should_split = True
                    
                    if should_split:
                        final_sentences.append("".join(current_sent)) # Thai usually has no space
                        current_sent = [word]
                        current_len = len(word)
                    else:
                        current_sent.append(word)
                        current_len += len(word)
                
                if current_sent:
                    final_sentences.append("".join(current_sent))
            else:
                final_sentences.append(chunk.strip())
                
        return [s.strip() for s in final_sentences if s.strip()]