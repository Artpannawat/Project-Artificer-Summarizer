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
          <span class="input-unit">หัวข้อ</span>
        </div>
      </div>
      
      <button 
        @click="summarize" 
        :disabled="loading || cooldown || (inputType === 'text' && !inputText.trim()) || (inputType === 'file' && !selectedFile)" 
        class="summarize-button"
        :class="{ 'loading': loading || cooldown }"
      >
        <svg v-if="loading" class="loading-spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 12a9 9 0 11-6.219-8.56" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <polyline points="10,15 15,10 21,4" stroke="currentColor" stroke-width="2"/>
        </svg>
        {{ loading ? 'กำลังประมวลผล...' : (cooldown ? 'รอสักครู่...' : (inputType === 'file' ? 'สรุปไฟล์' : 'สรุปเนื้อหา')) }}
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
    
    <!-- Results Section -->
    <div v-if="basicSummary || aiSummary" class="results-container">
      
      <!-- Basic Engine Result -->
      <div v-if="basicSummary" class="summary-section basic-engine">
        <div class="summary-header">
          <div class="header-left">
            <div class="summary-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
                <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2"/>
                <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/>
                <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2"/>
                <polyline points="10,9 9,9 8,9" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <h3>Basic Engine (Traditional)</h3>
          </div>
          <button 
            @click="copyToClipboard(basicSummary, 'basic')" 
            class="copy-button-icon" 
            :class="{ 'copied': copiedState.basic }"
            :title="copiedState.basic ? 'คัดลอกแล้ว!' : 'คัดลอก'"
          >
            <svg v-if="!copiedState.basic" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8 4v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7.242a2 2 0 0 0-.602-1.43L16.083 2.57A2 2 0 0 0 14.685 2H10a2 2 0 0 0-2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M16 18v2a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
        <div class="summary-content">
          <p>{{ basicSummary }}</p>
        </div>
      </div>

      <!-- AI Engine Result -->
      <div v-if="aiSummary" class="summary-section ai-engine">
        <div class="summary-header">
          <div class="header-left">
            <div class="summary-icon ai-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="ai-header-text">
              <h3>Artificer AI Engine</h3>
              <span class="powered-by">Powered by Gemini</span>
            </div>
            <span class="premium-badge">Recommended</span>
          </div>
          
          <button 
            @click="copyToClipboard(aiSummary, 'ai')" 
            class="copy-button-icon" 
            :class="{ 'copied': copiedState.ai }"
            :title="copiedState.ai ? 'คัดลอกแล้ว!' : 'คัดลอก'"
          >
            <svg v-if="!copiedState.ai" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8 4v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7.242a2 2 0 0 0-.602-1.43L16.083 2.57A2 2 0 0 0 14.685 2H10a2 2 0 0 0-2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M16 18v2a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>

        <!-- Metrics Dashboard (Premium UI) -->
        <div v-if="aiMetrics" class="metrics-dashboard">
          <div class="metric-card">
             <span class="metric-label">Accuracy</span>
             <span class="metric-value text-green">{{ aiMetrics.accuracy }}%</span>
          </div>
          <div class="metric-divider"></div>
          <div class="metric-card">
             <span class="metric-label">Completeness</span>
             <span class="metric-value text-blue">{{ aiMetrics.completeness }}%</span>
          </div>
          <div class="metric-divider"></div>
          <div class="metric-card">
             <span class="metric-label">Avg. Score</span>
             <span class="metric-value text-purple">{{ aiMetrics.average }}%</span>
          </div>
        </div>
        <div class="summary-content">
          <p>{{ aiSummary }}</p>
        </div>
        
        <!-- Detailed Metrics Bar (Optional, can be toggled) -->
        <div v-if="aiMetrics" class="metrics-details">
           <div class="metric-item">
             <span>Accuracy</span>
             <div class="progress-bar"><div class="fill" :style="`width: ${aiMetrics.accuracy}%`"></div></div>
           </div>
           <div class="metric-item">
             <span>Completeness</span>
             <div class="progress-bar"><div class="fill" :style="`width: ${aiMetrics.completeness}%`"></div></div>
           </div>
           <div class="metric-item">
             <span>Conciseness</span>
             <div class="progress-bar"><div class="fill" :style="`width: ${aiMetrics.conciseness}%`"></div></div>
           </div>
        </div>
      </div>

      <div class="actions-row">
        <button @click="clearResults" class="clear-button">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polyline points="3,6 5,6 21,6" stroke="currentColor" stroke-width="2"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2"/>
          </svg>
          ล้างผลลัพธ์ทั้งหมด
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
      basicSummary: '',
      aiSummary: '',
      aiMetrics: null, // Store parsed metrics
      loading: false,
      error: '',
      backendUrl: import.meta.env.VITE_API_URL || ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? 'http://127.0.0.1:8000' : ''),
      inputType: 'text', // 'text' or 'file'
      selectedFile: null,
      fileProcessing: false,
      isDragOver: false,
      serverInfo: null,
      cooldown: false, // Spam Protection
      copiedState: { basic: false, ai: false }
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
      this.basicSummary = ''
      this.aiSummary = ''
      
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
        const token = localStorage.getItem('token')
        const headers = {}
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }
        
        if (this.inputType === 'text') {
          // Text summarization
          response = await axios.post(`${this.backendUrl}/summarize`, {
            text: this.inputText,
            num_sentences: this.numSentences
          }, { headers })
        } else {
          // File summarization
          const formData = new FormData()
          formData.append('file', this.selectedFile)
          formData.append('num_sentences', this.numSentences.toString())
          
          // Merge content-type with auth headers
          response = await axios.post(`${this.backendUrl}/summarize-file`, formData, {
            headers: {
              ...headers,
              'Content-Type': 'multipart/form-data'
            }
          })
        }
        
        // Handle new response format
        if (response.data.comparison_mode) {
           this.basicSummary = response.data.basic_summary
           
           let rawAi = response.data.ai_summary
           // Parse Metrics
           const metricsMatch = rawAi.match(/\[METRICS:\s*(\{.*?\})\s*\]/);
           if (metricsMatch && metricsMatch[1]) {
              try {
                  this.aiMetrics = JSON.parse(metricsMatch[1]);
                  // Remove metrics tag from display text
                  this.aiSummary = rawAi.replace(metricsMatch[0], '').trim();
              } catch (e) {
                  console.error("Failed to parse AI metrics", e);
                  this.aiSummary = rawAi;
                  this.aiMetrics = null;
              }
           } else {
              this.aiSummary = rawAi;
              this.aiMetrics = null;
           }
           
        } else {
           // Fallback just in case
           this.basicSummary = response.data.summary
           this.aiSummary = ""
           this.aiMetrics = null
        }
      } catch (e) {
        // Handle Quota Exceeded (429) specifically
        if (e.response && e.response.status === 500 && e.response.data && e.response.data.detail && e.response.data.detail.includes('429 RESOURCE_EXHAUSTED')) {
             this.aiSummary = "⚠️ ขออภัย AI Service ใช้งานเกินขีดจำกัด (Quota Exceeded) กรุณาลองใหม่ในอีกสักครู่ หรือใช้ Basic Engine ไปก่อน"
             // Keep basic summary if available
             if (!this.basicSummary) {
                 this.error = "AI Service is busy (Quota Exceeded). Please try again later."
             }
        } else if (e.response?.status === 429) {
             this.error = "System is busy. Please try again later."
        } else {
             this.error = e.response?.data?.detail || e.message
        }
      } finally {
        this.loading = false
        // Spam Protection: 3s Cooldown
        this.cooldown = true
        setTimeout(() => {
            this.cooldown = false
        }, 3000)
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
    
    async copyToClipboard(text, type) {
      try {
        await navigator.clipboard.writeText(text)
        // Set copied state
        this.copiedState[type] = true
        // Reset after 2 seconds
        setTimeout(() => {
          this.copiedState[type] = false
        }, 2000)
      } catch (err) {
        console.error('Failed to copy text: ', err)
      }
    },
    
    clearResults() {
      this.basicSummary = ''
      this.aiSummary = ''
      this.aiMetrics = null
      this.error = ''
      this.inputText = ''
      this.selectedFile = null
      this.inputType = 'text'
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },
    
    loadFromHistory(historyItem) {
      if (!historyItem) return
      
      // Reset first
      this.clearResults()
      
      // Restore input (We switch to text mode to show the content even if it was a file)
      this.inputType = 'text'
      this.inputText = historyItem.original_text || ''

      // Restore results from the nested summary_result object
      const result = historyItem.summary_result || {}
      
      this.basicSummary = result.basic_summary || ''
      
      // Handle AI Summary & Metrics Parsing for History
      let rawAi = result.ai_summary || ''
      
      const metricsMatch = rawAi.match(/\[METRICS:\s*(\{.*?\})\s*\]/);
      if (metricsMatch && metricsMatch[1]) {
          try {
              this.aiMetrics = JSON.parse(metricsMatch[1]);
              // Remove metrics tag from display text
              this.aiSummary = rawAi.replace(metricsMatch[0], '').trim();
          } catch (e) {
              console.error("Failed to parse AI metrics from history", e);
              this.aiSummary = rawAi;
              this.aiMetrics = null;
          }
      } else {
          this.aiSummary = rawAi;
          this.aiMetrics = null;
      }
      
      if (result.filename) {
        console.log("Loaded history from file:", result.filename)
      }
    }
  }
}
</script>

<style scoped src="./Summarizer.css"></style>
