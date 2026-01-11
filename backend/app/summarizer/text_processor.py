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

    def tokenize_words(self, text: str) -> list[str]:
        """
        Tokenizer for TextRank.
        Uses Character Trigrams (3-grams) for Thai text to avoid heavy libraries (PyThaiNLP).
        This works well for similarity/overlap calculations without needing a dictionary.
        """
        if not text:
            return []
            
        # 1. Remove spaces to treat as continuous flow (for Thai)
        text_no_space = text.replace(" ", "")
        
        # 2. Generate Character Trigrams
        # e.g. "สวัสดี" -> ["สวั", "วัส", "ัสด", "สดี"]
        n = 3
        if len(text_no_space) < n:
            return [text_no_space]
            
        trigrams = [text_no_space[i:i+n] for i in range(len(text_no_space) - n + 1)]
        return trigrams

    def segment_sentences(self, text: str) -> list[str]:
        """
        Segment text into partial sentences/phrases using intelligent heuristics.
        Does not require heavy NLP libraries.
        """
        if not text:
            return []
            
        # 1. Clean and normalize
        text = text.strip()
        
        # 2. Split by standard punctuation for English parts
        # Split by: .!? followed by space, or double newline
        chunks = re.split(r'(?:(?<=[.!?])\s+|\n\s*\n)', text)
        
        final_sentences = []
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk: continue
            
            # 3. Handling Thai long strings
            # If a chunk is very long (>150 chars) and contains spaces, it might be multiple Thai sentences
            if len(chunk) > 150:
                # Heuristic: Split by spaces that are "likely" sentence breaks
                # (e.g. not between numbers, not inside English phrases)
                # For simplicity, we split by 2+ spaces or large distinct gaps
                sub_parts = re.split(r'\s{2,}', chunk) 
                
                # If still too massive, try generating a split on single spaces but grouping them
                if len(sub_parts) == 1:
                    words = chunk.split(' ')
                    current = ""
                    for word in words:
                        if len(current) + len(word) < 120:
                            current += word + " "
                        else:
                            final_sentences.append(current.strip())
                            current = word + " "
                    if current:
                        final_sentences.append(current.strip())
                else:
                    final_sentences.extend([s.strip() for s in sub_parts if s.strip()])
            else:
                final_sentences.append(chunk)
                
        return [s for s in final_sentences if len(s) > 1]