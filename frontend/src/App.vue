<template>
    <div id="app" class="artificer-container">
      <header class="artificer-header">
        <div class="logo-section">
          <span class="logo">Artificer</span>
        </div>
        <div class="title-section">
          <h1>เครื่องมือการสรุปบทความ</h1>
        </div>
        <div class="user-profile" @click="toggleDropdown">
          <img src="/user-icon.svg" alt="User" class="user-icon">
          <ul class="profile-dropdown" v-show="showDropdown">
            <li v-if="isAuthenticated">Profile</li>
            <li v-if="isAuthenticated" @click="logout">Logout</li>
            <li v-else>
              <a href="#" @click="currentView = 'Login'">Login</a> /
              <a href="#" @click="currentView = 'Register'">Register</a>
            </li>
          </ul>
        </div>
      </header>
      <main class="main-content">
        <h2 class="prompt">Ask our AI anything</h2>
        
        <div v-if="isAuthenticated">
          <Summarizer />
        </div>
        <div v-else>
          <Login v-if="currentView === 'Login'" @authenticated="onAuthenticated" @switch-to-register="currentView = 'Register'" />
          <Register v-if="currentView === 'Register'" @authenticated="onAuthenticated" @switch-to-login="currentView = 'Login'" />
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
    },
    methods: {
      checkAuth() {
        this.isAuthenticated = !!localStorage.getItem('token');
      },
      onAuthenticated() {
        this.isAuthenticated = true;
      },
      toggleDropdown() {
        this.showDropdown = !this.showDropdown;
      },
      logout() {
        localStorage.removeItem('token');
        this.isAuthenticated = false;
      }
    }
  }
  </script>
  
  <style>
  @import './assets/styles.css';
  
  /* Styles for auth forms */
  .auth-card {
    background: linear-gradient(135deg, #f0f4ff, #e6e8fa);
    padding: 40px;
    border-radius: 15px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
    text-align: center;
  }
  
  .auth-card h2 {
    color: #5d5dff;
    margin-bottom: 25px;
  }
  
  .auth-card input {
    width: 100%;
    padding: 12px;
    margin-bottom: 15px;
    border: 1px solid #ddd;
    border-radius: 8px;
    box-sizing: border-box;
  }
  
  .auth-button {
    background: linear-gradient(90deg, #9b59b6, #d247d7);
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 20px;
    cursor: pointer;
    font-weight: bold;
    width: 100%;
  }
  </style>