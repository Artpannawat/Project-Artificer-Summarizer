<template>
  <div class="history-sidebar" :class="{ 'open': isOpen }">
    <div class="sidebar-header">
      <h3>ประวัติการใช้งาน</h3>
      <button @click="$emit('close')" class="close-btn" aria-label="Close Sidebar">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
      </button>
    </div>

    <!-- Clear All Button -->
    <div v-if="history.length > 0" class="actions-header">
        <button class="clear-all-btn" @click="confirmClearAll">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
            ล้างประวัติทั้งหมด
        </button>
    </div>

    <div class="history-list" v-if="!loading">
      <div v-if="history.length === 0" class="empty-state">
        <p>ยังไม่มีประวัติการใช้งาน</p>
      </div>

      <div v-for="(group, dateLabel) in groupedHistory" :key="dateLabel" class="history-group">
        <h4 class="date-label">{{ dateLabel }}</h4>
        <div 
          v-for="item in group" 
          :key="item.id" 
          class="history-item"
          @click="$emit('select-history', item.id)"
        >
          <div class="item-content">
            <span class="item-title">{{ item.title }}</span>
            <span class="item-time">{{ formatTime(item.created_at) }}</span>
          </div>
          <button @click.stop="deleteItem(item.id)" class="delete-btn" title="ลบรายการนี้">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
          </button>
        </div>
      </div>
    </div>
    
    <div v-else class="loading-state">
        <div class="spinner"></div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'HistorySidebar',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      history: [],
      loading: false,
      baseUrl: 'http://127.0.0.1:8000'
    };
  },
  computed: {
    groupedHistory() {
      const groups = {};
      const today = new Date().toDateString();
      const yesterday = new Date(Date.now() - 86400000).toDateString();

      this.history.forEach(item => {
        const date = new Date(item.created_at);
        const dateStr = date.toDateString();
        
        let label = dateStr;
        if (dateStr === today) label = 'วันนี้';
        else if (dateStr === yesterday) label = 'เมื่อวานนี้';
        else label = date.toLocaleDateString('th-TH', { day: 'numeric', month: 'short', year: 'numeric' });

        if (!groups[label]) groups[label] = [];
        groups[label].push(item);
      });
      return groups;
    }
  },
  watch: {
    isOpen(newVal) {
      if (newVal) {
        this.fetchHistory();
      }
    }
  },
  methods: {
    async fetchHistory() {
      this.loading = true;
      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        const response = await axios.get(`${this.baseUrl}/api/history`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.history = response.data;
      } catch (error) {
        console.error("Failed to load history:", error);
      } finally {
        this.loading = false;
      }
    },
    async deleteItem(id) {
        if(!confirm('คุณต้องการลบรายการนี้ใช่หรือไม่?')) return;
        
      try {
        const token = localStorage.getItem('token');
        await axios.delete(`${this.baseUrl}/api/history/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.history = this.history.filter(item => item.id !== id);
      } catch (error) {
        console.error("Failed to delete item:", error);
      }
    },
    async confirmClearAll() {
        if(!confirm('คุณแน่ใจหรือไม่ที่จะลบประวัติทั้งหมด? การกระทำนี้ไม่สามารถย้อนกลับได้')) return;
        
        try {
            const token = localStorage.getItem('token');
            await axios.delete(`${this.baseUrl}/api/history`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            this.history = [];
        } catch (error) {
            console.error("Failed to clear history:", error);
        }
    },
    formatTime(dateString) {
      return new Date(dateString).toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' });
    }
  }
};
</script>

<style scoped>
.history-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: 280px;
  background: rgba(30, 30, 40, 0.85); /* Deep purple/dark base */
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.4);
  transform: translateX(-100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1000;
  color: #fff;
  display: flex;
  flex-direction: column;
}

.history-sidebar.open {
  transform: translateX(0);
}

.sidebar-header {
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  background: linear-gradient(135deg, #A78BFA 0%, #F472B6 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.close-btn {
  background: none;
  border: none;
  color: #9CA3AF;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: color 0.2s, background 0.2s;
}

.close-btn:hover {
  color: #fff;
  background: rgba(255,255,255,0.1);
}

.actions-header {
    padding: 0.75rem 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.clear-all-btn {
    background: transparent;
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #FCA5A5;
    font-size: 0.8rem;
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    width: 100%;
    justify-content: center;
    transition: all 0.2s;
}

.clear-all-btn:hover {
    background: rgba(239, 68, 68, 0.1);
    border-color: #EF4444;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

/* Scrollbar styling */
.history-list::-webkit-scrollbar {
  width: 6px;
}
.history-list::-webkit-scrollbar-track {
  background: transparent;
}
.history-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.date-label {
  font-size: 0.75rem;
  color: #9CA3AF;
  margin: 1rem 0 0.5rem 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.item-content {
  overflow: hidden;
  flex: 1;
  margin-right: 8px;
}

.item-title {
  display: block;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #E5E7EB;
}

.item-time {
  display: block;
  font-size: 0.75rem;
  color: #6B7280;
  margin-top: 2px;
}

.delete-btn {
  background: none;
  border: none;
  color: #6B7280;
  padding: 4px;
  cursor: pointer;
  opacity: 0; /* Hidden by default */
  transition: all 0.2s;
  border-radius: 4px;
}

.history-item:hover .delete-btn {
  opacity: 1; /* Show on hover */
}

.delete-btn:hover {
  color: #EF4444;
  background: rgba(239, 68, 68, 0.1);
}

.empty-state, .loading-state {
    padding: 2rem;
    text-align: center;
    color: #6B7280;
    font-size: 0.9rem;
}

.spinner {
    border: 3px solid rgba(255, 255, 255, 0.1);
    border-top: 3px solid #8B5CF6;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    animation: spin 1s linear infinite;
    margin: 0 auto;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
</style>
