// src/lib/api.ts
// import axios from "axios";

// export const api = axios.create({
//   baseURL: import.meta.env.VITE_API_BASE,
//   withCredentials: true,
// });

import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
})

// 🔑 THIS IS THE ONLY FIX
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
