import re

    def summarize(self, text: str, num_sentences: int = 5, min_length: int = 20, max_length: int = 2000) -> str:
        if not text:
            return ""

        num_sentences = max(1, int(num_sentences or 5))

        try:
            # 1. Preprocessing & Segmentation
            # We manually import TextProcessor here to avoid circular imports if any, 
            # but ideally it should be Dependency Injected. For now, we use local logic or helper.
            from backend.app.summarizer.text_processor import TextProcessor
            processor = TextProcessor()
            
            clean_text = processor.clean_text(text)
            sentences = processor.segment_sentences(clean_text)
            
            # Filter weak sentences
            valid_sentences = [s for s in sentences if len(s) >= min_length]
            
            if not valid_sentences:
                return text[:500] + "..." if len(text) > 500 else text

            if len(valid_sentences) <= num_sentences:
                return " ".join(valid_sentences)

            # 2. Build Frequency Map (Term Frequency)
            word_frequencies = {}
            stopwords = set(["the", "is", "in", "at", "of", "on", "and", "a", "an", "to", "for", "with", "user", "defined", "การ", "ความ", "ที่", "ซึ่ง", "อัน", "ของ", "และ", "หรือ", "ใน", "โดย", "เป็น", "ไป", "มา", "จะ", "ให้", "ได้"])
            
            for sentence in valid_sentences:
                # Simple tokenize by space
                words = sentence.split()
                for word in words:
                    w_lower = word.lower()
                    if w_lower not in stopwords and len(w_lower) > 1:
                        word_frequencies[w_lower] = word_frequencies.get(w_lower, 0) + 1

            # Normalize frequencies
            max_freq = max(word_frequencies.values()) if word_frequencies else 1
            for word in word_frequencies:
                word_frequencies[word] = word_frequencies[word] / max_freq

            # 3. Score Sentences
            sentence_scores = {}
            for i, sentence in enumerate(valid_sentences):
                score = 0
                words = sentence.split()
                for word in words:
                    w_lower = word.lower()
                    if w_lower in word_frequencies:
                        score += word_frequencies[w_lower]
                
                # Normalize by sentence length to avoid bias towards long sentences
                # But give slight penalty to very short ones
                if len(words) > 0:
                     sentence_scores[i] = score / (len(words) ** 0.5) # Soft normalization

            # 4. Select Top Sentences (Sorting by Score)
            top_sentences_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
            
            # 5. Reorder by original appearance (Coherence)
            top_sentences_indices.sort()
            
            summary = [valid_sentences[i] for i in top_sentences_indices]
            
            return " ".join(summary)

        except Exception as e:
            print(f"Basic Summarizer Error: {e}")
            # Fallback
            return text[:500] + "..."