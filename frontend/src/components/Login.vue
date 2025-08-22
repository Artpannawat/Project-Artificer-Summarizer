<template>
    <div class="auth-card">
      <h2>เข้าสู่ระบบ</h2>
      <form @submit.prevent="login">
        <input v-model="email" type="email" placeholder="อีเมล" required />
        <input v-model="password" type="password" placeholder="รหัสผ่าน" required />
        <button type="submit" class="auth-button">เข้าสู่ระบบ</button>
      </form>
      <p v-if="message">{{ message }}</p>
      <p>ยังไม่มีบัญชี? <a href="#" @click="$emit('switch-to-register')">ลงทะเบียน</a></p>
    </div>
  </template>
  
  <script>
  import axios from 'axios';
  
  export default {
    name: 'Login',
    data() {
      return {
        email: '',
        password: '',
        message: '',
        backendUrl: 'http://127.0.0.1:8000',
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
    },
  };
  </script>
  
  <style scoped>
  /* You can add auth-card styles here or in App.vue */
  </style>