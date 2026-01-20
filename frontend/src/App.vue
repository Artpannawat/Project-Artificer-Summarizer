<template>
  <div id="app" class="artificer-container">
    <!-- Modern Professional Navbar -->
    <nav class="modern-navbar">
      <div class="navbar-content">
        <div class="logo-section" @click="handleLogoClick" style="cursor: pointer;">
          <div class="logo-icon">
            <img src="/logo.png" alt="Artificer Logo" class="app-logo-img" />
          </div>
          <span class="logo-text">Artificer</span>
          
          <!-- History Toggle Button -->
          <button v-if="isAuthenticated && !isGuest" @click="toggleSidebar" class="history-toggle-btn" title="ประวัติการใช้งาน">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 8v4l3 3"></path>
                  <circle cx="12" cy="12" r="9"></circle>
              </svg>
          </button>
        </div>
        
        <div class="navbar-center">
          <h1 class="app-title">เครื่องมือการสรุปบทความ</h1>
          <p class="app-subtitle">AI-Powered Content Summarization</p>
        </div>
        
        <div class="right-section">
          <!-- Theme Toggle Switch -->
          <div class="theme-toggle" @click="toggleTheme" title="Toggle Theme">
            <div class="toggle-track" :class="{ 'dark': isDarkMode }">
              <div class="toggle-thumb">
                <svg v-if="!isDarkMode" width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="5" stroke="#F59E0B" stroke-width="2" fill="#F59E0B"/>
                  <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" stroke="#F59E0B" stroke-width="2"/>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="#A78BFA" stroke="#A78BFA" stroke-width="2"/>
                </svg>
              </div>
            </div>
          </div>

          <div class="user-profile" @click="toggleDropdown" ref="userProfile">
            <div class="user-avatar">
              <img v-if="currentUser.avatar_url" :src="getAvatarUrl(currentUser.avatar_url)" alt="User Avatar" class="avatar-img"/>
              <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/>
                <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="user-info" v-if="isAuthenticated">
              <span class="user-name">{{ currentUser.username || 'ผู้ใช้งาน' }}</span>
            </div>
            <div class="dropdown-arrow">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            
            <!-- Modern Dropdown Menu -->
            <div class="profile-dropdown" :class="{ 'show': showDropdown }">
              <div v-if="isAuthenticated" class="dropdown-content">
                <div class="dropdown-header">
                  <div class="user-avatar-large-container" @click.stop="triggerFileInput">
                    <div class="user-avatar-large">
                      <img v-if="currentUser.avatar_url" :src="getAvatarUrl(currentUser.avatar_url)" alt="User Avatar" class="avatar-img"/>
                      <svg v-else width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/>
                        <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" stroke="currentColor" stroke-width="2"/>
                      </svg>
                    </div>
                    <!-- Hover Effect Overlay -->
                    <div class="avatar-overlay">
                      <svg v-if="!isUploading" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                        <circle cx="12" cy="13" r="4"></circle>
                      </svg>
                      <div v-else class="upload-spinner"></div>
                    </div>
                    <input type="file" ref="fileInput" hidden @change="handleAvatarUpload" accept="image/png, image/jpeg">
                  </div>
                  <div class="user-details">
                    <span class="user-name-large">{{ currentUser.username || 'ผู้ใช้งาน' }}</span>
                    <span class="user-email">{{ currentUser.email || 'user@example.com' }}</span>
                  </div>
                </div>
                <div class="dropdown-divider"></div>
                <div v-if="isAdmin" class="dropdown-item" @click="currentView = 'AdminDashboard'; showDropdown = false">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M3 3h18v18H3z" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M3 9h18M9 21V9" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                  Admin Dashboard
                </div>
                <div class="dropdown-divider"></div>
                <div class="dropdown-item" @click="openChangePasswordModal">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                  เปลี่ยนรหัสผ่าน
                </div>
                <div class="dropdown-divider"></div>
                <div class="dropdown-item logout-item" @click="logout">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="1.5"/>
                    <polyline points="16,17 21,12 16,7" stroke="currentColor" stroke-width="1.5"/>
                    <line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                  ออกจากระบบ
                </div>
              </div>
              <div v-else class="dropdown-content">
                <div class="dropdown-item" @click="switchToLogin">
                  เข้าสู่ระบบ
                </div>
                <div class="dropdown-item" @click="switchToRegister">
                  ลงทะเบียน
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
    
    <HistorySidebar :is-open="isSidebarOpen" @close="isSidebarOpen = false" @select-history="handleHistorySelect" />

    <main class="main-content" :class="{ 'sidebar-open': isSidebarOpen }">
      <div class="content-header">
        <h2 class="main-prompt">Ask our AI anything</h2>
        <p class="main-description">ใช้ประสิทธิภาพของ AI เพื่อสรุปเนื้อหาของคุณอย่างรวดเร็วและแม่นยำ</p>
      </div>
      
      <div class="content-body">
        <div v-if="isAuthenticated" class="authenticated-content">
          <AdminDashboard v-if="currentView === 'AdminDashboard'" />
          <Summarizer v-else ref="summarizerComponent" />
        </div>
        <div v-else class="auth-content">
          <Login v-if="currentView === 'Login'" @authenticated="onAuthenticated" @switch-to-register="currentView = 'Register'" />
          <Register v-if="currentView === 'Register'" @authenticated="onAuthenticated" @switch-to-login="currentView = 'Login'" />
        </div>
      </div>
      
      <footer style="text-align: center; padding: 1rem; opacity: 0.6; font-size: 0.8rem;">
        System v2.0 DEV Pannawat (Robust Mode)
      </footer>
    </main>

    <!-- Change Password Modal -->
    <div v-if="showChangePasswordModal" class="modal-overlay" @click.self="closeChangePasswordModal">
      <div class="modal-content">
        <h3>เปลี่ยนรหัสผ่าน</h3>
        <form @submit.prevent="handleChangePassword">
          <div class="form-group">
            <label>รหัสผ่านปัจจุบัน</label>
            <input type="password" v-model="passwordForm.current_password" required placeholder="ระบุรหัสผ่านปัจจุบัน" />
          </div>
          <div class="form-group">
             <label>รหัสผ่านใหม่</label>
             <input type="password" v-model="passwordForm.new_password" required placeholder="ระบุรหัสผ่านใหม่ (อย่างน้อย 4 ตัวอักษร)" minlength="4" />
          </div>
          <div class="form-group">
             <label>ยืนยันรหัสผ่านใหม่</label>
             <input type="password" v-model="passwordForm.confirm_password" required placeholder="ยืนยันรหัสผ่านใหม่" />
          </div>
          <p v-if="passwordError" class="error-text">{{ passwordError }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeChangePasswordModal">ยกเลิก</button>
            <button type="submit" class="btn-confirm" :disabled="isChangingPassword">
               {{ isChangingPassword ? 'กำลังบันทึก...' : 'บันทึก' }}
            </button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script>
import Summarizer from './components/Summarizer.vue';
import HistorySidebar from './components/HistorySidebar.vue';
import AdminDashboard from './components/AdminDashboard.vue';
import Login from './components/Login.vue';
import Register from './components/Register.vue';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? 'http://localhost:8000' : '');

