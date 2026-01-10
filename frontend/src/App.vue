<template>
  <div id="app" class="artificer-container">
    <!-- Modern Professional Navbar -->
    <nav class="modern-navbar">
      <div class="navbar-content">
        <div class="logo-section">
          <div class="logo-icon">
          <div class="logo-icon">
            <img src="/logo.png" alt="Artificer Logo" class="app-logo-img" />
          </div>
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
          <Summarizer ref="summarizerComponent" />
        </div>
        <div v-else class="auth-content">
          <Login v-if="currentView === 'Login'" @authenticated="onAuthenticated" @switch-to-register="currentView = 'Register'" />
          <Register v-if="currentView === 'Register'" @authenticated="onAuthenticated" @switch-to-login="currentView = 'Login'" />
        </div>
      </div>
      
      <footer style="text-align: center; padding: 1rem; opacity: 0.6; font-size: 0.8rem;">
        System v1.6 (UI Validated)
      </footer>
    </main>
  </div>
</template>

<script>
import Summarizer from './components/Summarizer.vue';
import HistorySidebar from './components/HistorySidebar.vue';
import Login from './components/Login.vue';
import Register from './components/Register.vue';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? 'http://localhost:8000' : '');

export default {
  name: 'App',
  components: {
    Summarizer,
    HistorySidebar,
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
      isUploading: false
    };
  },
  computed: {
    isGuest() {
      return this.currentUser && (this.currentUser.username === 'Guest' || this.currentUser.email === '');
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
      if (path.startsWith('http')) return path;
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
        this.currentUser.avatar_url = response.data.avatar_url + `?t=${new Date().getTime()}`; // Cache buster
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
</style>