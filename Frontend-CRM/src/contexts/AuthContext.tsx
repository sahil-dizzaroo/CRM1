import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
// import axios from 'axios'
import { api } from '../lib/api'

interface User {
  user_id: string
  email: string
  name?: string
  role: string
  is_privileged: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  signup: (user_id: string, name: string, email: string, password: string, role?: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// interface AuthProviderProps {
//   children: ReactNode
//   apiBase: string
// }
interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Load token and user from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token')
    const storedUser = localStorage.getItem('auth_user')
    
    if (storedToken && storedUser) {
      setToken(storedToken)
      try {
        setUser(JSON.parse(storedUser))
        // Verify token is still valid by fetching current user
        // axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`
        // axios.get(`${apiBase}/auth/me`)
        api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`
        api.get('/auth/me')

          .then(response => {
            setUser(response.data)
            localStorage.setItem('auth_user', JSON.stringify(response.data))
          })
          .catch(() => {
            // Token invalid, clear auth
            logout()
          })
      } catch (e) {
        console.error('Error parsing stored user:', e)
        logout()
      }
    }
    setLoading(false)
  }, [])

  // Set axios default authorization header when token changes
  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete api.defaults.headers.common['Authorization']
    }
  }, [token])

  const login = async (email: string, password: string) => {
    try {
      const formData = new FormData()
      formData.append('username', email)  // OAuth2PasswordRequestForm uses 'username'
      formData.append('password', password)
      
      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      const { access_token, user: userData } = response.data
      setToken(access_token)
      setUser(userData)
      localStorage.setItem('auth_token', access_token)
      localStorage.setItem('auth_user', JSON.stringify(userData))
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed')
    }
  }

  const signup = async (user_id: string, name: string, email: string, password: string, role: string = 'participant') => {
    try {
      const response = await api.post('/auth/signup', {

        user_id,
        name,
        email,
        password,
        role
      })
      
      const { access_token, user: userData } = response.data
      setToken(access_token)
      setUser(userData)
      localStorage.setItem('auth_token', access_token)
      localStorage.setItem('auth_user', JSON.stringify(userData))
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Signup failed')
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    delete api.defaults.headers.common['Authorization']
  }

  return (
    <AuthContext.Provider value={{ user, token, login, signup, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

