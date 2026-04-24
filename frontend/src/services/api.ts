/// <reference types="vite/client" />
import axios, { AxiosError } from 'axios'
import toast from 'react-hot-toast'
import type { CV, ParsedProfile, ApiError, JobSearchResult, JobSearchParams, SavedJob, MatchResponse } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true, // always send httpOnly auth cookies
})

let _isRefreshing = false
let _refreshQueue: Array<() => void> = []

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const original = error.config

    if (error.response?.status === 401 && original && !original.url?.includes('/auth/')) {
      if (_isRefreshing) {
        // Queue the request until refresh completes
        return new Promise((resolve) => {
          _refreshQueue.push(() => resolve(api(original)))
        })
      }

      _isRefreshing = true
      try {
        await api.post('/auth/refresh')
        _refreshQueue.forEach((cb) => cb())
        _refreshQueue = []
        return api(original)
      } catch {
        _refreshQueue = []
        globalThis.location.href = '/login'
        throw error
      } finally {
        _isRefreshing = false
      }
    }

    // Don't toast on auth-related endpoints — callers handle those
    if (!original?.url?.includes('/auth/')) {
      const message = error.response?.data?.detail || error.response?.data?.message || 'Error desconocido'
      toast.error(message)
    }

    throw error
  }
)

// CV API
export const cvApi = {
  upload: async (file: File): Promise<CV> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<CV>('/cvs/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
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

// Job Search API
export const jobApi = {
  search: async (params: JobSearchParams): Promise<JobSearchResult[]> => {
    const response = await api.get<JobSearchResult[]>('/jobs/search', { params })
    return response.data
  },

  save: async (job: Omit<SavedJob, 'id' | 'saved_at'>): Promise<SavedJob> => {
    const response = await api.post<SavedJob>('/jobs/save', job)
    return response.data
  },

  unsave: async (externalId: string): Promise<void> => {
    await api.delete(`/jobs/save/${externalId}`)
  },

  getSaved: async (): Promise<SavedJob[]> => {
    const response = await api.get<SavedJob[]>('/jobs/saved')
    return response.data
  },
}

// Match API
export const matchApi = {
  matchJobs: async (
    cvId: string,
    jobs: Array<{ external_id: string; title: string; company: string; description: string }>
  ): Promise<MatchResponse> => {
    const response = await api.post<MatchResponse>('/match/jobs', { cv_id: cvId, jobs })
    return response.data
  },
}
