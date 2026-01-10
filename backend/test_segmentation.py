import sys
from pythainlp import sent_tokenize

text = """ในยุคดิจิทัล ข้อมูล (Data) เปรียบเสมือนน้ำมันดิบ แต่มันจะไม่มีค่าเลยหากไม่ผ่านกระบวนการกลั่นกรอง หรือที่เรียกว่า "การประเมวลผลข้อมูล" (Data Processing)
การประมวลผล คือขั้นตอนการนำข้อมูลดิบ (Raw Data) ที่อาจจะยุ่งเหยิง กระจัดกระจาย มาผ่านกรรมวิธีทางคอมพิวเตอร์
เพื่อเปลี่ยนให้เป็นสารสนเทศ (Information) ที่มนุษย์เข้าใจได้และนำไปใช้ประโยชน์ได้จริง โดยมีวงจรหลัก 3 ขั้นตอน"""

print("--- Original Text ---")
print(text)
print("\n--- Sentences (default) ---")
try:
    sentences = sent_tokenize(text)
    for i, s in enumerate(sentences):
        print(f"{i+1}: {s}")
except Exception as e:
    print(e)
