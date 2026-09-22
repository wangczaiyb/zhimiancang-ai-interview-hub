import client from './client'
import type { UserInfo, JobItem, ResumeItem, ApplicationItem, InterviewSession, InterviewReportData, PaperPreview } from '@/types'

export const authApi = {
  login: (data: any) => client.post('/auth/login', data),
  logout: () => client.post('/auth/logout'),
  getMe: () => client.get<any, UserInfo>('/auth/me'),
  registerPersonal: (data: any) => client.post('/auth/register/personal', data),
  registerEnterprise: (data: any) => client.post('/auth/register/enterprise', data),
  updateOnboarding: (data: any) => client.put('/personal/onboarding', data),
  changePassword: (data: any) => client.post('/auth/change-password', data),
  forgotPassword: (email: string) => client.post('/auth/forgot-password', { email }),
  resetPassword: (data: any) => client.post('/auth/reset-password', data),
}

export const publicApi = {
  getHome: () => client.get('/public/home'),
  getHotJobs: () => client.get('/jobs/hot'),
  getCompanyPublic: (id: number) => client.get(`/companies/${id}/public`),
  getCompanyJobs: (id: number) => client.get(`/companies/${id}/jobs`),
}

export const jobApi = {
  listJobs: (params: any) => client.get<any, { items: JobItem[]; total: number; page: number; total_pages: number }>('/jobs', { params }),
  getJobDetail: (id: number) => client.get<any, JobItem>(`/jobs/${id}`),
  favoriteJob: (id: number) => client.post(`/jobs/${id}/favorite`),
  unfavoriteJob: (id: number) => client.delete(`/jobs/${id}/favorite`),
  applyJob: (id: number, data: { resume_id: number }) => client.post(`/jobs/${id}/apply`, data),
}

