<template>
  <div class="summarizer-card">
    <div class="card-header">
      <div class="header-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
          <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2"/>
          <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/>
          <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2"/>
          <polyline points="10,9 9,9 8,9" stroke="currentColor" stroke-width="2"/>
        </svg>
      </div>
      <div class="header-content">
        <h2>สรุปบทความ</h2>
        <p>ใช้ AI เพื่อสรุปเนื้อหายาวๆ ให้กระชับและเข้าใจง่าย</p>
      </div>
    </div>
    
    <div class="input-section">
      <!-- File Upload or Text Input Toggle -->
      <div class="input-type-selector">
        <button 
          @click="inputType = 'text'" 
          :class="['type-button', { 'active': inputType === 'text' }]"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
            <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2"/>
            <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/>
            <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2"/>
          </svg>
          ข้อความ
        </button>
        <button 
          @click="inputType = 'file'" 
          :class="['type-button', { 'active': inputType === 'file' }]"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
            <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2"/>
            <path d="M9.5 12h5" stroke="currentColor" stroke-width="2"/>
            <path d="M12 9.5v5" stroke="currentColor" stroke-width="2"/>
          </svg>
          อัปโหลดไฟล์
        </button>
      </div>

      <!-- Text Input -->
      <div v-if="inputType === 'text'" class="text-input-container">
        <label class="input-label">
          <span class="label-text">เนื้อหาที่ต้องการสรุป</span>
          <span class="label-hint">วางข้อความหรือบทความที่ต้องการสรุปที่นี่</span>
        </label>
        <textarea 
          v-model="inputText" 
          placeholder="วางข้อความยาวๆ ที่นี่... ยิ่งมีเนื้อหามากยิ่งได้ผลลัพธ์ที่ดี" 
          rows="8"
          class="text-input"
        ></textarea>
      </div>

      <!-- File Upload -->
      <div v-else class="file-input-container">
        <label class="input-label">
          <span class="label-text">อัปโหลดไฟล์เอกสาร</span>
          <span class="label-hint" v-if="serverInfo && serverInfo.file_processor_mode === 'simple'">
            รองรับเฉพาะไฟล์ TXT (ขนาดสูงสุด 10MB) - ติดตั้ง dependencies เพิ่มเติมสำหรับ PDF/DOC
          </span>
          <span class="label-hint" v-else>
            รองรับไฟล์ PDF, DOC, DOCX, TXT (ขนาดสูงสุด 10MB)
          </span>
        </label>
        
        <div class="file-upload-area" 
             :class="{ 'drag-over': isDragOver, 'has-file': selectedFile }"
             @drop="handleFileDrop"
             @dragover.prevent="handleDragOver"
             @dragleave="handleDragLeave"
             @click="$refs.fileInput.click()">
          
          <input 
            ref="fileInput"
            type="file" 
            @change="handleFileSelect"
            :accept="serverInfo && serverInfo.file_processor_mode === 'simple' ? '.txt' : '.pdf,.doc,.docx,.txt'"
            class="file-input-hidden"
          />
          
          <div v-if="!selectedFile" class="upload-placeholder">
            <div class="upload-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.5"/>
                <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="1.5"/>
                <path d="M12 11v6" stroke="currentColor" stroke-width="1.5"/>
                <path d="M9 14l3-3 3 3" stroke="currentColor" stroke-width="1.5"/>
              </svg>
            </div>
            <div class="upload-text">
              <p class="upload-primary">ลากไฟล์มาวางที่นี่ หรือคลิกเพื่อเลือกไฟล์</p>
              <p class="upload-secondary" v-if="serverInfo && serverInfo.file_processor_mode === 'simple'">
                รองรับเฉพาะไฟล์ TXT
              </p>
              <p class="upload-secondary" v-else>
                รองรับไฟล์ PDF, DOC, DOCX, TXT
              </p>
            </div>
          </div>

          <div v-else class="file-preview">
            <div class="file-info">
              <div class="file-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
                  <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <div class="file-details">
                <p class="file-name">{{ selectedFile.name }}</p>
                <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
              </div>
            </div>
            <button @click.stop="removeFile" class="remove-file-button">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
                <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- File processing status -->
        <div v-if="fileProcessing" class="file-processing">
          <div class="processing-icon">
            <svg class="loading-spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 12a9 9 0 11-6.219-8.56" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <span>กำลังประมวลผลไฟล์...</span>
        </div>
      </div>
    </div>
    
    <div class="controls-section">
      <div class="control-group">
        <label class="control-label">จำนวนประโยคที่ต้องการสรุป</label>
        <div class="number-input-wrapper">
          <input 
            type="number" 
            v-model.number="numSentences" 
            min="1" 
            max="10" 
            class="number-input"
          />
          <span class="input-unit">ประโยค</span>
        </div>
      </div>
      
      <button 
        @click="summarize" 
        :disabled="loading || (inputType === 'text' && !inputText.trim()) || (inputType === 'file' && !selectedFile)" 
        class="summarize-button"
        :class="{ 'loading': loading }"
      >
        <svg v-if="loading" class="loading-spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 12a9 9 0 11-6.219-8.56" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <polyline points="10,15 15,10 21,4" stroke="currentColor" stroke-width="2"/>
        </svg>
        {{ loading ? 'กำลังประมวลผล...' : (inputType === 'file' ? 'สรุปไฟล์' : 'สรุปเนื้อหา') }}
      </button>
    </div>
    
    <div v-if="error" class="error-message">
      <div class="error-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
          <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/>
        </svg>
      </div>
      <span>{{ error }}</span>
    </div>
    
    <div v-if="summary" class="summary-section">
      <div class="summary-header">
        <div class="summary-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polyline points="20,6 9,17 4,12" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <h3>ผลลัพธ์การสรุป</h3>
      </div>
      <div class="summary-content">
        <p>{{ summary }}</p>
      </div>
      <div class="summary-actions">
        <button @click="copyToClipboard" class="copy-button">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" stroke-width="2"/>
          </svg>
          คัดลอก
        </button>
        <button @click="clearResults" class="clear-button">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polyline points="3,6 5,6 21,6" stroke="currentColor" stroke-width="2"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2"/>
          </svg>
          ล้างผลลัพธ์
        </button>
      </div>
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
      backendUrl: 'http://127.0.0.1:8000',
      inputType: 'text', // 'text' or 'file'
      selectedFile: null,
      fileProcessing: false,
      isDragOver: false,
      serverInfo: null
    }
  },
  
  async created() {
    // Check server capabilities
    await this.checkServerCapabilities()
  },
  methods: {
    async checkServerCapabilities() {
      try {
        const response = await axios.get(`${this.backendUrl}/health`)
        this.serverInfo = response.data
        
        // If server only supports TXT files, show warning
        if (this.serverInfo.file_processor_mode === 'simple') {
          console.warn('Server is running in simple mode - only TXT files are supported')
        }
      } catch (error) {
        console.error('Failed to check server capabilities:', error)
      }
    },
    
    async summarize() {
      this.error = ''
      this.summary = ''
      
      // Check input based on type
      if (this.inputType === 'text') {
        if (!this.inputText.trim()) {
          this.error = 'กรุณากรอกข้อความ'
          return
        }
      } else if (this.inputType === 'file') {
        if (!this.selectedFile) {
          this.error = 'กรุณาเลือกไฟล์'
          return
        }
      }
      
      this.loading = true
      try {
        let response
        
        if (this.inputType === 'text') {
          // Text summarization
          response = await axios.post(`${this.backendUrl}/summarize`, {
            text: this.inputText,
            num_sentences: this.numSentences
          })
        } else {
          // File summarization
          const formData = new FormData()
          formData.append('file', this.selectedFile)
          formData.append('num_sentences', this.numSentences.toString())
          
          response = await axios.post(`${this.backendUrl}/summarize-file`, formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          })
        }
        
        this.summary = response.data.summary
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
      } finally {
        this.loading = false
      }
    },
    
    // File handling methods
    handleFileSelect(event) {
      const file = event.target.files[0]
      this.processSelectedFile(file)
    },
    
    handleFileDrop(event) {
      event.preventDefault()
      this.isDragOver = false
      const file = event.dataTransfer.files[0]
      this.processSelectedFile(file)
    },
    
    handleDragOver(event) {
      event.preventDefault()
      this.isDragOver = true
    },
    
    handleDragLeave() {
      this.isDragOver = false
    },
    
    processSelectedFile(file) {
      if (!file) return
      
      // Check server capabilities
      const isSimpleMode = this.serverInfo && this.serverInfo.file_processor_mode === 'simple'
      
      // Validate file type based on server capabilities
      let allowedTypes, allowedExtensions, errorMessage
      
      if (isSimpleMode) {
        allowedTypes = ['text/plain']
        allowedExtensions = ['.txt']
        errorMessage = 'รองรับเฉพาะไฟล์ TXT เท่านั้น (ติดตั้ง dependencies เพิ่มเติมสำหรับ PDF/DOC)'
      } else {
        allowedTypes = ['application/pdf', 'application/msword', 
                       'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                       'text/plain']
        allowedExtensions = ['.pdf', '.doc', '.docx', '.txt']
        errorMessage = 'รองรับเฉพาะไฟล์ PDF, DOC, DOCX, TXT เท่านั้น'
      }
      
      const isValidType = allowedTypes.includes(file.type) || 
                         allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
      
      if (!isValidType) {
        this.error = errorMessage
        return
      }
      
      // Validate file size (10MB)
      const maxSize = 10 * 1024 * 1024
      if (file.size > maxSize) {
        this.error = 'ขนาดไฟล์เกิน 10MB'
        return
      }
      
      this.selectedFile = file
      this.error = ''
    },
    
    removeFile() {
      this.selectedFile = null
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },
    
    async copyToClipboard() {
      try {
        await navigator.clipboard.writeText(this.summary)
        // Could add a toast notification here
      } catch (err) {
        console.error('Failed to copy text: ', err)
      }
    },
    
    clearResults() {
      this.summary = ''
      this.error = ''
      this.inputText = ''
      this.selectedFile = null
      this.inputType = 'text'
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    }
  }
}
</script>

