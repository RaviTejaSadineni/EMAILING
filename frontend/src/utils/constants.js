export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/',
  IMPORT: '/import',
  PROCESSING: '/processing',
  CONTRACTS: '/contracts',
  STAKEHOLDERS: '/stakeholders',
  EMAILS: '/emails',
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
