<template>
    <div class="auth-card">
      <div class="auth-header">
         <h2>สร้างบัญชีใหม่</h2> 
         <p class="auth-subtitle">สมัครสมาชิกเพื่อเริ่มต้นใช้งาน Artificer AI</p>
      </div>

      <form @submit.prevent="register" class="auth-form">
        <div class="input-group">
            <input v-model="username" type="text" placeholder="ชื่อผู้ใช้" required class="modern-input" />
        </div>
        <div class="input-group">
            <input v-model="email" type="email" placeholder="อีเมล" required class="modern-input" />
        </div>
        <div class="input-group">
            <input v-model="password" type="password" placeholder="รหัสผ่าน" required class="modern-input" />
        </div>
        <button type="submit" class="auth-button">สมัครสมาชิก</button>
      </form>
      <p v-if="message" class="error-text">{{ message }}</p>

      <div class="login-link">
        <p>มีบัญชีอยู่แล้ว? <a href="#" @click="$emit('switch-to-login')">เข้าสู่ระบบ</a></p>
      </div>
    </div>
  </template>
  
  <script>
  import axios from 'axios';
  
  export default {
    name: 'Register',
    data() {
      return {
        username: '',
        email: '',
        password: '',
        message: '',
        backendUrl: import.meta.env.VITE_API_URL || ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? 'http://127.0.0.1:8000' : ''),
      };
    },
    methods: {
      async register() {
        try {
          const response = await axios.post(`${this.backendUrl}/register`, {
            username: this.username,
            email: this.email,
            password: this.password,
          });
          localStorage.setItem('token', response.data.access_token);
          this.message = 'ลงทะเบียนสำเร็จ! กำลังเข้าสู่ระบบ...';
          this.$emit('authenticated');
        } catch (error) {
          this.message = error.response?.data?.detail || 'เกิดข้อผิดพลาดในการลงทะเบียน';
        }
      },
    },
  };
  </script>
  
  <style scoped>
  .auth-card {
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
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
  }

  .auth-subtitle {
      color: #6B7280;
      font-size: 0.95rem;
  }

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
      color: #1F2937;
  }

  /* Dark Mode Overrides for Input */
  :global([data-theme='dark']) .modern-input {
      background: #1E293B;
      border-color: #4B5563;
      color: #F3F4F6;
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

  .error-text {
      color: #EF4444;
      font-size: 0.875rem;
      margin-top: 0.5rem;
  }

  .login-link {
      margin-top: 1.5rem;
      font-size: 0.9rem;
      color: #6B7280;
  }
  
  .login-link a {
      color: #8B5CF6;
      text-decoration: none;
      font-weight: 600;
  }

  .login-link a:hover {
      text-decoration: underline;
  }
  </style>