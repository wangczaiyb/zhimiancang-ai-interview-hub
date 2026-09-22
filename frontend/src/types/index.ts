export interface UserInfo {
  id: number
  email: string
  phone?: string
  account_type: 'PERSONAL' | 'ENTERPRISE' | 'ADMIN'
  status: string
  roles: string[]
  name: string
  avatar_url?: string
  company_id?: number
  company_name?: string
  profile_type?: string
  target_job_title?: string
}

export interface JobItem {
  id: number
  company_id: number
  company_name: string
  company_logo?: string
  department_name?: string
  title: string
  category: string
  city: string
  salary_min: number
  salary_max: number
  education: string
  experience: string
  type: string
  headcount: number
  description: string
  duties: string
  requirements: string
  bonus?: string
  skills_required: string
  skills: { skill_name: string; level: string; required: boolean }[]
  competencies: { competency_name: string; weight: number; required_score: number }[]
  status: string
  reject_reason?: string
  is_favorited?: boolean
  match_score?: number
  applications_count?: number
  created_at: string
}

export interface ResumeItem {
  id: number
  user_id: number
  name: string
  is_default: boolean
  file_url?: string
  file_name?: string
  target_job_title: string
  completeness: number
  created_at: string
  educations: { school: string; major: string; degree: string; start_date: string; end_date: string }[]
  projects: { name: string; role: string; description: string; technologies: string; start_date: string; end_date: string }[]
  work_experiences: { company: string; title: string; description: string; start_date: string; end_date: string }[]
  skills: { skill_name: string; level: string; evidence?: string }[]
}

export interface ApplicationItem {
  id: number
  user_id: number
  candidate_name: string
  candidate_avatar?: string
  candidate_school?: string
  candidate_education?: string
  candidate_major?: string
  job_id: number
  job_title: string
  company_id: number
  company_name: string
  resume_id: number
  status: string
  match_score: number
  reject_reason?: string
  withdraw_reason?: string
  tags: string[]
  has_interview_invitation?: boolean
  invitation_status?: string
  created_at: string
  updated_at: string
  status_history: { id: number; from_status?: string; to_status: string; note?: string; created_at: string }[]
}

export interface InterviewSession {
  id: number
  user_id: number
  company_id?: number
  job_id?: number
  job_title: string
  type: string
  mode: string
  difficulty: string
  status: string
  current_question_seq: number
  total_questions: number
  duration_minutes: number
  questions: {
    id: number
    seq: number
    stage: string
    skill_name: string
    text: string
    difficulty: string
    user_answer?: string
    evaluation?: any
  }[]
  current_question?: {
    id: number
    seq: number
    stage: string
    skill_name: string
    text: string
    difficulty: string
  }
}

export interface InterviewReportData {
  id: number
  interview_id: number
  job_title?: string
  interview_type?: string
  duration_minutes?: number
  total_score: number
  performance_level: string
  dimension_scores: Record<string, number>
  strengths: string[]
  weaknesses: string[]
  suggestions: string[]
  summary: string
  status: string
  created_at: string
  questions_analysis: {
    seq: number
    question: string
    answer: string
    score: number
    evidence: string[]
    weaknesses: string[]
    missing_knowledge: string[]
    suggestions: string[]
  }[]
}
