/// <reference types="vite/client" />
import axios, { AxiosError } from 'axios'
import toast from 'react-hot-toast'
import type { CV, ParsedProfile, ApiError } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const message = error.response?.data?.detail || error.response?.data?.message || 'Error desconocido'
    toast.error(message)
    return Promise.reject(error)
  }
)

// CV API
export const cvApi = {
  upload: async (file: File): Promise<CV> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post<CV>('/cvs/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  parse: async (cvId: string): Promise<ParsedProfile> => {
    const response = await api.post<ParsedProfile>(`/cvs/${cvId}/parse`)
    return response.data
  },

  getProfile: async (cvId: string): Promise<ParsedProfile> => {
    const response = await api.get<ParsedProfile>(`/cvs/${cvId}/profile`)
    return response.data
  },

  updateProfile: async (cvId: string, profile: ParsedProfile): Promise<ParsedProfile> => {
    const response = await api.put<ParsedProfile>(`/cvs/${cvId}/profile`, profile)
    return response.data
  },

  list: async (): Promise<CV[]> => {
    const response = await api.get<CV[]>('/cvs/')
    return response.data
  },

  delete: async (cvId: string): Promise<void> => {
    await api.delete(`/cvs/${cvId}`)
  },
}
