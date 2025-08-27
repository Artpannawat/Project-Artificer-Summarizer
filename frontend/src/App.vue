<template>
    <div id="app" class="artificer-container">
      <!-- Modern Professional Navbar -->
      <nav class="modern-navbar">
        <div class="navbar-content">
          <div class="logo-section">
            <div class="logo-icon">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="16" cy="16" r="16" fill="url(#gradient1)"/>
                <path d="M12 10h8l-2 6h2l-6 8 2-8h-2l-2-6z" fill="white"/>
                <defs>
                  <linearGradient id="gradient1" x1="0" y1="0" x2="32" y2="32">
                    <stop offset="0%" stop-color="#8B5CF6"/>
                    <stop offset="100%" stop-color="#A855F7"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <span class="logo-text">Artificer</span>
          </div>
          
          <div class="navbar-center">
            <h1 class="app-title">เครื่องมือการสรุปบทความ</h1>
            <p class="app-subtitle">AI-Powered Content Summarization</p>
          </div>
          
          <div class="user-profile" @click="toggleDropdown" ref="userProfile">
            <div class="user-avatar">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/>
                <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="user-info" v-if="isAuthenticated">
              <span class="user-name">ผู้ใช้งาน</span>
              <span class="user-status">ออนไลน์</span>
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
                  <div class="user-avatar-large">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/>
                      <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <div class="user-details">
                    <span class="user-name-large">ผู้ใช้งาน</span>
                    <span class="user-email">user@example.com</span>
                  </div>
                </div>
                <div class="dropdown-divider"></div>
                <div class="dropdown-item" @click="viewProfile">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                  โปรไฟล์
                </div>
                <div class="dropdown-item" @click="viewSettings">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                  การตั้งค่า
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
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" stroke="currentColor" stroke-width="1.5"/>
                    <polyline points="10,17 15,12 10,7" stroke="currentColor" stroke-width="1.5"/>
                    <line x1="15" y1="12" x2="3" y2="12" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                  เข้าสู่ระบบ
                </div>
                <div class="dropdown-item" @click="switchToRegister">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="1.5"/>
                    <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="1.5"/>
                    <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="1.5"/>
                    <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                  ลงทะเบียน
                </div>
              </div>
            </div>
          </div>
        </div>
      </nav>
      
      <main class="main-content">
        <div class="content-header">
          <h2 class="main-prompt">Ask our AI anything</h2>
          <p class="main-description">ใช้ประสิทธิภาพของ AI เพื่อสรุปเนื้อหาของคุณอย่างรวดเร็วและแม่นยำ</p>
        </div>
        
        <div class="content-body">
          <div v-if="isAuthenticated" class="authenticated-content">
            <Summarizer />
          </div>
          <div v-else class="auth-content">
            <Login v-if="currentView === 'Login'" @authenticated="onAuthenticated" @switch-to-register="currentView = 'Register'" />
            <Register v-if="currentView === 'Register'" @authenticated="onAuthenticated" @switch-to-login="currentView = 'Login'" />
          </div>
        </div>
      </main>
    </div>
  </template>
  
  <script>
  import Summarizer from './components/Summarizer.vue';
  import Login from './components/Login.vue';
  import Register from './components/Register.vue';
  
  export default {
    name: 'App',
    components: {
      Summarizer,
      Login,
      Register
    },
    data() {
      return {
        isAuthenticated: false,
        currentView: 'Login', // Start with the login view
        showDropdown: false
      };
    },
    created() {
      this.checkAuth();
      // Close dropdown when clicking outside
      document.addEventListener('click', this.handleClickOutside);
    },
    beforeUnmount() {
      document.removeEventListener('click', this.handleClickOutside);
    },
    methods: {
      checkAuth() {
        this.isAuthenticated = !!localStorage.getItem('token');
      },
      onAuthenticated() {
        this.isAuthenticated = true;
        this.showDropdown = false;
      },
      logout() {
        localStorage.removeItem('token');
        this.isAuthenticated = false;
        this.showDropdown = false;
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
      viewProfile() {
        // Placeholder for profile functionality
        console.log('View Profile clicked');
        this.showDropdown = false;
      },
      viewSettings() {
        // Placeholder for settings functionality
        console.log('View Settings clicked');
        this.showDropdown = false;
      }
    }
  }
  </script>
  
  <style>
  @import './assets/styles.css';
  
  /* Modern Auth Card Styles */
  .auth-card {
    background: var(--background-card);
    padding: 2.5rem;
    border-radius: 24px;
    box-shadow: var(--shadow-large);
    border: 1px solid var(--border-light);
    width: 100%;
    max-width: 450px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  
  .auth-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--primary-purple), var(--secondary-purple));
  }
  
  .auth-card h2 {
    color: var(--text-primary);
    margin: 0 0 2rem 0;
    font-size: 1.75rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--primary-purple), var(--secondary-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .auth-card input {
    width: 100%;
    padding: 1rem 1.25rem;
    margin-bottom: 1.25rem;
    border: 2px solid var(--border-light);
    border-radius: 12px;
    box-sizing: border-box;
    font-size: 1rem;
    transition: all 0.3s ease;
    background: rgba(139, 92, 246, 0.02);
  }
  
  .auth-card input:focus {
    outline: none;
    border-color: var(--primary-purple);
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
    background: rgba(139, 92, 246, 0.05);
  }
  
  .auth-card input::placeholder {
    color: var(--text-light);
  }
  
  .auth-button {
    background: linear-gradient(135deg, var(--primary-purple), var(--secondary-purple));
    color: white;
    border: none;
    padding: 1rem 2rem;
    border-radius: 12px;
    cursor: pointer;
    font-weight: 600;
    font-size: 1rem;
    width: 100%;
    transition: all 0.3s ease;
    box-shadow: var(--shadow-medium);
  }
  
  .auth-button:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-large);
  }
  
  .auth-button:active {
    transform: translateY(0);
  }
  
  .auth-card p {
    color: var(--text-secondary);
    margin: 1.5rem 0 0 0;
    font-size: 0.875rem;
  }
  
  .auth-card a {
    color: var(--primary-purple);
    text-decoration: none;
    font-weight: 600;
    transition: color 0.2s ease;
  }
  
  .auth-card a:hover {
    color: var(--secondary-purple);
    text-decoration: underline;
  }
  
  /* Animation for smooth transitions */
  .auth-content {
    animation: fadeInUp 0.6s ease-out;
  }
  
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(30px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  </style>