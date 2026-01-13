import re
import math
from collections import Counter

class SummarizationModel:
    def summarize(self, text: str, num_sentences: int = 5, min_length: int = 20, max_length: int = 2000) -> str:
        if not text:
            return ""

        num_sentences = max(1, int(num_sentences or 5))

        try:
            # 1. Preprocessing & Segmentation
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

            # 2. TextRank Implementation (Graph-Based)
            
            # Extended Stopwords for Thai/English
            stopwords = set([
                "the", "is", "in", "at", "of", "on", "and", "a", "an", "to", "for", "with", "user", "defined", "this", "that", "it",
                "การ", "ความ", "ที่", "ซึ่ง", "อัน", "ของ", "และ", "หรือ", "ใน", "โดย", "เป็น", "ไป", "มา", "จะ", "ให้", "ได้", "แต่",
                "จาก", "ว่า", "เพื่อ", "กับ", "แก่", "แห่ง", "นั้น", "นี้", "กัน", "แล้ว", "จึง", "อยู่", "ถูก", "เอา"
            ])

            # Pre-compute word sets for each sentence (Jaccard Similarity needs sets)
            sentence_words = []
            for sent in valid_sentences:
                # USE CUSTOM TOKENIZER instead of .split()
                # This allows identifying Thai words even without spaces
                words = processor.tokenize(sent)
                
                # Retrieve clean words (remove punctuation/single-char junk if needed)
                clean_words = [w.lower() for w in words if w.lower() not in stopwords and len(w.strip()) > 0]
                sentence_words.append(clean_words)

            # Build Similarity Matrix
            n = len(valid_sentences)
            scores = [1.0] * n  # Initial PageRank scores
            damping = 0.85
            iterations = 10
            
            # Similar to PageRank: score(i) = (1-d) + d * sum(score(j) * weight(j,i) / sum_weight(j))
            # Simplified TextRank: score(i) = (1-d) + d * sum(similarity(i,j) * score(j))
            # We use Jaccard Similarity for simplicity and speed.
            
            def jaccard_similarity(words1, words2):
                set1 = set(words1)
                set2 = set(words2)
                if not set1 or not set2:
                    return 0.0
                intersection = len(set1.intersection(set2))
                # Soft Jaccard to avoid pure 0 if small intersection but high relevance
                union = len(set1) + len(set2) - intersection 
                if union == 0: return 0.0
                return intersection / union

            # Run Power Method Iterations
            for _ in range(iterations):
                new_scores = [0.0] * n
                for i in range(n):
                    sum_similarity = 0.0
                    for j in range(n):
                        if i == j: continue
                        
                        sim = jaccard_similarity(sentence_words[i], sentence_words[j])
                        
                        # Add contribution from neighbor j
                        sum_similarity += sim * scores[j]
                    
                    new_scores[i] = (1 - damping) + damping * sum_similarity
                scores = new_scores

            # 4. Select Top Sentences
            # Create pairs of (index, score)
            ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:num_sentences]
            
            # 5. Reorder by original appearance (Coherence)
            ranked_indices.sort()
            
            summary = [valid_sentences[i] for i in ranked_indices]
            
            # Format as bullet points
            formatted_summary = "\n".join([f"- {sentence}" for sentence in summary])
            
            # If summary is too short, fallback to first few sentences
            if len(formatted_summary) < 50: # Check length of formatted string
                 return "\n".join([f"- {s}" for s in valid_sentences[:num_sentences]])
                 
            return formatted_summary

        except Exception as e:
            print(f"Basic Summarizer Error: {e}")
            # Fallback
            return text[:500] + "..."