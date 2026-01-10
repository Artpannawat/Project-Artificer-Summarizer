import re

class SummarizationModel:
    def summarize(self, text: str, num_sentences: int = 5, min_length: int = 20, max_length: int = 2000) -> str:
        if not text:
            return ""

        num_sentences = max(1, int(num_sentences or 5))

        try:
            # 1. Split into sentences (Basic Regex for Thai/English)
            # Split by newline first
            chunks = text.split('\n')
            sentences = []
            
            for chunk in chunks:
                # Split by punctuation (.!?)
                parts = re.split(r'(?<=[.!?])\s+', chunk)
                for p in parts:
                    clean_p = p.strip()
                    if clean_p and len(clean_p) >= min_length:
                        sentences.append(clean_p)
            
            if not sentences:
                return text[:500] + "..."

            if len(sentences) <= num_sentences:
                return " ".join(sentences)

            # 2. Simple Selection Heuristic (First + Last + Middle) for variety without ML
            # If we need 5 sentences:
            # - Always take the first (Introduction)
            # - Always take the last (Conclusion)
            # - Pick others evenly distributed
            
            selected = []
            if num_sentences == 1:
                return sentences[0]
            
            # Start
            selected.append(sentences[0])
            
            if num_sentences > 2:
                # Middle indices
                step = len(sentences) / num_sentences
                for i in range(1, num_sentences - 1):
                    idx = int(i * step)
                    if idx > 0 and idx < len(sentences) - 1:
                        selected.append(sentences[idx])
            
            # End
            if len(sentences) > 1:
                selected.append(sentences[-1])

            # Ensure unique and respect limit
            final_selection = []
            seen = set()
            for s in selected:
                if s not in seen:
                    final_selection.append(s)
                    seen.add(s)
            
            # Fill up if duplicate removal reduced count
            for s in sentences:
                if len(final_selection) >= num_sentences:
                    break
                if s not in seen:
                    final_selection.append(s)
                    seen.add(s)

            return " ".join(final_selection)

        except Exception as e:
            print(f"Basic Summarizer Error: {e}")
            return text[:1000] + "..."