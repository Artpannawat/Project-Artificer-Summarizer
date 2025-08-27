import re
from pythainlp.util import normalize

class TextProcessor:
    def clean_text(self, text: str) -> str:
        """Enhanced text cleaning with better preprocessing"""
        if not text:
            return ""
        
        # Step 1: Handle different types of content
        is_thai = re.search(r"[\u0E00-\u0E7F]", text) is not None
        
        # Step 2: Remove unwanted characters and formatting
        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', ' ', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', ' ', text)
        
        # Step 3: Language-specific processing
        if is_thai:
            # Normalize Thai text
            text = normalize(text)
            
            # Remove zero-width characters common in Thai text
            text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
            
            # Fix Thai punctuation issues
            text = re.sub(r'([.!?])\s*([.!?]+)', r'\1', text)  # Remove duplicate punctuation
            text = re.sub(r'([ก-๙])\s+([ก-๙])', r'\1\2', text)  # Fix unnecessary spaces in Thai
            
        else:
            # English text processing
            # Fix common OCR/PDF extraction issues
            text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
            text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)  # Add space after punctuation
            
        # Step 4: General cleaning
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix punctuation spacing
        text = re.sub(r'\s+([.!?,:;])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([.!?])\s*([.!?]+)', r'\1', text)  # Remove duplicate punctuation
        
        # Step 5: Handle paragraphs and line breaks
        # Convert multiple line breaks to paragraph separation
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Convert single line breaks to spaces (except for paragraph breaks)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        # Convert paragraph breaks back to proper sentence separation
        text = re.sub(r'\n\n+', '. ', text)
        
        # Step 6: Final cleanup
        cleaned_text = text.strip()
        
        # Ensure text ends with proper punctuation
        if cleaned_text and not cleaned_text.endswith(('.', '!', '?', '।')):
            cleaned_text += '.'
        
        return cleaned_text
    
    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> list:
        """Extract key phrases from text for better summarization context"""
        if not text:
            return []
        
        is_thai = re.search(r"[\u0E00-\u0E7F]", text) is not None
        phrases = []
        
        try:
            if is_thai:
                from pythainlp import word_tokenize
                # Extract noun phrases and important terms
                words = word_tokenize(text, engine="newmm")
                # Simple approach: look for sequences of nouns/important words
                current_phrase = []
                for word in words:
                    if len(word) > 1 and not re.match(r'^[^\u0E00-\u0E7F]+$', word):
                        current_phrase.append(word)
                    else:
                        if len(current_phrase) >= 2:
                            phrases.append(''.join(current_phrase))
                        current_phrase = []
                        
            else:
                # English key phrase extraction
                # Look for capitalized sequences (potential proper nouns)
                capitalized_sequences = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
                phrases.extend(capitalized_sequences)
                
                # Look for technical terms or important phrases
                technical_terms = re.findall(r'\b[a-zA-Z]{3,}\b', text)
                word_freq = {}
                for term in technical_terms:
                    term_lower = term.lower()
                    word_freq[term_lower] = word_freq.get(term_lower, 0) + 1
                
                # Get most frequent terms
                frequent_terms = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
                phrases.extend([term for term, freq in frequent_terms if freq > 1])
            
            # Return top phrases
            return phrases[:max_phrases]
            
        except Exception:
            return []