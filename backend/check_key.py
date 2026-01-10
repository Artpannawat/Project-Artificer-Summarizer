import google.generativeai as genai
from decouple import config
import os

# 1. โหลด Key จาก .env
# (ลองหาทั้ง 2 ชื่อ เผื่อคุณตั้งชื่อสลับกัน)
api_key = config("GOOGLE_API_KEY", default=None)
if not api_key:
    api_key = config("GEMINI_API_KEY", default=None)

print(f"🔑 Loaded Key: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")

if not api_key:
    print("❌ ERROR: ไม่พบ API Key ในไฟล์ .env เลย! (เช็กชื่อตัวแปรด่วน)")
    exit()

# 2. ตั้งค่า
genai.configure(api_key=api_key)

# 3. ลองดึงรายชื่อโมเดลที่ Key นี้ใช้ได้
print("\n📋 Checking available models for this Key...")
found_lite = False
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"   ✅ {m.name}")
            if 'flash-lite' in m.name:
                found_lite = True
except Exception as e:
    print(f"❌ ERROR: Key นี้ใช้งานไม่ได้เลย! สาเหตุ: {e}")
    exit()

# 4. ทดสอบยิงจริง (Test Multiple Models)
candidates = [
    'gemini-2.0-flash-lite-preview-02-05',
    'gemini-2.0-flash',
    'gemini-2.5-flash',
    'gemini-1.5-flash',
]

print(f"\n🧪 Testing Generation on {len(candidates)} candidates...")

for model_name in candidates:
    print(f"\n------------------------------------------------")
    print(f"👉 Testing: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, just say OK.")
        print(f"   🎉 SUCCESS! Response: {response.text.strip()}")
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            print("   ⚠️ FAILED: Quota Exceeded (429)")
        elif "404" in error_msg:
            print("   ❌ FAILED: Model Not Found (404)")
        else:
            print(f"   💥 FAILED: {error_msg}")