export default {
  name: 'App',
  components: {
    Summarizer,
    HistorySidebar,
    AdminDashboard,
    Login,
    Register
  },
  data() {
    return {
      isAuthenticated: false,
      currentView: 'Login',
      showDropdown: false,
      isSidebarOpen: false,
      isDarkMode: false,
      currentUser: {
        username: '',
        email: '',
        avatar_url: null
      },
      isUploading: false,
      showChangePasswordModal: false,
      isChangingPassword: false,
      passwordForm: {
        current_password: '',
        new_password: '',
        confirm_password: ''
      },
      passwordError: null
    };
  },
  computed: {
    isGuest() {
      return this.currentUser && (this.currentUser.username === 'Guest' || this.currentUser.email === '');
    },
    isAdmin() {
      return this.currentUser && this.currentUser.role === 'admin';
    }
  },
  created() {
    this.checkAuth();
    this.initTheme();
    // Close dropdown when clicking outside
    document.addEventListener('click', this.handleClickOutside);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside);
  },
  methods: {
    initTheme() {
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme === 'dark') {
        this.isDarkMode = true;
        document.documentElement.setAttribute('data-theme', 'dark');
      } else {
        this.isDarkMode = false;
        document.documentElement.removeAttribute('data-theme');
      }
    },
    toggleTheme() {
      this.isDarkMode = !this.isDarkMode;
      if (this.isDarkMode) {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
      } else {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
      }
    },
    checkAuth() {
      const token = localStorage.getItem('token');
      if (token) {
        this.isAuthenticated = true;
        this.fetchUserProfile();
      }
    },
    async fetchUserProfile() {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}/users/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.currentUser = response.data;
      } catch (error) {
        console.error('Error fetching profile:', error);
        if (error.response && error.response.status === 403) {
           this.logout();
        }
      }
    },
    onAuthenticated(status = 'authenticated') {
      if (status === 'guest') {
        this.isAuthenticated = true; // Allow access
        this.currentUser = { username: 'Guest', email: '', avatar_url: null };
      } else {
        this.isAuthenticated = true;
        this.showDropdown = false;
        this.fetchUserProfile();
      }
    },
    logout() {
      localStorage.removeItem('token');
      this.isAuthenticated = false;
      this.showDropdown = false;
      this.isSidebarOpen = false; // Close sidebar on logout
      this.currentUser = { username: '', email: '', avatar_url: null };
    },
    toggleDropdown() {
      this.showDropdown = !this.showDropdown;
    },
    handleClickOutside(event) {
      if (this.$refs.userProfile && !this.$refs.userProfile.contains(event.target)) {
        this.showDropdown = false;
      }
    },
    switchToLogin() {
      this.currentView = 'Login';
      this.showDropdown = false;
    },
    switchToRegister() {
      this.currentView = 'Register';
      this.showDropdown = false;
    },
    getAvatarUrl(path) {
      if (!path) return null;
      if (path.startsWith('http') || path.startsWith('data:')) return path;
      return `${API_URL}${path}`;
    },
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    async handleAvatarUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      if (file.size > 5 * 1024 * 1024) {
        alert('File size too large (Max 5MB)');
        return;
      }

      this.isUploading = true;
      const formData = new FormData();
      formData.append('file', file);

      try {
        const token = localStorage.getItem('token');
        const response = await axios.post(`${API_URL}/users/upload-avatar`, formData, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
        
        // Update local state immediately
        if (response.data.avatar_url.startsWith('data:')) {
           this.currentUser.avatar_url = response.data.avatar_url;
        } else {
           this.currentUser.avatar_url = response.data.avatar_url + `?t=${new Date().getTime()}`; // Cache buster for HTTP URLs only
        }
      } catch (error) {
        alert('Failed to upload avatar');
        console.error(error);
      } finally {
        this.isUploading = false;
      }
    },
    toggleSidebar() {
      this.isSidebarOpen = !this.isSidebarOpen;
    },
    async handleHistorySelect(historyId) {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}/api/history/${historyId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Use refs to call method on child component
        if (this.$refs.summarizerComponent) {
            this.$refs.summarizerComponent.loadFromHistory(response.data);
            // On mobile/tablet, close sidebar after selection
            if (window.innerWidth < 1024) {
                this.isSidebarOpen = false;
            }
        }
      } catch (error) {
        console.error("Failed to load history details:", error);
      }
    },
    openChangePasswordModal() {
      this.showChangePasswordModal = true;
      this.showDropdown = false;
      this.passwordError = null;
      this.passwordForm = { current_password: '', new_password: '', confirm_password: '' };
    },
    closeChangePasswordModal() {
      this.showChangePasswordModal = false;
    },
    async handleChangePassword() {
      this.passwordError = null;
      if (this.passwordForm.new_password !== this.passwordForm.confirm_password) {
        this.passwordError = "รหัสผ่านใหม่ไม่ตรงกัน";
        return;
      }
      
      this.isChangingPassword = true;
      try {
        const token = localStorage.getItem('token');
        await axios.post(`${API_URL}/users/change-password`, {
             current_password: this.passwordForm.current_password,
             new_password: this.passwordForm.new_password
        }, {
           headers: { Authorization: `Bearer ${token}` }
        });
        
        alert("เปลี่ยนรหัสผ่านสำเร็จ!");
        this.closeChangePasswordModal();
      } catch (error) {
        this.passwordError = error.response?.data?.detail || "เกิดข้อผิดพลาดในการเปลี่ยนรหัสผ่าน";
      } finally {
        this.isChangingPassword = false;
      }
    },
    handleLogoClick() {
      if (this.isAuthenticated) {
        this.currentView = 'Summarizer';
        this.isSidebarOpen = false;
      }
    }
  }
}
</script>

