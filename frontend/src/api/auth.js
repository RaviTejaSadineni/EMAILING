import apiClient from './client'

export const register = async (payload) => {
  const { data } = await apiClient.post('/auth/register', payload)
  return data
}

export const login = async (payload) => {
  const { data } = await apiClient.post('/auth/login', payload)
  return data
}

export const getMe = async () => {
  const { data } = await apiClient.get('/auth/me')
  return data
}

export const refreshToken = async (refreshTokenValue) => {
  const { data } = await apiClient.post('/auth/refresh', { refresh_token: refreshTokenValue })
  return data
}
