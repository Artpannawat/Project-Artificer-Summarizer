<template>
  <div class="admin-dashboard card">
    <div class="dashboard-header">
      <h2>Admin Dashboard</h2>
      <div class="stats-container">
        <div class="stat-card">
          <span class="stat-value">{{ stats.total_users }}</span>
          <span class="stat-label">Total Users</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ stats.total_summaries }}</span>
          <span class="stat-label">Est. Summaries</span>
        </div>
        <div class="stat-card active">
          <span class="stat-value">System</span>
          <span class="stat-label">Status: Online</span>
        </div>
      </div>
    </div>

    <div class="users-section">
      <h3>User Management</h3>
      <div class="table-container">
        <table class="users-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Email</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>
                <div class="user-cell">
                  <div class="avatar-small">
                     <img v-if="user.avatar_url" :src="getAvatarUrl(user.avatar_url)" alt="avatar" @error="user.avatar_url = null" />
                     <div v-else class="avatar-placeholder">{{ user.username[0].toUpperCase() }}</div>
                  </div>
                  <span>{{ user.username }}</span>
                </div>
              </td>
              <td>
                <span class="role-badge" :class="user.role">{{ user.role }}</span>
              </td>
              <td>{{ user.email }}</td>
              <td>
                <button v-if="user.role !== 'admin'" @click="resetPassword(user.id)" class="action-btn warning" title="Reset Password">Reset</button>
                <button v-if="user.role !== 'admin'" @click="deleteUser(user.id)" class="action-btn danger" title="Delete">Ban</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? 'http://localhost:8000' : '');

export default {
  name: 'AdminDashboard',
  data() {
    return {
      stats: {
        total_users: 0,
        total_summaries: 0
      },
      users: []
    };
  },
  mounted() {
    this.fetchData();
  },
  methods: {
    getAvatarUrl(path) {
      if (!path) return '';
      if (path.startsWith('http') || path.startsWith('data:')) return path;
      return `${API_URL}${path}`;
    },
    async fetchData() {
      try {
        const token = localStorage.getItem('token');
        const headers = { Authorization: `Bearer ${token}` };
        
        const [statsRes, usersRes] = await Promise.all([
          axios.get(`${API_URL}/admin/stats`, { headers }),
          axios.get(`${API_URL}/admin/users`, { headers })
        ]);
        
        this.stats = statsRes.data;
        this.users = usersRes.data;
      } catch (error) {
        console.error("Admin Access Error:", error);
        alert("Failed to load Admin Data. Are you an Admin?");
      }
    },
    async resetPassword(userId) {
       if(!confirm("Reset password for this user to '1234'?")) return;
       try {
         const token = localStorage.getItem('token');
         await axios.post(`${API_URL}/admin/users/${userId}/reset-pass`, {}, {
            headers: { Authorization: `Bearer ${token}` }
         });
         alert("Password reset to '1234'");
       } catch (err) {
         alert("Failed to reset password");
       }
    },
    async deleteUser(userId) {
       if(!confirm("Are you sure you want to delete/ban this user?")) return;
       try {
         const token = localStorage.getItem('token');
         await axios.delete(`${API_URL}/admin/users/${userId}`, {
            headers: { Authorization: `Bearer ${token}` }
         });
         this.fetchData(); // Refresh list
       } catch (err) {
         alert("Failed to delete user");
       }
    }
  }
}
</script>

<style scoped>
.admin-dashboard {
  padding: 2rem;
  color: var(--text-color, #1e293b);
}

.dashboard-header {
  margin-bottom: 2rem;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.stat-card {
  background: var(--input-bg, #f8fafc);
  padding: 1.5rem;
  border-radius: 12px;
  text-align: center;
  border: 1px solid rgba(0,0,0,0.05);
}

.stat-value {
  display: block;
  font-size: 2.5rem;
  font-weight: 700;
  color: #3b82f6;
}

.stat-label {
  color: var(--text-muted);
  font-size: 0.9rem;
}

.table-container {
  overflow-x: auto;
  background: var(--input-bg, #f8fafc);
  border-radius: 12px;
  padding: 1rem;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th, .users-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.avatar-small {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  background: #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-small img {
  width: 100%;
  height: 100%;
}

.role-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 600;
}

.role-badge.admin {
  background: #dbeafe;
  color: #1e40af;
}

.role-badge.user {
  background: #f1f5f9;
  color: #64748b;
}

.action-btn {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  border: none;
  font-size: 0.8rem;
  cursor: pointer;
  margin-right: 0.5rem;
}

.warning { background: #fef3c7; color: #92400e; }
.danger { background: #fee2e2; color: #b91c1c; }

:global([data-theme='dark']) .stat-card,
:global([data-theme='dark']) .table-container {
  background: #1f2937;
  border-color: #374151;
}

:global([data-theme='dark']) .users-table th,
:global([data-theme='dark']) .users-table td {
  border-bottom-color: #374151;
  color: #f3f4f6;
}
</style>
