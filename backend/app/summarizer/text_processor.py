import re

class TextProcessor:
    def clean_text(self, text: str) -> str:
        if not text:
            return ""

        # 1. กรองสัญญาณรบกวน (ส่วนเกินจากสคริปต์) - ย้ายมาไว้ด้านบนสุด
        
        # A. ลบ "ทั้งบรรทัด" สำหรับพวกหัวข้อเทคนิค (ฉาก, มุมกล้อง, ภาพ)
        delete_patterns = [
            r'(?i)^\s*(?:Scene|Int\.|Ext\.|ซีน|ฉาก)\s*[\d:]+.*$', 
            r'(?i)^\s*(?:Camera(?:\s*Angle)?|Cut\s*to|มุมกล้อง|ภาพ|Visual)\s*[:\s].*$',
            r'(?i)^\s*\[\s*.*\s*\]\s*$' # บรรทัดที่มีแค่ [เวลา] หรือ [การกระทำ]
        ]
        for pattern in delete_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE)

        # B. ลบ "แค่คำนำหน้า" สำหรับบทพูด/เสียงบรรยาย (เก็บเนื้อหาไว้!)
        # รูปแบบ: "ผู้พูด: " -> ""
        prefix_patterns = [
            r'(?i)^\s*(?:Voice\s*Over|VO|เสียงบรรยาย|บทพูด|Dialogue|Line)\s*[:\s]+', 
            r'(?i)^\s*(?:นักแสดง|ตัวละคร|Character|Cast|พี่\s*[A-Z])\s*[:\s]+',
            r'(?i)^\s*[A-Z\s]+:\s', # ชื่อภาษาอังกฤษ: ...
            r'(?i)^\s*[^:\n]+:\s' # ชื่อทั่วไป: ... (ดักจับป้ายชื่อผู้พูดที่เหลือถ้าเป็นไปได้ ระวังอย่ากินเนื้อหาประโยค)
        ]
        for pattern in prefix_patterns:
            text = re.sub(pattern, ' ', text, flags=re.MULTILINE)

        # C. ทำความสะอาดพวก Bullet/OCR ที่ทำให้ TextRank เพี้ยน
        # ลบตัวนำหน้า "•", "-", "0", "*" ที่ต้นบรรทัด
        text = re.sub(r'(?m)^\s*[•●▪\-*0o๐]+\s+', ' ', text)
        
        # D. ลบส่วนเกินที่แทรกอยู่ในบรรทัด
        inline_patterns = [
            r'\[\d{1,2}:\d{2}\]', r'\(\d{1,2}:\d{2}\)', # ประทับเวลา
            r'\([^)]*\)' # คำสั่งการแสดงในวงเล็บ (หัวเราะ)
        ]
        for pattern in inline_patterns:
            text = re.sub(pattern, '', text)
        
        # 2. จัดรูปแบบการขึ้นบรรทัดใหม่: แทนที่การขึ้นบรรทัดใหม่เดี่ยวด้วยช่องว่าง เก็บการขึ้นบรรทัดใหม่คู่ไว้ (ย่อหน้า)
        # แก้ปัญหา PDF ตัดคำที่ประโยคถูกแบ่งข้ามบรรทัด
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        # 3. การจัดรูปแบบภาษาไทย: รวม นิคหิต + สระอา -> สระอำ
        text = text.replace('\u0E4D\u0E32', '\u0E33') 
        text = text.replace('\u0E32\u0E4D', '\u0E33')

        # 4. ยุบช่องว่างที่ซ้อนกัน
        text = re.sub(r' +', ' ', text)
        
        return text.strip()

    def _is_valid_sentence(self, sentence: str) -> bool:
        """
        การตรวจสอบแบบ Heuristic: คืนค่า False ถ้าประโยคเป็นขยะ/สรุปไม่ได้
        """
        s = sentence.strip()
        if len(s) < 15:
            return False
            
        # คำเชื่อมที่บ่งบอกว่าเป็นส่วนขยาย ไม่ใช่ใจความหลัก
        bad_starters = ('และ', 'แต่', 'ซึ่ง', 'ยิ่งไปกว่านั้น', 'นอกจากนี้', 'เพราะ', 'โดย', 'ที่')
        if s.startswith(bad_starters):
            # อย่างไรก็ตาม ถ้าประโยคยาวมาก อาจจะเป็นประโยคความซ้อนที่ดีก็ได้
            # แต่โดยปกติสำหรับการสรุป เราต้องการประโยคที่สมบูรณ์ในตัวเอง
            # เข้มงวดกับประโยคสั้น < 40 ตัวอักษร แต่ยืดหยุ่นกับประโยคยาว
            if len(s) < 40:
                return False
                
        return True

    def __init__(self):
        try:
            from .constants import THAI_DICT
            self.thai_dict = THAI_DICT
        except ImportError:
            self.thai_dict = set()
        self.max_word_len = 20 # ความยาวสูงสุดที่จะสแกนหาคำในพจนานุกรม

    def tokenize(self, text: str) -> list[str]:
        """
        ตัดคำโดยใช้ Maximum Matching กับพจนานุกรมขนาดเล็กในตัว
        จำเป็นสำหรับ TextRank ภาษาไทย (เพราะภาษาไทยไม่มีช่องว่าง)
        """
        if not text:
            return []

        # 1. แยกด้วยช่องว่าง/บรรทัดใหม่ก่อน (ง่ายที่สุด)
        chunks = text.split()
        tokens = []

        for chunk in chunks:
            # ถ้าเป็นภาษาอังกฤษ/ตัวเลข (ส่วนใหญ่) ให้เก็บไว้เลย
            if re.match(r'^[a-zA-Z0-9\.\-\,]+$', chunk):
                tokens.append(chunk)
                continue
                
            # ตรรกะ MaxMatch ภาษาไทย
            i = 0
            while i < len(chunk):
                found = False
                # พยายามหาคำที่ยาวที่สุดที่ตรงกับพจนานุกรม
                if self.thai_dict:
                    for j in range(min(len(chunk), i + self.max_word_len), i, -1):
                        word = chunk[i:j]
                        if word in self.thai_dict:
                            tokens.append(word)
                            i = j
                            found = True
                            break
                
                if not found:
                    # ถ้าไม่เจอในพจนานุกรม ให้เก็บทีละ 1 ตัวอักษร
                    tokens.append(chunk[i])
                    i += 1
        
        return tokens

    def segment_sentences(self, text: str) -> list[str]:
        """
        แบ่งข้อความเป็นประโยคโดยใช้ตรรกะภาษาไทยดั้งเดิม (คั่นด้วยช่องว่าง)
        บวกกับบรรทัดใหม่และเครื่องหมายวรรคตอน รวมถึงตรรกะซ่อมประโยคที่ขาด
        """
        if not text:
            return []
            
        # 1. แยกด้วยบรรทัดใหม่ก่อน (ย่อหน้ามักจะหมายถึงจบประโยค)
        lines = text.splitlines()
        
        raw_sentences = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 2. แยกด้วยเครื่องหมายวรรคตอน หรือ ช่องว่าง (สำหรับไทย ช่องว่าง = จบประโยค/วลี)
            # ใช้ช่องว่างเดียวแยกได้เลย แล้วค่อยไปรวมกันใหม่ในขั้นตอนต่อไป
            chunks = re.split(r'(?:[!?.]+| +)', line)

            for chunk in chunks:
                if chunk.strip():
                    raw_sentences.append(chunk.strip())
        
        # 4. ซ่อมประโยคที่ขาด (เช่น จบด้วยคำเชื่อม/คำนำหน้า) & รวมท่อนสั้นๆ
        final_sentences = []
        # เพิ่ม 'ความ', 'การ', 'ของ', 'ใน' เพื่อป้องกันการตัดจบที่คำนำหน้า/คำบุพบททั่วไป
        bad_endings = ('แต่', 'และ', 'หรือ', 'ก็', 'คือ', 'ว่า', 'ซึ่ง', 'ที่', 'เพื่อ', 'โดย', 'กับ', 'ความ', 'การ', 'ของ', 'ใน', 'ไม่')
        
        buffer = ""
        # Heuristic: ความยาวขั้นต่ำของประโยค/ใจความที่ "สมบูรณ์" -> ลดเหลือ 20 เพื่อให้ได้ Bullet Points ที่ละเอียดขึ้น
        MIN_SENTENCE_LENGTH = 20 
        
        for s in raw_sentences:
            s = s.strip()
            if not s: continue
            
            # ถ้ามี buffer แสดงว่ากำลังอยู่ในโหมดรวมประโยค
            if buffer:
                buffer += " " + s
                # รวมต่อถ้าจบด้วยคำที่ไม่ดี หรือยังสั้นเกินไป
                if buffer.endswith(bad_endings) or len(buffer) < MIN_SENTENCE_LENGTH:
                    continue
                else:
                    if self._is_valid_sentence(buffer):
                         final_sentences.append(buffer)
                    buffer = ""
            else:
                # ผู้ท้าชิงประโยคใหม่
                if s.endswith(bad_endings) or len(s) < MIN_SENTENCE_LENGTH:
                    buffer = s
                else:
                    if self._is_valid_sentence(s):
                         final_sentences.append(s)
        
        # ล้าง Buffer
        if buffer and self._is_valid_sentence(buffer):
             final_sentences.append(buffer)

        # กรองขยะสั้นๆ ที่อาจหลุดรอดมาเป็นครั้งสุดท้าย
        return [s for s in final_sentences if self._is_valid_sentence(s)]