import sys
import os

# Add backend directory to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from app.summarizer.summarization_model import SummarizationModel
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_textrank():
    model = SummarizationModel()
    
    # Sample Thai text (News article about AI)
    text = """
    ปัญญาประดิษฐ์ หรือ เอไอ กลายเป็นเทคโนโลยีที่มีบทบาทสำคัญในปัจจุบัน 
    การพัฒนาเอไอเป็นไปอย่างก้าวกระโดดในช่วงไม่กี่ปีที่ผ่านมา 
    บริษัทเทคโนโลยีชั้นนำต่างแข่งขันกันพัฒนาโมเดลภาษาขนาดใหญ่ 
    การนำเอไอมาประยุกต์ใช้ช่วยเพิ่มประสิทธิภาพในการทำงานหลากหลายด้าน 
    อย่างไรก็ตาม ความกังวลเกี่ยวกับผลกระทบของเอไอก็มีมากขึ้นเช่นกัน 
    โดยเฉพาะในเรื่องของการแย่งงานมนุษย์และความเป็นส่วนตัวของข้อมูล 
    ภาครัฐและเอกชนจึงต้องร่วมมือกันวางกรอบการกำกับดูแลเอไอให้เหมาะสม
    """
    
    print("Original Text Length:", len(text))
    
    try:
        summary = model.summarize(text, num_sentences=3)
        print("\nSummary Result:")
        print(summary)
        print("\nSummary Length:", len(summary))
        
        if not summary:
            print("FAILED: Summary is empty")
        else:
            print("SUCCESS: TextRank ran successfully")
            
    except Exception as e:
        print(f"FAILED: Error during summarization: {e}")

if __name__ == "__main__":
    test_textrank()
