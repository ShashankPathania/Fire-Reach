import { getToken } from './auth'

export async function apiFetch(url, options = {}) {
  const token = getToken()
  const headers = {
    ...(options.headers || {}),
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  return fetch(url, {
    ...options,
    headers,
  })
}
