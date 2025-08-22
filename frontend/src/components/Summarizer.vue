<template>
  <div class="card">
    <h2>สรุปบทความ</h2>
    <textarea v-model="inputText" placeholder="วางข้อความยาวๆ ที่นี่..." rows="8"></textarea>
    <div class="controls">
      <label>จำนวนประโยคที่ต้องการสรุป:</label>
      <input type="number" v-model.number="numSentences" min="1" max="10" />
      <button @click="summarize" :disabled="loading">สรุป</button>
    </div>
    <div v-if="loading">กำลังประมวลผล...</div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="summary" class="summary">
      <h3>ผลลัพธ์</h3>
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
    }
  }
}
</script>

<style scoped>
.card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
textarea { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #ddd; }
.controls { display: flex; gap: 12px; align-items: center; margin-top: 12px; }
.controls input { width: 80px; padding: 6px 8px; }
button { background: linear-gradient(90deg, #9b59b6, #d247d7); color: white; border: none; padding: 10px 16px; border-radius: 20px; cursor: pointer; }
.error { color: #d33; margin-top: 12px; }
.summary { background: #f9f9ff; border-radius: 8px; padding: 12px; margin-top: 16px; }
</style>

