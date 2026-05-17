import apiClient from './client'

export const startClassification = async () => (await apiClient.post('/api/classification/start')).data
export const getClassificationStatus = async () => (await apiClient.get('/api/classification/status')).data
export const getClassificationResults = async () => (await apiClient.get('/api/classification/results')).data

export const startThreadMerge = async () => (await apiClient.post('/api/threads/start-merge')).data
export const getThreadMergeStatus = async () => (await apiClient.get('/api/threads/status')).data
export const getThreads = async () => (await apiClient.get('/api/threads')).data

export const startContractExtraction = async () => (await apiClient.post('/api/contracts/start-extraction')).data
export const getContractExtractionStatus = async () => (await apiClient.get('/api/contracts/status')).data
export const getContracts = async () => (await apiClient.get('/api/contracts')).data

export const startStakeholderExtraction = async () => (await apiClient.post('/api/stakeholders/start-extraction')).data
export const getStakeholderExtractionStatus = async () => (await apiClient.get('/api/stakeholders/status')).data
export const getStakeholders = async () => (await apiClient.get('/api/stakeholders')).data

export const startLifecycleDetection = async () => (await apiClient.post('/api/lifecycle/start-detection')).data
export const getLifecycleStatus = async () => (await apiClient.get('/api/lifecycle/status')).data
export const getLifecycleOverview = async () => (await apiClient.get('/api/lifecycle/overview')).data
