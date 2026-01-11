import re

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
            
            # Filter weak sentences (too short)
            valid_sentences = [s for s in sentences if len(s) >= min_length]
            
            if not valid_sentences:
                return text[:500] + "..." if len(text) > 500 else text

            if len(valid_sentences) <= num_sentences:
                return " ".join(valid_sentences)

            # 2. TextRank Algorithm Implementation
            try:
                import networkx as nx
                import math

                # Build Graph
                graph = nx.Graph()
                
                # Tokenize all sentences once
                sentence_tokens = [set(processor.tokenize_words(s)) for s in valid_sentences]
                
                # Add nodes
                for i in range(len(valid_sentences)):
                    graph.add_node(i)
                
                # Calculate Similarity (Jaccard Index)
                for i in range(len(valid_sentences)):
                    for j in range(i + 1, len(valid_sentences)):
                        words1 = sentence_tokens[i]
                        words2 = sentence_tokens[j]
                        
                        # Jaccard Similarity
                        intersection = len(words1.intersection(words2))
                        union = len(words1.union(words2))
                        
                        if union > 0:
                            similarity = intersection / union
                            if similarity > 0:
                                graph.add_edge(i, j, weight=similarity)

                # Run PageRank
                scores = nx.pagerank(graph, weight='weight')
                
                # Sort by score
                ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(valid_sentences)), reverse=True)
                
                # Select top N
                top_sentences = [s for score, s in ranked_sentences[:num_sentences]]
                
                # Reorder by appearance in original text
                # We need to map back to original indices
                final_summary = []
                for sentence in valid_sentences:
                    if sentence in top_sentences:
                        final_summary.append(sentence)
                        if len(final_summary) >= num_sentences:
                            break
                            
                return " ".join(final_summary)

            except ImportError:
                print("WARNING: NetworkX not found. Falling back to simple frequency.")
                # Fallback logic could go here, or just return start
                return " ".join(valid_sentences[:num_sentences])

        except Exception as e:
            print(f"Basic Summarizer Error: {e}")
            import traceback
            traceback.print_exc()
            return text[:500] + "..."