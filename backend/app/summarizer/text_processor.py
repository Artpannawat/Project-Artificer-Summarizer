import re
from .constants import THAI_DICT

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

    
    
    def __init__(self):
        # Expanded Dictionary for "Basic" Tokenization (Lite version of PyThaiNLP)
        # Includes common Function Words, Nouns, Verbs, Adjectives to cover ~80% of general text
        self.thai_dict = THAI_DICT
        
        # Sort to handle sub-word issues (optional optimization but set lookup is O(1))
        # Finding max length for optimization
        self.max_word_len = max([len(w) for w in self.thai_dict]) + 5 # Dynamic max len
        
        # Regex for checking Thai characters range
        self.thai_char_pattern = re.compile(r'[\u0E00-\u0E7F]')

    def tokenize(self, text: str) -> list[str]:
        """
        Tokenize text into words using Maximum Matching with an Expanded Dictionary.
        Includes logic to group unknown characters to reduce fragmentation.
        """
        if not text:
            return []

        # 1. Pre-split by spaces/newlines first
        chunks = text.split()
        tokens = []

        for chunk in chunks:
            # If chunk is English/Numbers (mostly), just keep it
            if not self.thai_char_pattern.search(chunk):
                tokens.append(chunk)
                continue
                
            # Thai MaxMatch Logic with Unknown Grouping
            i = 0
            length = len(chunk)
            
            while i < length:
                found = False
                
                # A. Try to find longest matching word
                for j in range(min(length, i + self.max_word_len), i, -1):
                    word = chunk[i:j]
                    if word in self.thai_dict:
                        tokens.append(word)
                        i = j
                        found = True
                        break
                
                if found:
                    continue
                    
                # B. If not found, it's an "Unknown"
                # Instead of taking just 1 char, try to consume until we hit a "Known Start" or end
                # But simple version: Just take 1 char if it's Thai vowel/tone mark to attach to previous?
                # No, safer is to group consecutive unknowns.
                
                unknown_buf = chunk[i]
                current_idx = i + 1
                
                while current_idx < length:
                    # Check if the substring starting at current_idx matches any word in dict
                    # This is lookahead "is this a start of a known word?"
                    is_known_start = False
                    
                    # Quick check: scan ahead for max_word_len
                    for k in range(min(length, current_idx + self.max_word_len), current_idx, -1):
                        if chunk[current_idx:k] in self.thai_dict:
                            is_known_start = True
                            break
                    
                    if is_known_start:
                        break
                        
                    # Also stop if we hit English/Numbers inside Thai string
                    if not self.thai_char_pattern.match(chunk[current_idx]):
                        break
                        
                    unknown_buf += chunk[current_idx]
                    current_idx += 1
                
                tokens.append(unknown_buf)
                i = current_idx
        
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
            # If a chunk is very long (>150 chars), try to find logical break points
            # Thai typically uses space for sentence boundaries, but also for emphasis.
            # We look for spaces that are likely sentence boundaries.
            
            if len(chunk) > 150:
                # Heuristic: Split by spaces that follow key conjunctions or standard gaps
                # This Regex looks for a space followed by typical Thai starting words or just large gaps
                # But to be safe for "Basic" engine, we just split by "  " (double space) if exists,
                # or single space if it's really long.
                
                # Split by any space, then regroup
                words = chunk.split(' ')
                current_sent = []
                current_len = 0
                
                for word in words:
                    conjunctions = ['ดังนั้น', 'เพราะ', 'แต่', 'อย่างไรก็ตาม', 'นอกจากนี้', 'ทั้งนี้', 'โดย', 'เพื่อ']
                    
                    # If current sentence is long enough AND (we hit a conjunction OR just getting too long)
                    if current_len > 80 and (word in conjunctions or current_len > 200):
                        final_sentences.append(" ".join(current_sent))
                        current_sent = [word]
                        current_len = len(word)
                    else:
                        current_sent.append(word)
                        current_len += len(word) + 1
                
                if current_sent:
                    final_sentences.append(" ".join(current_sent))
            else:
                final_sentences.append(chunk.strip())
                
        return [s.strip() for s in final_sentences if s.strip()]