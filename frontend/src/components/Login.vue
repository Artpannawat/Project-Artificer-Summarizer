<template>
    <div class="auth-card">
      <div class="auth-header">
         <h2>ยินดีต้อนรับ</h2> 
         <p class="auth-subtitle">เข้าสู่ระบบเพื่อใช้งาน AI Summarizer</p>
      </div>

      <form @submit.prevent="login" class="auth-form">
        <div class="input-group">
            <input v-model="email" type="email" placeholder="อีเมล" required class="modern-input" />
        </div>
        <div class="input-group">
            <input v-model="password" type="password" placeholder="รหัสผ่าน" required class="modern-input" />
        </div>
        <button type="submit" class="auth-button">เข้าสู่ระบบ</button>
      </form>
      <p v-if="message" class="error-text">{{ message }}</p>
      
      <div class="divider">
        <span>หรือเข้าสู่ระบบด้วย</span>
      </div>

      <div class="social-login">
        <!-- Render Custom Google Button using the scoped slot -->
        <!-- Use popup-type="TOKEN" to explicitly request an Access Token, which our backend now supports -->
        <GoogleLogin :callback="handleGoogleCallback" popup-type="TOKEN">
          <button type="button" class="google-btn">
            <div class="google-icon-wrapper">
              <svg class="google-icon" viewBox="0 0 48 48">
                <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path>
                <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path>
                <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path>
                <path fill="#34A853" d="M24 48c6.48 0 11.95-2.09 15.81-5.73l-7.73-6c-2.15 1.45-4.92 2.3-8.08 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path>
              </svg>
            </div>
            <span class="google-btn-text">ดำเนินการต่อด้วย Google</span>
          </button>
        </GoogleLogin>
      </div>

      <div class="guest-section">
          <button type="button" class="guest-button" @click="continueAsGuest">
            <span>ทดลองใช้งานแบบ Guest</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </button>
      </div>

      <div class="register-link">
        <p>ยังไม่มีบัญชี? <a href="#" @click="$emit('switch-to-register')">ลงทะเบียนใหม่</a></p>
      </div>
    </div>
  </template>
  
  <script>
  import axios from 'axios';
  import { GoogleLogin } from 'vue3-google-login';
  
  export default {
    name: 'Login',
    components: {
        GoogleLogin
    },
    data() {
      return {
        email: '',
        password: '',
        message: '',
        backendUrl: import.meta.env.VITE_API_URL || ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? 'http://127.0.0.1:8000' : ''),
      };
    },
    methods: {
      async login() {
        try {
          const response = await axios.post(`${this.backendUrl}/login`, {
            email: this.email,
            password: this.password,
          });
          localStorage.setItem('token', response.data.access_token);
          this.message = 'เข้าสู่ระบบสำเร็จ! กำลังเปลี่ยนเส้นทาง...';
          this.$emit('authenticated');
        } catch (error) {
          this.message = error.response?.data?.detail || 'เกิดข้อผิดพลาดในการเข้าสู่ระบบ';
        }
      },
      async handleGoogleCallback(response) {
        try {
          // Send the JWT credential (ID Token) OR Access Token to the backend
          const token = response.credential || response.access_token;
          const result = await axios.post(`${this.backendUrl}/auth/google`, {
            token: token
          });
          localStorage.setItem('token', result.data.access_token);
          this.message = 'เข้าสู่ระบบสำเร็จ! กำลังเปลี่ยนเส้นทาง...';
          this.$emit('authenticated');
        } catch (error) {
          console.error(error);
          this.message = 'Google Login Failed';
        }
      },
      continueAsGuest() {
        localStorage.removeItem('token');
        this.$emit('authenticated', 'guest');
      }
    },
  };
  </script>
  
  <style scoped>
  .auth-card {
      /* Inherits basic card styles but can be extended */
      text-align: center;
  }

  .auth-header {
      margin-bottom: 2rem;
  }

  .auth-header h2 {
      font-size: 1.75rem;
      font-weight: 700;
      background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%);
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
  }

  .auth-subtitle {
      color: #6B7280;
      font-size: 0.95rem;
  }

  /* Input Styles */
  .auth-form {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      margin-bottom: 1rem;
  }

  .modern-input {
      width: 100%;
      padding: 0.875rem 1rem;
      border: 1px solid #E5E7EB;
      border-radius: 12px;
      font-size: 0.95rem;
      transition: all 0.2s ease;
      background: #F9FAFB;
      color: #1F2937; /* Default light mode text */
  }

  /* Dark Mode Overrides for Input */
  :global([data-theme='dark']) .modern-input {
      background: #1E293B; /* Darker background */
      border-color: #4B5563;
      color: #F3F4F6; /* Light text */
  }
  
  :global([data-theme='dark']) .modern-input::placeholder {
      color: #9CA3AF;
  }

  .modern-input:focus {
      outline: none;
      border-color: #8B5CF6;
      background: white;
      box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  }

  :global([data-theme='dark']) .modern-input:focus {
      background: #0F172A;
      border-color: #A78BFA;
      box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.2);
  }

  .auth-button {
      width: 100%;
      padding: 0.875rem;
      border: none;
      border-radius: 12px;
      background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
      color: white;
      font-weight: 600;
      font-size: 1rem;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
  }

  .auth-button:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
  }

  /* Divider */
  .divider {
    display: flex;
    align-items: center;
    text-align: center;
    margin: 1.5rem 0;
    color: #9CA3AF;
  }
  .divider::before, .divider::after {
    content: '';
    flex: 1;
    border-bottom: 1px solid #E5E7EB;
  }
  :global([data-theme='dark']) .divider::before, 
  :global([data-theme='dark']) .divider::after {
    border-color: #374151;
  }

  .divider span {
    padding: 0 12px;
    font-size: 0.85rem;
    font-weight: 500;
  }

  /* Google Button */
  .social-login {
    display: flex;
    justify-content: center;
    width: 100%;
  }

  .google-btn {
      width: 100%;
      height: 48px;
      background-color: white;
      border-radius: 12px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05), 0 0 0 1px #E5E7EB;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s ease;
      position: relative;
      overflow: hidden;
  }

  :global([data-theme='dark']) .google-btn {
      background-color: #1E293B;
      box-shadow: 0 2px 4px rgba(0,0,0,0.2), 0 0 0 1px #374151;
  }

  .google-btn:hover {
      background-color: #F9FAFB;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08), 0 0 0 1px #D1D5DB;
      transform: translateY(-1px);
  }

  :global([data-theme='dark']) .google-btn:hover {
      background-color: #334155;
      box-shadow: 0 4px 12px rgba(0,0,0,0.4), 0 0 0 1px #4B5563;
  }

  .google-icon-wrapper {
      margin-right: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
  }

  .google-icon {
      width: 20px;
      height: 20px;
  }

  .google-btn-text {
      color: #374151;
      font-size: 0.95rem;
      font-weight: 500;
      font-family: inherit;
  }

  :global([data-theme='dark']) .google-btn-text {
      color: #F3F4F6;
  }

  /* Guest Button */
  .guest-section {
      margin-top: 1rem;
  }

  .guest-button {
    width: 100%;
    padding: 0.875rem;
    background: transparent;
    border: 2px dashed #D1D5DB;
    border-radius: 12px;
    color: #6B7280;
    cursor: pointer;
    font-size: 0.95rem;
    font-weight: 500;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    position: relative;
    overflow: hidden;
  }

  .guest-button:hover {
    border-color: #8B5CF6;
    color: #8B5CF6;
    background: rgba(139, 92, 246, 0.03);
  }

  .guest-button svg {
      transition: transform 0.3s ease;
  }

  .guest-button:hover svg {
      transform: translateX(3px);
  }

  .error-text {
      color: #EF4444;
      font-size: 0.875rem;
      margin-top: 0.5rem;
  }

  .register-link {
      margin-top: 1.5rem;
      font-size: 0.9rem;
      color: #6B7280;
  }
  
  .register-link a {
      color: #8B5CF6;
      text-decoration: none;
      font-weight: 600;
  }

  .register-link a:hover {
      text-decoration: underline;
  }
</style>