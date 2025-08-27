import io
import os
from typing import Union
from fastapi import UploadFile, HTTPException

# Try to import optional dependencies
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import docx2txt
    HAS_DOCX2TXT = True
except ImportError:
    HAS_DOCX2TXT = False

try:
    from docx import Document
    HAS_PYTHON_DOCX = True
except ImportError:
    HAS_PYTHON_DOCX = False


class FileProcessor:
    """
    Class for processing various document formats (PDF, DOC, DOCX, TXT)
    and extracting text content for summarization.
    """
    
    SUPPORTED_FORMATS = {
        'application/pdf': 'pdf',
        'application/msword': 'doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'text/plain': 'txt'
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self):
        pass
    
    async def extract_text_from_file(self, file: UploadFile) -> str:
        """
        Extract text content from uploaded file based on its format.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            str: Extracted text content
            
        Raises:
            HTTPException: If file format is not supported or extraction fails
        """
        # Validate file size
        content = await file.read()
        if len(content) > self.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="ขนาดไฟล์เกิน 10MB")
        
        # Reset file pointer
        await file.seek(0)
        
        # Determine file format
        file_format = self._get_file_format(file)
        
        try:
            if file_format == 'pdf':
                text = await self._extract_from_pdf(content)
            elif file_format == 'docx':
                text = await self._extract_from_docx(content)
            elif file_format == 'doc':
                text = await self._extract_from_doc(content)
            elif file_format == 'txt':
                text = await self._extract_from_txt(content)
            else:
                raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์ PDF, DOC, DOCX, TXT เท่านั้น")
            
            if not text or len(text.strip()) < 10:
                raise HTTPException(status_code=400, detail="ไม่พบเนื้อหาในไฟล์ หรือเนื้อหาสั้นเกินไป")
            
            return text.strip()
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการประมวลผลไฟล์: {str(e)}")
    
    def _get_file_format(self, file: UploadFile) -> str:
        """
        Determine file format from content type or filename extension.
        """
        # Check content type first
        if file.content_type in self.SUPPORTED_FORMATS:
            return self.SUPPORTED_FORMATS[file.content_type]
        
        # Fallback to file extension
        if file.filename:
            filename_lower = file.filename.lower()
            if filename_lower.endswith('.pdf'):
                return 'pdf'
            elif filename_lower.endswith('.docx'):
                return 'docx'
            elif filename_lower.endswith('.doc'):
                return 'doc'
            elif filename_lower.endswith('.txt'):
                return 'txt'
        
        raise HTTPException(status_code=400, detail="ไม่สามารถระบุประเภทไฟล์ได้")
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and format extracted text from files"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common extraction issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Space between camelCase
        text = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', text)  # Space after punctuation
        text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)  # Space between letter and number
        text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)  # Space between number and letter
        
        # Remove page numbers and headers/footers patterns
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip likely page numbers
            if re.match(r'^\d+$', line):
                continue
            
            # Skip very short lines (likely headers/footers)
            if len(line) < 10:
                continue
            
            # Skip lines that are mostly numbers or symbols
            if len(re.sub(r'[^a-zA-Zก-๙]', '', line)) < len(line) * 0.5:
                continue
            
            cleaned_lines.append(line)
        
        # Join lines with proper spacing
        cleaned_text = ' '.join(cleaned_lines)
        
        # Final cleanup
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        return cleaned_text
    
    async def _extract_from_pdf(self, content: bytes) -> str:
        """Enhanced PDF text extraction with better formatting"""
        if not HAS_PYMUPDF and not HAS_PYPDF2:
            raise HTTPException(
                status_code=500, 
                detail="ไม่สามารถอ่านไฟล์ PDF ได้ เนื่องจากไม่มี PDF processing libraries"
            )
        
        try:
            text = ""
            
            # Try PyMuPDF first (better for complex PDFs)
            if HAS_PYMUPDF:
                try:
                    pdf_document = fitz.open(stream=content, filetype="pdf")
                    
                    for page_num in range(pdf_document.page_count):
                        page = pdf_document.load_page(page_num)
                        
                        # Get text with better formatting
                        page_text = page.get_text("text")
                        
                        # Clean up the extracted text
                        if page_text.strip():
                            # Fix common PDF extraction issues
                            page_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', page_text)  # Add space between words
                            page_text = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', page_text)  # Add space after punctuation
                            page_text = re.sub(r'\s+', ' ', page_text)  # Normalize whitespace
                            
                            text += page_text + "\n\n"
                    
                    pdf_document.close()
                    
                    if text.strip():
                        return self._clean_extracted_text(text)
                except Exception:
                    pass  # Try PyPDF2 as fallback
            
            # Fallback to PyPDF2
            if HAS_PYPDF2:
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                    
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text.strip():
                            # Clean up the extracted text
                            page_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', page_text)
                            page_text = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', page_text)
                            page_text = re.sub(r'\s+', ' ', page_text)
                            text += page_text + "\n\n"
                    
                    if text.strip():
                        return self._clean_extracted_text(text)
                except Exception:
                    pass
            
            # If both methods fail
            raise HTTPException(
                status_code=500, 
                detail="ไม่สามารถอ่านเนื้อหาจากไฟล์ PDF ได้ ไฟล์อาจเสียหายหรือมีการป้องกัน"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ไม่สามารถอ่านไฟล์ PDF ได้: {str(e)}")
    
    async def _extract_from_docx(self, content: bytes) -> str:
        """Enhanced DOCX text extraction with better formatting"""
        if not HAS_DOCX2TXT and not HAS_PYTHON_DOCX:
            raise HTTPException(
                status_code=500, 
                detail="ไม่สามารถอ่านไฟล์ DOCX ได้ เนื่องจากไม่มี DOCX processing libraries"
            )
        
        try:
            text = ""
            
            # Method 1: Using docx2txt (simpler and more reliable)
            if HAS_DOCX2TXT:
                try:
                    text = docx2txt.process(io.BytesIO(content))
                    if text.strip():
                        return self._clean_extracted_text(text)
                except Exception:
                    pass  # Try python-docx as fallback
            
            # Method 2: Using python-docx as fallback with better extraction
            if HAS_PYTHON_DOCX:
                try:
                    doc = Document(io.BytesIO(content))
                    paragraphs = []
                    
                    # Extract paragraphs with proper formatting
                    for paragraph in doc.paragraphs:
                        para_text = paragraph.text.strip()
                        if para_text and len(para_text) > 3:  # Skip very short paragraphs
                            # Check if it's a heading (usually shorter and may be important)
                            if len(para_text) < 100 and not para_text.endswith('.'):
                                para_text += '.'  # Add period for better sentence detection
                            paragraphs.append(para_text)
                    
                    # Extract text from tables with better structure
                    for table in doc.tables:
                        table_text = []
                        for row in table.rows:
                            row_text = []
                            for cell in row.cells:
                                cell_text = cell.text.strip()
                                if cell_text:
                                    row_text.append(cell_text)
                            if row_text:
                                table_text.append(' | '.join(row_text))
                        
                        if table_text:
                            # Add table as a structured paragraph
                            paragraphs.append('. '.join(table_text) + '.')
                    
                    # Join paragraphs with proper spacing
                    text = ' '.join(paragraphs)
                    if text.strip():
                        return self._clean_extracted_text(text)
                except Exception:
                    pass
            
            # If both methods fail
            raise HTTPException(
                status_code=500, 
                detail="ไม่สามารถอ่านเนื้อหาจากไฟล์ DOCX ได้ ไฟล์อาจเสียหายหรือไม่ถูกต้อง"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ไม่สามารถอ่านไฟล์ DOCX ได้: {str(e)}")
    
    async def _extract_from_doc(self, content: bytes) -> str:
        """Extract text from DOC file (legacy format)"""
        if not HAS_DOCX2TXT:
            raise HTTPException(
                status_code=400, 
                detail="ไม่สามารถอ่านไฟล์ .doc ได้ กรุณาแปลงเป็น .docx หรือ PDF"
            )
        
        try:
            # For .doc files, we'll try to use docx2txt which sometimes works
            # Note: .doc support is limited, recommend users to convert to .docx
            text = docx2txt.process(io.BytesIO(content))
            
            if not text.strip():
                raise HTTPException(
                    status_code=400, 
                    detail="ไม่สามารถอ่านไฟล์ .doc ได้ กรุณาแปลงเป็น .docx หรือ PDF"
                )
            
            return text
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"ไฟล์ .doc อาจเสียหาย กรุณาแปลงเป็น .docx หรือ PDF: {str(e)}"
            )
    
    async def _extract_from_txt(self, content: bytes) -> str:
        """Extract text from TXT file"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'cp874', 'iso-8859-1', 'windows-1252']
            
            for encoding in encodings:
                try:
                    text = content.decode(encoding)
                    return text
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, use utf-8 with error handling
            text = content.decode('utf-8', errors='replace')
            return text
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ไม่สามารถอ่านไฟล์ TXT ได้: {str(e)}")
    
    def validate_file(self, file: UploadFile) -> bool:
        """
        Validate uploaded file format and size.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            bool: True if file is valid
            
        Raises:
            HTTPException: If file is invalid
        """
        # Check if file exists
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="ไม่พบไฟล์")
        
        # Check file format
        try:
            self._get_file_format(file)
        except HTTPException:
            raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์ PDF, DOC, DOCX, TXT เท่านั้น")
        
        return True