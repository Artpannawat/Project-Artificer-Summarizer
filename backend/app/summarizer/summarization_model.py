from pythainlp import sent_tokenize, word_tokenize
from pythainlp.util import normalize
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re

class SummarizationModel:
    def _contains_thai(self, text: str) -> bool:
        return re.search(r"[\u0E00-\u0E7F]", text) is not None

    def _split_english_sentences(self, text: str) -> list[str]:
        parts = re.split(r"(?<=[.!?])\s+|\n+", text)
        return [p.strip() for p in parts if p and p.strip()]

    def _preprocess_thai_text(self, text: str) -> str:
        """Preprocess Thai text for better tokenization"""
        # Normalize Thai text
        text = normalize(text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def summarize(self, text: str, num_sentences: int = 5) -> str:
        if not text:
            return ""

        num_sentences = max(1, int(num_sentences or 5))

        if self._contains_thai(text):
            # Preprocess Thai text
            text = self._preprocess_thai_text(text)
            sentences = sent_tokenize(text)
            if len(sentences) <= num_sentences:
                return text.strip()
            
            # Use newmm engine for better Thai word tokenization
            corpus = []
            for s in sentences:
                try:
                    words = word_tokenize(s, engine="newmm")
                    corpus.append(" ".join(words))
                except Exception:
                    # Fallback to simple space splitting if tokenization fails
                    corpus.append(s)
            
            vectorizer = TfidfVectorizer(use_idf=True, smooth_idf=True, min_df=1)
        else:
            sentences = self._split_english_sentences(text)
            if len(sentences) <= num_sentences:
                return text.strip()
            corpus = sentences
            vectorizer = TfidfVectorizer(use_idf=True, smooth_idf=True, stop_words="english")

        try:
            matrix = vectorizer.fit_transform(corpus)
            sentence_scores = np.asarray(matrix.sum(axis=1)).ravel()
            top_sentence_indices = np.argsort(sentence_scores)[-num_sentences:][::-1]
            sorted_indices = sorted(top_sentence_indices)
            summary_sentences = [sentences[i] for i in sorted_indices]
            return " ".join(summary_sentences)
        except Exception as e:
            # Fallback: return first few sentences if vectorization fails
            return " ".join(sentences[:num_sentences])