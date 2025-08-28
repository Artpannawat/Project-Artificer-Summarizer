"""
AI-Enhanced Summarizer using pre-trained models
"""
import os
import re
from typing import Optional
import logging

# Try to import AI libraries
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    import openai
    HAS_OPENAI = bool(os.getenv('OPENAI_API_KEY'))
except ImportError:
    HAS_OPENAI = False

logger = logging.getLogger(__name__)

class AISummarizer:
    """AI-powered summarizer with fallback to traditional methods"""
    
    def __init__(self):
        self.models_loaded = False
        self.en_summarizer = None
        self.th_summarizer = None
        self.openai_client = None
        
        # Try to load models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize AI models if available"""
        try:
            if HAS_TRANSFORMERS:
                # English summarizer
                try:
                    self.en_summarizer = pipeline(
                        "summarization",
                        model="facebook/bart-large-cnn",
                        device=0 if torch.cuda.is_available() else -1,
                        framework="pt"
                    )
                    logger.info("Loaded English BART summarizer")
                except Exception as e:
                    logger.warning(f"Failed to load English summarizer: {e}")
                
                # Multilingual summarizer (works for Thai)
                try:
                    self.th_summarizer = pipeline(
                        "summarization",
                        model="google/mt5-small",
                        device=0 if torch.cuda.is_available() else -1,
                        framework="pt"
                    )
                    logger.info("Loaded multilingual mT5 summarizer")
                except Exception as e:
                    logger.warning(f"Failed to load Thai summarizer: {e}")
            
            if HAS_OPENAI:
                openai.api_key = os.getenv('OPENAI_API_KEY')
                self.openai_client = openai
                logger.info("OpenAI client initialized")
            
            self.models_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            self.models_loaded = False
    
    def _is_thai(self, text: str) -> bool:
        """Check if text contains Thai characters"""
        return bool(re.search(r'[\u0E00-\u0E7F]', text))
    
    def _chunk_text(self, text: str, max_length: int = 1000) -> list:
        """Split long text into chunks for processing"""
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def summarize_with_transformers(self, text: str, max_length: int = 150) -> Optional[str]:
        """Summarize using Hugging Face transformers"""
        if not HAS_TRANSFORMERS:
            return None
        
        try:
            is_thai = self._is_thai(text)
            summarizer = self.th_summarizer if is_thai else self.en_summarizer
            
            if not summarizer:
                return None
            
            # Handle long texts by chunking
            if len(text) > 1000:
                chunks = self._chunk_text(text, 900)
                summaries = []
                
                for chunk in chunks[:3]:  # Limit to 3 chunks to avoid timeout
                    try:
                        result = summarizer(
                            chunk,
                            max_length=max_length // len(chunks),
                            min_length=20,
                            do_sample=False
                        )
                        if result and len(result) > 0:
                            summaries.append(result[0]['summary_text'])
                    except Exception as e:
                        logger.warning(f"Failed to summarize chunk: {e}")
                        continue
                
                return " ".join(summaries) if summaries else None
            
            else:
                result = summarizer(
                    text,
                    max_length=max_length,
                    min_length=30,
                    do_sample=False
                )
                return result[0]['summary_text'] if result else None
                
        except Exception as e:
            logger.error(f"Transformers summarization failed: {e}")
            return None
    
    def summarize_with_openai(self, text: str, num_sentences: int = 3) -> Optional[str]:
        """Summarize using OpenAI API"""
        if not HAS_OPENAI or not self.openai_client:
            return None
        
        try:
            is_thai = self._is_thai(text)
            
            if is_thai:
                prompt = f"""
สรุปข้อความต่อไปนี้เป็นภาษาไทยใน {num_sentences} ประโยค:

{text[:3000]}  # Limit input length

ให้สรุปแบบกระชับ ครอบคลุมใจความสำคัญ และใช้ภาษาที่เข้าใจง่าย:
"""
            else:
                prompt = f"""
Summarize the following text in {num_sentences} sentences:

{text[:3000]}

Provide a concise summary that captures the main points:
"""
            
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI summarization failed: {e}")
            return None
    
    def summarize(self, text: str, num_sentences: int = 3, method: str = 'auto') -> Optional[str]:
        """
        Main summarization method with multiple AI approaches
        
        Args:
            text: Input text to summarize
            num_sentences: Target number of sentences
            method: 'auto', 'transformers', 'openai'
        """
        if not text or len(text.strip()) < 100:
            return text.strip()
        
        # Calculate max_length for transformers based on num_sentences
        max_length = min(num_sentences * 30, 200)
        
        # Try different methods based on preference
        if method == 'openai' or (method == 'auto' and HAS_OPENAI):
            result = self.summarize_with_openai(text, num_sentences)
            if result:
                return result
        
        if method == 'transformers' or (method == 'auto' and HAS_TRANSFORMERS):
            result = self.summarize_with_transformers(text, max_length)
            if result:
                return result
        
        # If all AI methods fail, return None (fallback to traditional)
        return None
    
    def is_available(self) -> bool:
        """Check if any AI summarization method is available"""
        return HAS_TRANSFORMERS or HAS_OPENAI
    
    def get_available_methods(self) -> list:
        """Get list of available AI methods"""
        methods = []
        if HAS_TRANSFORMERS:
            methods.append('transformers')
        if HAS_OPENAI:
            methods.append('openai')
        return methods