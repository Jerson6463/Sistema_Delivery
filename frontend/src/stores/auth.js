import axios from 'axios'
import { defineStore } from 'pinia'
import api from '@/services/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/'
const TOKEN_STORAGE_KEY = 'delivery_auth_tokens'

function getStoredTokens() {
  try {
    return JSON.parse(localStorage.getItem(TOKEN_STORAGE_KEY)) || {}
  } catch {
    return {}
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => {
    const tokens = getStoredTokens()

    return {
      accessToken: tokens.access || null,
      refreshToken: tokens.refresh || null,
      user: null,
      isBootstrapping: false,
    }
  },

  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken),
    role: (state) => state.user?.rol || state.user?.role || null,
  },

  actions: {
    persistTokens(tokens) {
      this.accessToken = tokens.access
      this.refreshToken = tokens.refresh
      localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens))
    },

    async login(credentials) {
      const { data } = await api.post('usuarios/login/', credentials)
      this.persistTokens(data)
      await this.fetchMe()
      return this.user
    },

    async fetchMe() {
      const { data } = await api.get('usuarios/me/')
      this.user = data
      return data
    },

    async bootstrapSession() {
      if (!this.accessToken || this.user || this.isBootstrapping) return

      this.isBootstrapping = true

      try {
        await this.fetchMe()
      } catch {
        this.logout()
      } finally {
        this.isBootstrapping = false
      }
    },

    async refreshAccessToken() {
      const { data } = await axios.post(`${API_BASE_URL}usuarios/login/refresh/`, {
        refresh: this.refreshToken,
      })

      this.persistTokens({
        access: data.access,
        refresh: data.refresh || this.refreshToken,
      })

      return data.access
    },

    logout() {
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      localStorage.removeItem(TOKEN_STORAGE_KEY)
    },
  },
})