<style scoped>
/* Modern Summarizer Card Styles */
.summarizer-card {
  background: white;
  border-radius: 24px;
  padding: 2rem;
  box-shadow: 0 10px 25px rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.1);
  max-width: 800px;
  margin: 0 auto;
  position: relative;
  overflow: hidden;
}

.summarizer-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #8B5CF6, #A855F7);
}

/* Card Header */
.card-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #E5E7EB;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #8B5CF6, #A855F7);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.header-content h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1F2937;
}

.header-content p {
  margin: 0;
  color: #6B7280;
  font-size: 0.875rem;
  line-height: 1.5;
}

/* Input Section */
.input-section {
  margin-bottom: 2rem;
}

/* Input Type Selector */
.input-type-selector {
  display: flex;
  background: #F3F4F6;
  border-radius: 12px;
  padding: 0.25rem;
  margin-bottom: 1.5rem;
  gap: 0.25rem;
}

.type-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  background: transparent;
  color: #6B7280;
}

.type-button.active {
  background: white;
  color: #8B5CF6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.type-button:hover:not(.active) {
  color: #374151;
}

/* Text Input Container */
.text-input-container {
  animation: fadeIn 0.3s ease;
}

.input-label {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.label-text {
  font-weight: 600;
  color: #1F2937;
  font-size: 0.875rem;
}

.label-hint {
  font-size: 0.75rem;
  color: #9CA3AF;
}

.text-input {
  width: 100%;
  padding: 1rem;
  border: 2px solid #E5E7EB;
  border-radius: 12px;
  font-size: 0.875rem;
  line-height: 1.6;
  transition: all 0.3s ease;
  background: rgba(139, 92, 246, 0.02);
  resize: vertical;
  min-height: 150px;
}

.text-input:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  background: rgba(139, 92, 246, 0.05);
}

