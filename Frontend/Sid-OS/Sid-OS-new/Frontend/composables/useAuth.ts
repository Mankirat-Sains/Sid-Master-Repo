export const useAuth = () => {
  const isAuthenticated = useState<boolean>('auth.isAuthenticated', () => {
    if (process.client) {
      return localStorage.getItem('sidos.auth') === 'true'
    }
    return false
  })

  const login = () => {
    if (process.client) {
      localStorage.setItem('sidos.auth', 'true')
      isAuthenticated.value = true
    }
  }

  const logout = () => {
    if (process.client) {
      localStorage.removeItem('sidos.auth')
      isAuthenticated.value = false
    }
  }

  const checkAuth = () => {
    if (process.client) {
      isAuthenticated.value = localStorage.getItem('sidos.auth') === 'true'
    }
    return isAuthenticated.value
  }

  return {
    isAuthenticated: readonly(isAuthenticated),
    login,
    logout,
    checkAuth
  }
}