export const resumeApi = {
  listResumes: () => client.get<any, ResumeItem[]>('/resumes'),
  getResume: (id: number) => client.get<any, ResumeItem>(`/resumes/${id}`),
  createResume: (data: any) => client.post<any, ResumeItem>('/resumes', data),
  updateResume: (id: number, data: any) => client.put<any, ResumeItem>(`/resumes/${id}`, data),
  deleteResume: (id: number) => client.delete(`/resumes/${id}`),
  parseResume: (id: number) => client.post(`/resumes/${id}/parse`),
  optimizeResume: (id: number) => client.post(`/resumes/${id}/optimize`),
  applyOptimization: (id: number) => client.post(`/resumes/${id}/optimize/apply`),
  uploadFile: (formData: FormData) => client.post('/files/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
}

export const applicationApi = {
  listApplications: (params?: any) => client.get<any, ApplicationItem[]>('/applications', { params }),
  getApplication: (id: number) => client.get<any, ApplicationItem>(`/applications/${id}`),
  withdrawApplication: (id: number, data: { reason: string }) => client.post(`/applications/${id}/withdraw`, data),
  acceptInvitation: (id: number) => client.post(`/interview-invitations/${id}/accept`),
  declineInvitation: (id: number) => client.post(`/interview-invitations/${id}/decline`),
}

export const personalApi = {
  getDashboard: () => client.get('/personal/dashboard'),
  getRecommendedJobs: () => client.get('/personal/jobs/recommended'),
  getJobMatch: (jobId: number) => client.get(`/personal/job-match/${jobId}`),
  getAssessment: (jobId?: number) => client.get('/personal/assessment', { params: { job_id: jobId } }),
  getCompetencies: () => client.get('/personal/competencies'),
  getGrowth: (period?: string) => client.get('/personal/growth', { params: { period } }),
  getLearningPlan: () => client.get('/learning/plans/current'),
  regenerateLearningPlan: (data?: any) => client.post('/learning/plans/generate', data || {}),
  completeTask: (id: number) => client.post(`/learning/tasks/${id}/complete`),
  getProfile: () => client.get('/personal/profile'),
  updateProfile: (data: any) => client.patch('/personal/profile', data),
  getNotifications: () => client.get('/notifications'),
  markNotificationRead: (id: number) => client.patch(`/notifications/${id}/read`),
  markAllNotificationsRead: () => client.post('/notifications/read-all'),
  getNotificationPreferences: () => client.get('/notifications/preferences'),
  updateNotificationPreferences: (data: any) => client.patch('/notifications/preferences', data),
  getConsents: () => client.get('/consents'),
  revokeConsent: (id: number) => client.delete(`/consents/${id}`),
  getSessions: () => client.get('/security/sessions'),
  revokeSession: (id: string) => client.delete(`/security/sessions/${id}`),
}

export const interviewApi = {
  createInterview: (data: any) => client.post<any, InterviewSession>('/interviews', data),
  listInterviews: () => client.get('/interviews'),
  getInterview: (id: number) => client.get<any, InterviewSession>(`/interviews/${id}`),
  startInterview: (id: number) => client.post(`/interviews/${id}/start`),
  pauseInterview: (id: number) => client.post(`/interviews/${id}/pause`),
  resumeInterview: (id: number) => client.post(`/interviews/${id}/resume`),
  answerQuestion: (id: number, data: any) => client.post(`/interviews/${id}/answer`, data),
  finishInterview: (id: number) => client.post(`/interviews/${id}/finish`),
  getReport: (id: number) => client.get<any, InterviewReportData>(`/interviews/${id}/report`),
  // 结构化题库组卷：配比查询 / 组卷预览 / 题库统计
  getPaperRatio: (params: { mode: string; total_questions: number }) =>
    client.get<any, { mode: string; ratio: Record<string, number>; allocated: Record<string, number>; bank_available: number; bank_ready: boolean }>('/interviews/paper-ratio', { params }),
  previewPaper: (data: any) => client.post<any, PaperPreview>('/interviews/paper-preview', data),
  getBankStats: () => client.get<any, { total: number; by_type: Record<string, number>; by_category: Record<string, number>; ready: boolean }>('/interviews/bank-stats'),
}

export const enterpriseApi = {
  getDashboard: () => client.get('/enterprise/dashboard'),
  listJobs: (params?: any) => client.get<any, JobItem[]>('/enterprise/jobs', { params }),
  createJob: (data: any) => client.post<any, JobItem>('/enterprise/jobs', data),
  getJob: (id: number) => client.get<any, JobItem>(`/enterprise/jobs/${id}`),
  updateJob: (id: number, data: any) => client.put<any, JobItem>(`/enterprise/jobs/${id}`, data),
  deleteJob: (id: number) => client.delete(`/enterprise/jobs/${id}`),
  submitJob: (id: number) => client.post(`/enterprise/jobs/${id}/submit`),
  pauseJob: (id: number) => client.post(`/enterprise/jobs/${id}/pause`),
  resumeJob: (id: number) => client.post(`/enterprise/jobs/${id}/resume`),
  closeJob: (id: number) => client.post(`/enterprise/jobs/${id}/close`),
  copyJob: (id: number) => client.post(`/enterprise/jobs/${id}/copy`),
  parseJD: (jd_text: string) => client.post('/enterprise/jobs/parse-jd', { jd_text }),
  listCandidates: (params?: any) => client.get<any, ApplicationItem[]>('/enterprise/candidates', { params }),
  getCandidate: (id: number) => client.get(`/enterprise/candidates/${id}`),
  advanceCandidate: (id: number, data: any) => client.post(`/enterprise/candidates/${id}/advance`, data),
  assignCandidate: (id: number, user_id: number) => client.post(`/enterprise/candidates/${id}/assign`, null, { params: { user_id } }),
  addTag: (id: number, tag: string) => client.post(`/enterprise/candidates/${id}/tags`, null, { params: { tag } }),
  getPipeline: (job_id?: number) => client.get('/enterprise/pipeline', { params: { job_id } }),
  listInterviews: () => client.get('/enterprise/interviews'),
  sendInvitation: (data: any) => client.post('/enterprise/interview-invitations', data),
  submitEvaluation: (id: number, data: any) => client.post(`/enterprise/interviews/${id}/evaluation`, data),
  listTalentPool: () => client.get('/enterprise/talent-pool'),
  addToTalentPool: (id: number) => client.post(`/enterprise/talent-pool/${id}`),
  removeFromTalentPool: (id: number) => client.delete(`/enterprise/talent-pool/${id}`),
  getAnalytics: (params?: any) => client.get('/enterprise/analytics', { params }),
  listMembers: () => client.get('/enterprise/members'),
  inviteMember: (data: any) => client.post('/enterprise/members', data),
  updateMember: (id: number, data: any) => client.patch(`/enterprise/members/${id}`, null, { params: data }),
  removeMember: (id: number) => client.delete(`/enterprise/members/${id}`),
  getSettings: () => client.get('/enterprise/settings'),
  updateSettings: (data: any) => client.patch('/enterprise/settings', data),
  submitVerification: (data: any) => client.post('/enterprise/verification', data),
  getLogs: () => client.get('/enterprise/operation-logs'),
}

export const adminApi = {
  login: (data: any) => client.post('/admin/auth/login', data),
  getDashboard: () => client.get('/admin/dashboard'),
  listUsers: (params?: any) => client.get('/admin/users', { params }),
  toggleUserStatus: (id: number) => client.post(`/admin/users/${id}/toggle-status`),
  listCompanies: () => client.get('/admin/companies'),
  toggleCompanyStatus: (id: number) => client.post(`/admin/companies/${id}/toggle-status`),
  listVerifications: () => client.get('/admin/verifications'),
  approveVerification: (id: number, opinion?: string) => client.post(`/admin/verifications/${id}/approve`, null, { params: { opinion } }),
  rejectVerification: (id: number, opinion: string) => client.post(`/admin/verifications/${id}/reject`, null, { params: { opinion } }),
  listJobsReview: () => client.get('/admin/jobs/review'),
  approveJob: (id: number) => client.post(`/admin/jobs/${id}/approve`),
  rejectJob: (id: number, reason: string) => client.post(`/admin/jobs/${id}/reject`, null, { params: { reason } }),
  takedownJob: (id: number, reason: string) => client.post(`/admin/jobs/${id}/take-down`, null, { params: { reason } }),
  listComplaints: () => client.get('/admin/complaints'),
  resolveComplaint: (id: number, resolution: string) => client.post(`/admin/complaints/${id}/resolve`, null, { params: { resolution } }),
  getContent: () => client.get('/admin/content'),
  updateContent: (data: any) => client.patch('/admin/content', data),
  getAIProviders: () => client.get('/admin/ai/providers'),
  updateAIProvider: (data: any) => client.patch('/admin/ai/providers', data),
  getAILogs: () => client.get('/admin/ai/logs'),
  getAuditLogs: () => client.get('/admin/audit-logs'),
}
