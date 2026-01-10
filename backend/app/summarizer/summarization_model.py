import re
import numpy as np

class SummarizationModel:
    def _contains_thai(self, text: str) -> bool:
        return re.search(r"[\u0E00-\u0E7F]", text) is not None

    def _split_english_sentences(self, text: str) -> list[str]:
        parts = re.split(r"(?<=[.!?])\s+|\n+", text)
        return [p.strip() for p in parts if p and p.strip()]

    def _preprocess_thai_text(self, text: str) -> str:
        """Preprocess Thai text for better tokenization"""
        from pythainlp.util import normalize
        # Normalize Thai text
        text = normalize(text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def summarize(self, text: str, num_sentences: int = 5, min_length: int = 20, max_length: int = 2000) -> str:
        # Lazy imports to prevent startup hang
        from pythainlp import sent_tokenize, word_tokenize
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import networkx as nx

        if not text:
            return ""

        num_sentences = max(1, int(num_sentences or 5))

        try:
            if self._contains_thai(text):
                # Preprocess Thai text
                text = self._preprocess_thai_text(text)
                sentences = sent_tokenize(text)
                
                # Filter sentences by length
                sentences = [s.strip() for s in sentences if min_length <= len(s) <= max_length]
                
                if not sentences:
                    return ""
                    
                if len(sentences) <= num_sentences:
                    return " ".join(sentences)
                
                # Use newmm engine for better Thai word tokenization
                corpus = []
                valid_sentences = []
                
                for s in sentences:
                    s = s.strip()
                    if not s:
                        continue
                    try:
                        words = word_tokenize(s, engine="newmm")
                        # Filter out stopwords or empty tokens
                        joined_words = " ".join([w for w in words if w.strip() and len(w.strip()) > 1])
                        if joined_words:
                            corpus.append(joined_words)
                            valid_sentences.append(s)
                    except Exception:
                        continue
                
                sentences = valid_sentences
                
                if len(sentences) <= num_sentences:
                    return " ".join(sentences)
                    
                if not corpus:
                     return " ".join(sentences[:num_sentences])

                vectorizer = TfidfVectorizer(use_idf=True, smooth_idf=True, min_df=1, norm='l2')
            else:
                raw_sentences = self._split_english_sentences(text)
                # Filter sentences by length
                sentences = [s.strip() for s in raw_sentences if min_length <= len(s) <= max_length]
                
                if len(sentences) <= num_sentences:
                    return " ".join(sentences)
                    
                corpus = sentences
                vectorizer = TfidfVectorizer(use_idf=True, smooth_idf=True, stop_words="english", norm='l2')

            # 1. Transform sentences to TF-IDF vectors
            tfidf_matrix = vectorizer.fit_transform(corpus)
            
            # 2. Compute Cosine Similarity Matrix
            similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
            
            # 3. Build Graph
            nx_graph = nx.from_numpy_array(similarity_matrix)
            
            # 4. Compute TextRank (PageRank) scores
            scores = nx.pagerank(nx_graph, max_iter=100, tol=1e-4)
            
            # 5. Rank sentences
            ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
            
            # 6. Select top N sentences
            top_sentences = ranked_sentences[:num_sentences]
            
            # 7. Sort by original appearance order to maintain flow
            # We need to find the original index of these top sentences
            final_sentences = []
            for _, sent in top_sentences:
                try:
                    idx = sentences.index(sent)
                    final_sentences.append((idx, sent))
                except ValueError:
                    continue
            
            final_sentences.sort(key=lambda x: x[0])
            
            return " ".join([s for _, s in final_sentences])
            
        except Exception as e:
            print(f"TextRank Error: {e}")
            # Fallback: return first few sentences if vectorization/graph fails
            if 'sentences' in locals() and sentences:
                 return " ".join(sentences[:num_sentences])
            return text[:1000] + "..." # basic fallback