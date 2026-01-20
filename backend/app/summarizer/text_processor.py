import re

class TextProcessor:
    def clean_text(self, text: str) -> str:
        if not text:
            return ""

        # 1. Filter Noise (Script artifacts) - Moved to TOP
        
        # A. Delete WHOLE lines for technical headers (Scenes, Camera, Visuals)
        delete_patterns = [
            r'(?i)^\s*(?:Scene|Int\.|Ext\.|ซีน|ฉาก)\s*[\d:]+.*$', 
            r'(?i)^\s*(?:Camera(?:\s*Angle)?|Cut\s*to|มุมกล้อง|ภาพ|Visual)\s*[:\s].*$',
            r'(?i)^\s*\[\s*.*\s*\]\s*$' # Lines that are just [timestamps] or [actions]
        ]
        for pattern in delete_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE)

        # B. Delete ONLY PREFIXES for Dialogue/VO (Keep the content!)
        # Pattern: "Speaker: " -> ""
        prefix_patterns = [
            r'(?i)^\s*(?:Voice\s*Over|VO|เสียงบรรยาย|บทพูด|Dialogue|Line)\s*[:\s]+', 
            r'(?i)^\s*(?:นักแสดง|ตัวละคร|Character|Cast|พี่\s*[A-Z])\s*[:\s]+',
            r'(?i)^\s*[A-Z\s]+:\s', # ENGLISH_NAME: ...
            r'(?i)^\s*[^:\n]+:\s' # Generic Name: ... (Catch all remaining speaker labels if possible, careful not to eat sentences)
        ]
        for pattern in prefix_patterns:
            text = re.sub(pattern, ' ', text, flags=re.MULTILINE)

        # C. Cleaning common list bullets/OCRs that mess up TextRank
        # Remove leading "•", "-", "0", "*" at start of lines
        text = re.sub(r'(?m)^\s*[•●▪\-*0o๐]+\s+', ' ', text)
        
        # D. Remove inline artifacts
        inline_patterns = [
            r'\[\d{1,2}:\d{2}\]', r'\(\d{1,2}:\d{2}\)', # Timestamps
            r'\([^)]*\)' # Stage directions in parentheses (laughing)
        ]
        for pattern in inline_patterns:
            text = re.sub(pattern, '', text)
        
        # 2. Normalize line breaks: Replace single newlines with spaces, keep double newlines (paragraphs)
        # This fixes PDF hard-wraps where a sentence is split across lines.
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        # 3. Thai Normalization: Combine Nikhahit + Sara Aa -> Sara Am
        text = text.replace('\u0E4D\u0E32', '\u0E33') 
        text = text.replace('\u0E32\u0E4D', '\u0E33')

        # 4. Collapse multiple spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()

    def _is_valid_sentence(self, sentence: str) -> bool:
        """
        Heuristic check: Return False if sentence is junk/noise.
        """
        s = sentence.strip()
        if len(s) < 15:
            return False
            
        # Conjunctions that indicate a fragment, not a main point
        bad_starters = ('และ', 'แต่', 'ซึ่ง', 'ยิ่งไปกว่านั้น', 'นอกจากนี้', 'เพราะ', 'โดย', 'ที่')
        if s.startswith(bad_starters):
            # However, if it's very long, it might be a valid complex sentence.
            # But usually for summary, we want standalone sentences.
            # Let's be strict for < 40 chars, lenient for long ones.
            if len(s) < 40:
                return False
                
        return True

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
        plus newlines and punctuation. Includes logic to repair broken sentences.
        """
        if not text:
            return []
            
        # 1. Split by newlines first (Paragraphs often imply sentence breaks)
        lines = text.splitlines()
        
        raw_sentences = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 2. Split by standard punctuation if present
            # 3. For Thai, only split if there are TWO or more spaces (paragraph breaks)
            chunks = re.split(r'(?:[!?.]+| {2,})', line)
            
            # Fallback: If chunks are huge and few (likely single-spaced PDF), try splitting by single space
            if len(chunks) <= 1 and len(line) > 300:
                 chunks = re.split(r'(?:[!?.]+| )', line)

            for chunk in chunks:
                if chunk.strip():
                    raw_sentences.append(chunk.strip())
        
        # 4. Repair broken sentences (e.g. ending with conjunctions/prefixes) & Merge short fragments
        final_sentences = []
        # Added 'ความ', 'การ', 'ของ', 'ใน' to prevent cutting off at common prefixes/prepositions
        bad_endings = ('แต่', 'และ', 'หรือ', 'ก็', 'คือ', 'ว่า', 'ซึ่ง', 'ที่', 'เพื่อ', 'โดย', 'กับ', 'ความ', 'การ', 'ของ', 'ใน', 'ไม่')
        
        buffer = ""
        # Heuristic: Minimum length for a "complete" Thai sentence/thought -> Increased to 60 to force longer phrases
        MIN_SENTENCE_LENGTH = 60 
        
        for s in raw_sentences:
            s = s.strip()
            if not s: continue
            
            # If buffer exists, we are in merging mode
            if buffer:
                buffer += " " + s
                # Keep merging if it ends with bad word OR is still too short
                if buffer.endswith(bad_endings) or len(buffer) < MIN_SENTENCE_LENGTH:
                    continue
                else:
                    if self._is_valid_sentence(buffer):
                         final_sentences.append(buffer)
                    buffer = ""
            else:
                # New sentence candidate
                if s.endswith(bad_endings) or len(s) < MIN_SENTENCE_LENGTH:
                    buffer = s
                else:
                    if self._is_valid_sentence(s):
                         final_sentences.append(s)
        
        # Flush buffer
        if buffer and self._is_valid_sentence(buffer):
             final_sentences.append(buffer)

        # Final filtering of very short noise that might have survived
        return [s for s in final_sentences if self._is_valid_sentence(s)]