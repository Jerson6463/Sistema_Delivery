import axios from 'axios'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const authStore = useAuthStore()

  if (authStore.accessToken) {
    config.headers.Authorization = `Bearer ${authStore.accessToken}`
  }

  return config
})

let refreshPromise = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status
    const authStore = useAuthStore()

    if (status !== 401 || originalRequest?._retry || !authStore.refreshToken) {
      if (status === 401) {
        authStore.logout()
        router.push({ name: 'login', query: { redirect: router.currentRoute.value.fullPath } })
      }

      return Promise.reject(error)
    }

    originalRequest._retry = true

    try {
      refreshPromise ||= authStore.refreshAccessToken()
      const accessToken = await refreshPromise
      refreshPromise = null

      originalRequest.headers.Authorization = `Bearer ${accessToken}`
      return api(originalRequest)
    } catch (refreshError) {
      refreshPromise = null
      authStore.logout()
      router.push({ name: 'login', query: { redirect: router.currentRoute.value.fullPath } })
      return Promise.reject(refreshError)
    }
  },
)

export default api
