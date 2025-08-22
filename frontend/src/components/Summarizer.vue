<template>
  <div class="card">
    <h2>สรุปบทความ</h2>
    
    <div class="file-upload-section">
      <h3>อัปโหลดไฟล์</h3>
      <div class="file-input-container">
        <input 
          type="file" 
          ref="fileInput" 
          @change="handleFileUpload" 
          accept=".txt,.docx,.pdf"
          class="file-input"
        />
        <button @click="$refs.fileInput.click()" class="upload-btn">
          เลือกไฟล์ (.txt, .docx, .pdf)
        </button>
        <span v-if="selectedFile" class="file-name">{{ selectedFile.name }}</span>
      </div>
      <div class="file-info" v-if="selectedFile">
        <p>ไฟล์ที่เลือก: {{ selectedFile.name }}</p>
        <p>ขนาด: {{ formatFileSize(selectedFile.size) }}</p>
      </div>
    </div>

    <div class="text-input-section">
      <h3>หรือใส่ข้อความโดยตรง</h3>
      <textarea v-model="inputText" placeholder="วางข้อความยาวๆ ที่นี่..." rows="8"></textarea>
    </div>

    <div class="controls">
      <label>จำนวนประโยคที่ต้องการสรุป:</label>
      <input type="number" v-model.number="numSentences" min="1" max="10" />
      <button @click="summarize" :disabled="loading || (!inputText.trim() && !selectedFile)">
        {{ selectedFile ? 'สรุปจากไฟล์' : 'สรุป' }}
      </button>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>กำลังประมวลผล...</p>
    </div>
    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="summary" class="summary">
      <h3>ผลลัพธ์</h3>
      <div v-if="fileInfo" class="file-info-result">
        <p><strong>ไฟล์:</strong> {{ fileInfo.filename }}</p>
        <p><strong>ขนาด:</strong> {{ fileInfo.file_size }} ตัวอักษร</p>
      </div>
      <p>{{ summary }}</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Summarizer',
  data() {
    return {
      inputText: '',
      numSentences: 3,
      summary: '',
      loading: false,
      error: '',
      selectedFile: null,
      fileInfo: null,
      backendUrl: 'http://127.0.0.1:8000'
    }
  },
  methods: {
    handleFileUpload(event) {
      const file = event.target.files[0]
      if (file) {
        const allowedTypes = ['.txt', '.docx', '.pdf']
        const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
        if (!allowedTypes.includes(fileExtension)) {
          this.error = 'รองรับเฉพาะไฟล์ .txt, .docx และ .pdf เท่านั้น'
          return
        }
        if (file.size > 10 * 1024 * 1024) {
          this.error = 'ไฟล์มีขนาดใหญ่เกินไป (สูงสุด 10MB)'
          return
        }
        this.selectedFile = file
        this.error = ''
        this.summary = ''
        this.fileInfo = null
      }
    },

    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },

    async summarize() {
      this.error = ''
      this.summary = ''
      this.fileInfo = null

      if (!this.inputText.trim() && !this.selectedFile) {
        this.error = 'กรุณากรอกข้อความหรือเลือกไฟล์'
        return
      }

      this.loading = true

      try {
        if (this.selectedFile) {
          await this.summarizeFromFile()
        } else {
          await this.summarizeFromText()
        }
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
      } finally {
        this.loading = false
      }
    },

    async summarizeFromFile() {
      const formData = new FormData()
      formData.append('file', this.selectedFile)
      formData.append('num_sentences', this.numSentences)

      const res = await axios.post(`${this.backendUrl}/summarize-file`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      this.summary = res.data.summary
      this.fileInfo = {
        filename: res.data.filename,
        file_size: res.data.file_size
      }
    },

    async summarizeFromText() {
      const res = await axios.post(`${this.backendUrl}/summarize`, {
        text: this.inputText,
        num_sentences: this.numSentences
      })

      this.summary = res.data.summary
    }
  }
}
</script>

<style scoped>
.card { 
  background: white; 
  border-radius: 12px; 
  padding: 20px; 
  box-shadow: 0 8px 24px rgba(0,0,0,0.08); 
}

.file-upload-section, .text-input-section {
  margin-bottom: 20px;
}

.file-upload-section h3, .text-input-section h3 {
  margin-bottom: 12px;
  color: #333;
  font-size: 16px;
}

.file-input-container {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.file-input {
  display: none;
}

.upload-btn {
  background: linear-gradient(90deg, #3498db, #2980b9);
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
}

.upload-btn:hover {
  background: linear-gradient(90deg, #2980b9, #1f5f8b);
}

.file-name {
  color: #27ae60;
  font-weight: 500;
}

.file-info {
  background: #f8f9fa;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
}

.file-info p {
  margin: 4px 0;
  color: #666;
}

textarea { 
  width: 100%; 
  padding: 12px; 
  border-radius: 8px; 
  border: 1px solid #ddd; 
  resize: vertical;
}

.controls { 
  display: flex; 
  gap: 12px; 
  align-items: center; 
  margin-top: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.controls input { 
  width: 80px; 
  padding: 6px 8px; 
  border: 1px solid #ddd;
  border-radius: 4px;
}

button { 
  background: linear-gradient(90deg, #9b59b6, #d247d7); 
  color: white; 
  border: none; 
  padding: 10px 16px; 
  border-radius: 20px; 
  cursor: pointer;
  font-weight: 500;
}

button:hover {
  background: linear-gradient(90deg, #8e44ad, #c0392b);
}

button:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.loading {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  color: #666;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #9b59b6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error { 
  color: #e74c3c; 
  margin-top: 12px;
  padding: 12px;
  background: #fdf2f2;
  border-radius: 6px;
  border-left: 4px solid #e74c3c;
}

.summary { 
  background: #f9f9ff; 
  border-radius: 8px; 
  padding: 16px; 
  margin-top: 16px;
  border-left: 4px solid #9b59b6;
}

.file-info-result {
  background: #e8f4fd;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 14px;
}

.file-info-result p {
  margin: 4px 0;
  color: #2c3e50;
}
</style>

