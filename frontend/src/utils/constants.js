export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/',
  IMPORT: '/import',
  PROCESSING: '/processing',
  CONTRACTS: '/contracts',
  STAKEHOLDERS: '/stakeholders',
  STAKEHOLDER_PROFILE: '/stakeholders/:id',
  STAKEHOLDER_COMPARISON: '/stakeholders/compare',
  STAKEHOLDER_NETWORK: '/stakeholders/network',
  EMAILS: '/emails',
  EMAIL_THREADS: '/emails/threads',
  EMAIL_THREAD_DETAIL: '/emails/threads/:id',
  EMAIL_CLASSIFICATION: '/emails/classification',
  ANALYTICS: '/analytics',
}

export const CONTRACT_STAGES = [
  'Request',
  'Legal Review',
  'Finance Review',
  'Procurement/Compliance',
  'Redline Negotiation',
  'Leadership Sign-off',
  'Repository & Obligation Tracking',
]
