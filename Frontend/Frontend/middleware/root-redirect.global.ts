export default defineNuxtRouteMiddleware((to) => {
  // Keep landing page accessible; opt-in redirect with ?redirect=login if needed
  if (to.path === '/' && to.query.redirect === 'login') {
    return navigateTo('/login', { replace: true })
  }
})
