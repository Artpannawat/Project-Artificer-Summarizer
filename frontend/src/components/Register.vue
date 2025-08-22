<template>
    <div class="auth-card">
      <h2>ลงทะเบียน</h2>
      <form @submit.prevent="register">
        <input v-model="username" type="text" placeholder="ชื่อผู้ใช้" required />
        <input v-model="email" type="email" placeholder="อีเมล" required />
        <input v-model="password" type="password" placeholder="รหัสผ่าน" required />
        <button type="submit" class="auth-button">ลงทะเบียน</button>
      </form>
      <p v-if="message">{{ message }}</p>
      <p>มีบัญชีอยู่แล้ว? <a href="#" @click="$emit('switch-to-login')">เข้าสู่ระบบ</a></p>
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
        backendUrl: 'http://127.0.0.1:8000',
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
  /* You can add auth-card styles here or in App.vue */
  </style>