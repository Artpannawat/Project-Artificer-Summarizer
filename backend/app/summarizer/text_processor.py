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