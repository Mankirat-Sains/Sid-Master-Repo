export default defineNuxtRouteMiddleware((to) => {
  // Always send root visitors to the login page
  if (to.path === '/') {
    return navigateTo('/login', { replace: true })
  }
})
