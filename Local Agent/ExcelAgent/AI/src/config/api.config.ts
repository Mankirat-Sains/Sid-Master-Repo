/**
 * API Configuration for Mantle Excel Agent
 * Configure your backend endpoints here
 */

// Detect if we're in development or production
const isDevelopment = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

export const API_CONFIG = {
  // Backend API base URL
  // Development: Use relative URLs (proxied through webpack dev server)
  // This avoids mixed content issues (HTTPS page can't call HTTP API)
  // Webpack proxy forwards /api/* requests to http://localhost:8000
  baseUrl: isDevelopment ? "" : "https://api.mantle.ai",
  
      // API endpoints
      endpoints: {
        command: "/api/excel/command",  // Main intelligent command endpoint
        analyzeLayout: "/api/excel/analyze-layout",  // LLM-powered layout analysis
        detectLegend: "/api/excel/detect-legend",  // Legend detection
        parseLabels: "/api/excel/parse-labels",  // LLM-assisted label mapping for ambiguous cases
        health: "/health",  // Health check
      },
  
  // Authentication
  auth: {
    enabled: false, // Set to true when you implement auth
    tokenKey: "mantle_auth_token",
  },
  
  // Request configuration
  timeout: 30000, // 30 seconds
  retries: 3,
};

// Helper to get full endpoint URL
export function getEndpoint(endpoint: keyof typeof API_CONFIG.endpoints): string {
  return `${API_CONFIG.baseUrl}${API_CONFIG.endpoints[endpoint]}`;
}

// Helper to get auth token (implement your auth logic)
export function getAuthToken(): string | null {
  if (!API_CONFIG.auth.enabled) return null;
  
  // For now, check localStorage
  // Later: Implement proper Microsoft SSO
  return localStorage.getItem(API_CONFIG.auth.tokenKey);
}

// Helper to set auth token
export function setAuthToken(token: string): void {
  localStorage.setItem(API_CONFIG.auth.tokenKey, token);
}