.text-input::placeholder {
  color: #9CA3AF;
}

/* File Input Container */
.file-input-container {
  animation: fadeIn 0.3s ease;
}

.file-upload-area {
  border: 2px dashed #E5E7EB;
  border-radius: 16px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(139, 92, 246, 0.02);
  position: relative;
}

.file-upload-area:hover {
  border-color: #8B5CF6;
  background: rgba(139, 92, 246, 0.05);
}

.file-upload-area.drag-over {
  border-color: #8B5CF6;
  background: rgba(139, 92, 246, 0.1);
  transform: scale(1.02);
}

.file-upload-area.has-file {
  border-style: solid;
  border-color: #8B5CF6;
  background: rgba(139, 92, 246, 0.05);
}

.file-input-hidden {
  display: none;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.upload-icon {
  color: #8B5CF6;
  opacity: 0.7;
}

.upload-text {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.upload-primary {
  font-size: 1rem;
  font-weight: 600;
  color: #1F2937;
  margin: 0;
}

.upload-secondary {
  font-size: 0.875rem;
  color: #6B7280;
  margin: 0;
}

.file-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: white;
  border-radius: 12px;
  border: 1px solid #E5E7EB;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-icon {
  color: #8B5CF6;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.file-name {
  font-weight: 600;
  color: #1F2937;
  margin: 0;
  font-size: 0.875rem;
}

.file-size {
  font-size: 0.75rem;
  color: #6B7280;
  margin: 0;
}

.remove-file-button {
  background: rgba(239, 68, 68, 0.1);
  color: #DC2626;
  border: none;
  border-radius: 8px;
  padding: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-file-button:hover {
  background: rgba(239, 68, 68, 0.2);
  transform: scale(1.1);
}

.file-processing {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 12px;
  margin-top: 1rem;
  color: #8B5CF6;
  font-size: 0.875rem;
  font-weight: 500;
}

.processing-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Controls Section */
.controls-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1.5rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1F2937;
}

.number-input-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: white;
  border: 2px solid #E5E7EB;
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  transition: all 0.3s ease;
}