<style>
@import './assets/styles.css';

.history-toggle-btn {
    background: transparent;
    border: none;
    color: white; /* Contrast against navbar gradient? No, navbar is transparent/glass? Wait. */
    /* Navbar text seems to be dark or light depending on theme? Logo text is "Artificer". */
    /* Let's check navbar styling in original file. */
    /* .logo-text is black/dark. */
    /* I'll start with inheriting color. */
    color: inherit;
    cursor: pointer;
    padding: 8px;
    /* margin-left: 1rem; -- Removed to rely on .logo-section gap */
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;
}

.history-toggle-btn:hover {
    background: rgba(0,0,0,0.05);
}

:global([data-theme='dark']) .history-toggle-btn {
    color: #fff;
}
:global([data-theme='dark']) .history-toggle-btn:hover {
    background: rgba(255,255,255,0.1);
}

/* Adjust main content when sidebar is open (Desktop) */
@media (min-width: 1024px) {
    .main-content {
        transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .main-content.sidebar-open {
        margin-left: 280px;
    }
}


.right-section {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

/* Theme Toggle */
.theme-toggle {
  cursor: pointer;
  padding: 4px;
}

.toggle-track {
  width: 48px;
  height: 24px;
  background-color: #E2E8F0;
  border-radius: 20px;
  position: relative;
  transition: background-color 0.3s ease;
  display: flex;
  align-items: center;
  padding: 2px;
}

.toggle-track.dark {
  background-color: #4B5563;
}

.toggle-thumb {
  width: 20px;
  height: 20px;
  background-color: white;
  border-radius: 50%;
  position: absolute;
  left: 2px;
  transition: transform 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.toggle-track.dark .toggle-thumb {
  transform: translateX(24px);
  background-color: #1F2937;
}

/* Avatar Styling */
.user-avatar-large-container {
  position: relative;
  width: 64px;
  height: 64px;
  margin-right: 1rem;
  cursor: pointer;
  border-radius: 50%;
  overflow: hidden;
}

.user-avatar-large {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--background-main);
  border-radius: 50%;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
  backdrop-filter: blur(2px);
}

.user-avatar-large-container:hover .avatar-overlay {
  opacity: 1;
}

.upload-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid white;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}


.app-logo-img {
  width: 48px;
  height: auto;
  margin-right: 12px; /* Spacing next to text */
  display: block;
}

@media (max-width: 640px) {
  .app-title {
    font-size: 1.5rem !important;
    text-align: center;
    line-height: 1.2;
    margin-bottom: 0.5rem;
  }
  
  .app-subtitle {
    font-size: 0.9rem !important;
    text-align: center;
    padding: 0 1rem;
    display: block !important; /* Force show, but smaller */
    opacity: 0.9;
  }

  .logo-text {
    display: none;
  }

  .navbar-content {
    padding: 0 0.5rem;
  }
  
  .right-section {
    gap: 0.5rem;
  }

  .logo-section {
    flex: 0 0 auto;
  }

  .navbar-center {
    display: none !important;
  }
  
  .modern-navbar {
      border-bottom: none !important;
  }
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: var(--card-bg, white);
  padding: 2rem;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: var(--text-color, #1e293b);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: var(--text-muted, #64748b);
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: var(--input-bg, #f8fafc);
  color: var(--text-color, #1e293b);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-cancel {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-muted);
}

.btn-confirm {
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-confirm:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-text {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

:global([data-theme='dark']) .modal-content {
   background: #1f2937;
}
:global([data-theme='dark']) .form-group input {
   background: #374151;
   border-color: #4b5563;
   color: white;
}
</style>