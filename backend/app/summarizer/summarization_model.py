from pythainlp import sent_tokenize, word_tokenize
from pythainlp.util import normalize
from pythainlp.corpus import thai_stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from collections import Counter
import math

class SummarizationModel:
    def __init__(self):
        """Initialize the summarization model with Thai stopwords"""
        try:
            self.thai_stopwords = set(thai_stopwords())
        except:
            # Fallback Thai stopwords if corpus loading fails
            self.thai_stopwords = {
                'และ', 'หรือ', 'แต่', 'เพราะ', 'เนื่องจาก', 'ดังนั้น', 'อย่างไรก็ตาม',
                'ที่', 'ซึ่ง', 'อัน', 'ได้', 'ให้', 'มา', 'ไป', 'จะ', 'ถูก', 'คือ', 'เป็น',
                'มี', 'อยู่', 'นั้น', 'นี้', 'เหล่านั้น', 'เหล่านี้', 'ใน', 'บน', 'ที่',
                'จาก', 'ไปยัง', 'เพื่อ', 'สำหรับ', 'กับ', 'โดย', 'แล้ว', 'แต่ง', 'ก็',
                'ขึ้น', 'ลง', 'เข้า', 'ออก', 'มาก', 'น้อย', 'ดี', 'เก่า', 'ใหม่'
            }
    
    def _contains_thai(self, text: str) -> bool:
        return re.search(r"[\u0E00-\u0E7F]", text) is not None

    def _split_english_sentences(self, text: str) -> list[str]:
        """Enhanced English sentence splitting"""
        # Handle common abbreviations
        text = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Sr|Jr)\.\s*', r'\1<DOT> ', text)
        
        # Split on sentence endings
        parts = re.split(r'(?<=[.!?])\s+|\n{2,}', text)
        
        # Restore dots in abbreviations
        sentences = []
        for part in parts:
            if part and part.strip():
                cleaned = part.replace('<DOT>', '.').strip()
                if len(cleaned) > 10:  # Filter out very short sentences
                    sentences.append(cleaned)
        
        return sentences

    def _preprocess_thai_text(self, text: str) -> str:
        """Enhanced Thai text preprocessing"""
        # Normalize Thai text
        text = normalize(text)
        
        # Fix common issues with Thai text
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)  # Remove zero-width characters
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'([.!?])\s*([.!?]+)', r'\1', text)  # Remove duplicate punctuation
        
        return text.strip()

    def _calculate_sentence_importance(self, sentences: list, word_freq: dict, is_thai: bool = False) -> list:
        """Calculate importance scores for sentences using multiple factors"""
        scores = []
        
        for i, sentence in enumerate(sentences):
            score = 0
            words = []
            
            if is_thai:
                try:
                    words = word_tokenize(sentence, engine="newmm")
                    # Filter out stopwords and short words
                    words = [w for w in words if w not in self.thai_stopwords and len(w) > 1]
                except:
                    words = sentence.split()
            else:
                # English processing
                words = re.findall(r'\b[a-zA-Z]{2,}\b', sentence.lower())
                # Remove common English stopwords
                english_stopwords = {
                    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                    'of', 'with', 'by', 'this', 'that', 'these', 'those', 'is', 'are', 
                    'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
                    'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'
                }
                words = [w for w in words if w not in english_stopwords]
            
            if not words:
                scores.append(0)
                continue
            
            # 1. TF-IDF based scoring
            tf_score = sum(word_freq.get(word, 0) for word in words) / len(words)
            
            # 2. Position scoring (earlier sentences are more important)
            position_score = 1.0 / (1 + i * 0.1)
            
            # 3. Length scoring (prefer medium-length sentences)
            length_score = min(len(words) / 20.0, 1.0) if len(words) < 40 else 0.8
            
            # 4. Keyword density
            unique_words = len(set(words))
            diversity_score = unique_words / len(words) if words else 0
            
            # 5. Numerical content (sentences with numbers might be important)
            number_score = 0.1 if re.search(r'\d+', sentence) else 0
            
            # 6. Question or exclamation bonus
            punctuation_score = 0.05 if re.search(r'[!?]', sentence) else 0
            
            # Combine all scores
            final_score = (tf_score * 0.4 + 
                          position_score * 0.2 + 
                          length_score * 0.2 + 
                          diversity_score * 0.1 + 
                          number_score + 
                          punctuation_score)
            
            scores.append(final_score)
        
        return scores

    def _remove_redundant_sentences(self, sentences: list, scores: list, similarity_threshold: float = 0.7) -> tuple:
        """Remove redundant sentences based on similarity"""
        if len(sentences) <= 1:
            return sentences, scores
        
        # Create TF-IDF vectors for similarity comparison
        try:
            vectorizer = TfidfVectorizer(lowercase=True, stop_words=None, min_df=1)
            tfidf_matrix = vectorizer.fit_transform(sentences)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Mark sentences for removal
            to_remove = set()
            for i in range(len(sentences)):
                if i in to_remove:
                    continue
                for j in range(i + 1, len(sentences)):
                    if j in to_remove:
                        continue
                    if similarity_matrix[i][j] > similarity_threshold:
                        # Remove the sentence with lower score
                        if scores[i] >= scores[j]:
                            to_remove.add(j)
                        else:
                            to_remove.add(i)
                            break
            
            # Filter out redundant sentences
            filtered_sentences = []
            filtered_scores = []
            for i, (sentence, score) in enumerate(zip(sentences, scores)):
                if i not in to_remove:
                    filtered_sentences.append(sentence)
                    filtered_scores.append(score)
            
            return filtered_sentences, filtered_scores
            
        except Exception:
            # Fallback: return original if similarity calculation fails
            return sentences, scores

    def summarize(self, text: str, num_sentences: int = 5) -> str:
        """Enhanced summarization using multiple techniques"""
        if not text or len(text.strip()) < 50:
            return text.strip()

        num_sentences = max(1, min(int(num_sentences or 5), 10))  # Limit to max 10 sentences
        is_thai = self._contains_thai(text)

        try:
            # Step 1: Preprocess and split into sentences
            if is_thai:
                text = self._preprocess_thai_text(text)
                sentences = sent_tokenize(text)
            else:
                sentences = self._split_english_sentences(text)

            # Filter out very short sentences
            sentences = [s for s in sentences if len(s.strip()) > 15]
            
            if len(sentences) <= num_sentences:
                return " ".join(sentences)

            # Step 2: Calculate word frequencies for TF-IDF
            all_words = []
            for sentence in sentences:
                if is_thai:
                    try:
                        words = word_tokenize(sentence, engine="newmm")
                        words = [w for w in words if w not in self.thai_stopwords and len(w) > 1]
                    except:
                        words = sentence.split()
                else:
                    words = re.findall(r'\b[a-zA-Z]{2,}\b', sentence.lower())
                    english_stopwords = {
                        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                        'of', 'with', 'by', 'this', 'that', 'these', 'those', 'is', 'are', 
                        'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did'
                    }
                    words = [w for w in words if w not in english_stopwords]
                all_words.extend(words)

            # Calculate word frequencies
            word_freq = Counter(all_words)
            total_words = len(all_words)
            
            # Convert to normalized frequencies
            word_freq = {word: count / total_words for word, count in word_freq.items()}

            # Step 3: Calculate sentence importance scores
            scores = self._calculate_sentence_importance(sentences, word_freq, is_thai)

            # Step 4: Remove redundant sentences
            sentences, scores = self._remove_redundant_sentences(sentences, scores)

            # Step 5: Select top sentences
            if len(sentences) <= num_sentences:
                selected_sentences = sentences
            else:
                # Get indices of top-scored sentences
                top_indices = np.argsort(scores)[-num_sentences:]
                # Sort by original order to maintain text flow
                top_indices = sorted(top_indices)
                selected_sentences = [sentences[i] for i in top_indices]

            # Step 6: Post-process the summary
            summary = " ".join(selected_sentences)
            
            # Clean up the summary
            summary = re.sub(r'\s+', ' ', summary).strip()
            
            # Ensure proper sentence ending
            if summary and not summary.endswith(('.', '!', '?', '।')):
                summary += '.'

            return summary

        except Exception as e:
            # Enhanced fallback strategy
            try:
                # Try simple TF-IDF approach as fallback
                if is_thai:
                    corpus = []
                    for s in sentences:
                        try:
                            words = word_tokenize(s, engine="newmm")
                            corpus.append(" ".join(words))
                        except:
                            corpus.append(s)
                    vectorizer = TfidfVectorizer(use_idf=True, smooth_idf=True, min_df=1)
                else:
                    corpus = sentences
                    vectorizer = TfidfVectorizer(use_idf=True, smooth_idf=True, stop_words="english")

                matrix = vectorizer.fit_transform(corpus)
                sentence_scores = np.asarray(matrix.sum(axis=1)).ravel()
                top_sentence_indices = np.argsort(sentence_scores)[-num_sentences:][::-1]
                sorted_indices = sorted(top_sentence_indices)
                return " ".join([sentences[i] for i in sorted_indices])
                
            except:
                # Ultimate fallback: return first few sentences
                return " ".join(sentences[:num_sentences])