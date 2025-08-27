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
        :disabled="loading || !inputText.trim()" 
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
        {{ loading ? 'กำลังประมวลผล...' : 'สรุปเนื้อหา' }}
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
      backendUrl: 'http://127.0.0.1:8000'
    }
  },
  methods: {
    async summarize() {
      this.error = ''
      this.summary = ''
      if (!this.inputText.trim()) {
        this.error = 'กรุณากรอกข้อความ'
        return
      }
      this.loading = true
      try {
        const res = await axios.post(`${this.backendUrl}/summarize`, {
          text: this.inputText,
          num_sentences: this.numSentences
        })
        this.summary = res.data.summary
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
      } finally {
        this.loading = false
      }
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

