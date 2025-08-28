import io
import os
from typing import Union
from fastapi import UploadFile, HTTPException


class SimpleFileProcessor:
    """
    Simple file processor that handles basic file types without heavy dependencies.
    This is a fallback when full file processing libraries are not available.
    """
    
    SUPPORTED_FORMATS = {
        'text/plain': 'txt'
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self):
        pass
    
    async def extract_text_from_file(self, file: UploadFile) -> str:
        """
        Extract text content from uploaded file (TXT files only in simple mode).
        
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
            if file_format == 'txt':
                text = await self._extract_from_txt(content)
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="ในโหมดพื้นฐานรองรับเฉพาะไฟล์ TXT เท่านั้น กรุณาติดตั้ง dependencies เพิ่มเติมสำหรับ PDF/DOC"
                )
            
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
            if filename_lower.endswith('.txt'):
                return 'txt'
        
        raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์ TXT ในโหมดพื้นฐาน")
    
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
            raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์ TXT ในโหมดพื้นฐาน")
        
        return True