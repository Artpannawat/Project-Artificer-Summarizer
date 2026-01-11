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
                words = [w.lower() for w in sent.split() if w.lower() not in stopwords]
                sentence_words.append(words)

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
                union = len(set1) + len(set2) - intersection # Simple union count
                # Avoid log(0) complexity, just simple ratio
                return intersection / (math.log(len(set1) + len(set2)) + 1.0) # Softened Jaccard

            # Run Power Method Iterations
            for _ in range(iterations):
                new_scores = [0.0] * n
                for i in range(n):
                    sum_similarity = 0.0
                    for j in range(n):
                        if i == j: continue
                        
                        sim = jaccard_similarity(sentence_words[i], sentence_words[j])
                        
                        # Add contribution from neighbor j
                        # In standard TextRank, we normalized by the sum of weights of j's neighbors.
                        # Here, for "Basic" speed, we use a simplified unweighted summation logic or just raw similarity.
                        # Let's use weighted sum.
                        
                        sum_similarity += sim * scores[j]
                    
                    new_scores[i] = (1 - damping) + damping * sum_similarity
                scores = new_scores

            # 4. Select Top Sentences
            # Create pairs of (index, score)
            ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:num_sentences]
            
            # 5. Reorder by original appearance (Coherence)
            ranked_indices.sort()
            
            summary = [valid_sentences[i] for i in ranked_indices]
            
            joined_summary = " ".join(summary)
            
            # If summary is too short, fallback to first few sentences
            if len(joined_summary) < 100:
                 return " ".join(valid_sentences[:num_sentences])
                 
            return joined_summary

        except Exception as e:
            print(f"Basic Summarizer Error: {e}")
            # Fallback
            return text[:500] + "..."