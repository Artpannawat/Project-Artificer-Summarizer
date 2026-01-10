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
        Designed for Thai/English mixed text without heavy NLP libraries.
        """
        if not text:
            return []
            
        # Split by common ending punctuation
        # Thai often uses space as a sentence delimiter, so we treat large spaces or standard punctuation as splitters.
        
        # 1. Split by standard punctuation (.!?) followed by space
        chunks = re.split(r'(?<=[.!?])\s+', text)
        
        final_sentences = []
        for chunk in chunks:
            # 2. For Thai, sometimes long sentences are just separated by spaces.
            # We enforce a split if a segment is very long (>200 chars) and has spaces.
            if len(chunk) > 200:
                # Attempt to split by spaces if they look like phrase breaks
                # (This is a heuristic and not perfect, but better than massive blocks)
                sub_parts = chunk.split(' ')
                current_sent = ""
                for part in sub_parts:
                    if len(current_sent) + len(part) < 150:
                        current_sent += part + " "
                    else:
                        final_sentences.append(current_sent.strip())
                        current_sent = part + " "
                if current_sent:
                    final_sentences.append(current_sent.strip())
            else:
                final_sentences.append(chunk.strip())
                
        return [s for s in final_sentences if s]