.number-input-wrapper:focus-within {
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.number-input {
  border: none;
  outline: none;
  width: 60px;
  text-align: center;
  font-weight: 600;
  color: #1F2937;
}

.input-unit {
  font-size: 0.75rem;
  color: #6B7280;
  font-weight: 500;
}

.summarize-button {
  background: linear-gradient(135deg, #8B5CF6, #A855F7);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(139, 92, 246, 0.25);
  white-space: nowrap;
}

.summarize-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 15px rgba(139, 92, 246, 0.35);
}

.summarize-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Error Message */
.error-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 12px;
  color: #DC2626;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.error-icon {
  flex-shrink: 0;
}

/* Summary Section */
.summary-section {
  background: linear-gradient(135deg, #F3E8FF, rgba(168, 85, 247, 0.1));
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(139, 92, 246, 0.2);
  animation: slideInUp 0.5s ease-out;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.summary-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #8B5CF6, #A855F7);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.summary-header h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 700;
  color: #1F2937;
}

.summary-content {
  background: white;
  padding: 1.25rem;
  border-radius: 12px;
  margin-bottom: 1rem;
  box-shadow: 0 2px 4px rgba(139, 92, 246, 0.1);
}

.summary-content p {
  margin: 0;
  line-height: 1.7;
  color: #374151;
}

.summary-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.copy-button, .clear-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.copy-button {
  background: rgba(139, 92, 246, 0.1);
  color: #8B5CF6;
}

.copy-button:hover {
  background: rgba(139, 92, 246, 0.2);
  transform: translateY(-1px);
}

.clear-button {
  background: rgba(107, 114, 128, 0.1);
  color: #6B7280;
}

.clear-button:hover {
  background: rgba(107, 114, 128, 0.2);
  transform: translateY(-1px);
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .summarizer-card {
    padding: 1.5rem;
    margin: 0 1rem;
  }
  
  .controls-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .summarize-button {
    width: 100%;
    justify-content: center;
  }
  
  .summary-actions {
    flex-direction: column;
  }
  
  .copy-button, .clear-button {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .card-header {
    flex-direction: column;
    text-align: center;
  }
  
  .header-content h2 {
    font-size: 1.25rem;
  }
}
</style>

