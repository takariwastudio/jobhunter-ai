export interface CV {
  id: string
  original_filename: string
  file_path: string
  mime_type?: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  error_message?: string
  created_at: string
  updated_at?: string
}

export interface ExperienceItem {
  company: string
  title: string
  start_date?: string
  end_date?: string
  description?: string
}

export interface EducationItem {
  institution: string
  degree: string
  start_date?: string
  end_date?: string
}

export interface SkillItem {
  name: string
  category: 'technical' | 'soft'
  level?: 'beginner' | 'intermediate' | 'advanced' | 'expert'
}

export interface LanguageItem {
  name: string
  level: 'basic' | 'conversational' | 'fluent' | 'native'
}

export interface ParsedProfile {
  full_name?: string
  email?: string
  phone?: string
  summary?: string
  experience: ExperienceItem[]
  education: EducationItem[]
  skills: SkillItem[]
  languages: LanguageItem[]
  raw_text?: string
}

export interface Job {
  id: string
  title: string
  company: string
  description: string
  location?: string
  salary_range?: string
  job_type?: string
  remote?: boolean
  source: string
  source_url?: string
  posted_date?: string
  created_at: string
}

export interface JobSearchResult {
  external_id: string
  title: string
  company: string
  description: string
  source: 'adzuna' | 'jsearch'
  source_url: string
  location?: string
  salary_range?: string
  job_type?: string
  remote?: boolean
  posted_date?: string
  is_saved: boolean
}

export interface SavedJob {
  id: string
  external_id: string
  source: string
  title: string
  company: string
  description: string
  location?: string
  salary_range?: string
  job_type?: string
  remote?: boolean
  source_url?: string
  posted_date?: string
  saved_at: string
}

export interface JobSearchParams {
  q: string
  location?: string
  country?: string
  remote?: boolean
  page?: number
  limit?: number
  source?: 'adzuna' | 'jsearch' | 'all'
}

export interface User {
  id: string
  email: string | null
  phone: string | null
  display_name: string | null
  avatar_url: string | null
  provider: string
}

export interface ApiError {
  message: string
  detail?: string
}

export type MatchRecommendation = 'strong_match' | 'good_match' | 'partial_match' | 'weak_match'

export interface MatchScore {
  external_id: string
  score: number
  reasoning: string
  matching_skills: string[]
  missing_skills: string[]
  recommendation: MatchRecommendation
}

export interface MatchResponse {
  results: MatchScore[]
  profile_name: string | null
}
