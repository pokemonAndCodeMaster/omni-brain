import axios from 'axios'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 20_000,
})

http.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    console.error('[HTTP ERROR]', error)
    return Promise.reject(error)
  },
)
