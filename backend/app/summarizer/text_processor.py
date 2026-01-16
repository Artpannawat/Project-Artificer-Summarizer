import re

class TextProcessor:
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        # 1. Normalize line breaks: Replace single newlines with spaces, keep double newlines (paragraphs)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        # 2. Normalize whitespace (remove zero-width spaces, multiple spaces)
        text = re.sub(r"[\u200b\u200c\u200d\uFEFF]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        
        return text

    
    def __init__(self):
        # Small Dictionary for "Basic" Tokenization (Lite version of PyThaiNLP)
        # Focus on "Function Words" that act as natural delimiters + Common words
        self.thai_dict = set([
            "การ", "ความ", "ที่", "ซึ่ง", "อัน", "และ", "หรือ", "แต่", "ก็", "ด้วย", "โดย", "ใน", "นอก", "บน", "ล่าง", "เหนือ", "ใต้", 
            "จาก", "ถึง", "สู่", "ยัง", "ให้", "ได้", "ไป", "มา", "มี", "เป็น", "อยู่", "จะ", "ต้อง", "น่า", "ควร", "อยาก", "ไม่", "ใช่", "ว่า",
            "เขา", "เธอ", "ฉัน", "มัน", "เรา", "ท่าน", "คน", "สัตว์", "สิ่ง", "ของ", "ผู้", "งาน", "เงิน", "ใจ", "ดี", "เลว", "มาก", "น้อย",
            "สูง", "ต่ำ", "ใหญ่", "เล็ก", "ใหม่", "เก่า", "แรก", "หลัง", "ก่อน", "นี้", "นั้น", "โน้น", "ไหน", "ไร", "ใคร", "เมื่อ", "ถ้า", "หาก",
            "เพราะ", "จึง", "แล้ว", "เลย", "นะ", "ครับ", "ค่ะ", "จ้ะ", "ละ", "สิ", "พ.ศ.", "จ.ศ.", "ร.ศ.", "บาท", "ดอลลาร์", "เมตร", "กิโลเมตร",
            "วัน", "เดือน", "ปี", "เวลา", "นาที", "ชั่วโมง", "ประเทศ", "จังหวัด", "อำเภอ", "ตำบล", "โรงเรียน", "มหาวิทยาลัย", "บริษัท", "ระบบ",
            "ข้อมูล", "ปัญหา", "ผล", "เหตุ", "ช่วย", "ส่ง", "รับ", "ซื้อ", "ขาย", "ติดต่อ", "สื่อสาร", "พัฒนา", "บริหาร", "จัดการ", "วิเคราะห์",
            "สรุป", "รายงาน", "ตัวอย่าง", "เช่น", "ได้แก่", "อาทิ", "สำหรับ", "เพื่อ", "ต่อ", "ของ", "แห่ง", "ราย", "กลุ่ม", "พวก", "เหล่า"
        ])
        self.max_word_len = 20 # Max length to scan for dictionary match

    def tokenize(self, text: str) -> list[str]:
        """
        Tokenize text into words using Maximum Matching with a small embedded dictionary.
        Essential for Thai TextRank to work (since Thai has no spaces).
        """
        if not text:
            return []

        # 1. Pre-split by spaces/newlines first (easy wins)
        chunks = text.split()
        tokens = []

        for chunk in chunks:
            # If chunk is English/Numbers (mostly), just keep it
            if re.match(r'^[a-zA-Z0-9\.\-\,]+$', chunk):
                tokens.append(chunk)
                continue
                
            # Thai MaxMatch Logic
            i = 0
            while i < len(chunk):
                found = False
                # Try to find longest matching word from dictionary
                for j in range(min(len(chunk), i + self.max_word_len), i, -1):
                    word = chunk[i:j]
                    if word in self.thai_dict:
                        tokens.append(word)
                        i = j
                        found = True
                        break
                
                if not found:
                    # If not found in dict, take 1 character (or group of non-Thai chars)
                    # Optimization: Group unknown chars until we hit a known start-char? 
                    # For Basic Engine, just take 1 char is safe but slow/fragmented.
                    # Let's try to group "Unknowns"
                    tokens.append(chunk[i])
                    i += 1
        
        return tokens

    def segment_sentences(self, text: str) -> list[str]:
        """
        Segment text into partial sentences/phrases using punctuation and spacing.
        Enhanced for Thai/English mixed text to reduce "choppy" output.
        """
        if not text:
            return []
            
        # 1. Clean up excessive whitespace first
        text = re.sub(r' +', ' ', text.strip())
        
        # 2. Split by standard punctuation (.!?) followed by space
        # Lookbehind for punctuation, lookahead for space or end of string
        # Keep punctuation attached to the previous sentence if possible
        chunks = re.split(r'(?<=[.!?])\s+', text)
        
        final_sentences = []
        for chunk in chunks:
            if not chunk.strip():
                continue
                
            # 3. Handling Thai long paragraphs without punctuation
            # If a chunk is very long (>150 chars), try to find logical break points
            # Thai typically uses space for sentence boundaries, but also for emphasis.
            # We look for spaces that are likely sentence boundaries.
            
            if len(chunk) > 150:
                # Heuristic: Split by spaces that follow key conjunctions or standard gaps
                # This Regex looks for a space followed by typical Thai starting words or just large gaps
                # But to be safe for "Basic" engine, we just split by "  " (double space) if exists,
                # or single space if it's really long.
                
                # Split by any space, then regroup
                words = chunk.split(' ')
                current_sent = []
                current_len = 0
                
                for word in words:
                    conjunctions = ['ดังนั้น', 'เพราะ', 'แต่', 'อย่างไรก็ตาม', 'นอกจากนี้', 'ทั้งนี้', 'โดย', 'เพื่อ']
                    
                    # If current sentence is long enough AND (we hit a conjunction OR just getting too long)
                    if current_len > 80 and (word in conjunctions or current_len > 200):
                        final_sentences.append(" ".join(current_sent))
                        current_sent = [word]
                        current_len = len(word)
                    else:
                        current_sent.append(word)
                        current_len += len(word) + 1
                
                if current_sent:
                    final_sentences.append(" ".join(current_sent))
            else:
                final_sentences.append(chunk.strip())
                
        return [s.strip() for s in final_sentences if s.strip()]