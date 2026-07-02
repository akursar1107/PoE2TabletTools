/**
 * Shared configuration for frontend pages
 *
 * This file provides configuration that can be overridden before including it.
 * For production deployments where frontend and backend are separate:
 *
 *   // In your HTML, BEFORE including this file:
 *   <script>
 *     window.API_CONFIG = {
 *       apiBaseUrl: "https://your-backend.fly.dev",
 *       corsOrigins: "https://your-site.github.io"
 *     };
 *   </script>
 *   <script src="/js/config.js"></script>
 */

// Configuration - can be overridden via global window object
window.API_CONFIG = window.API_CONFIG || {};

// API base URL - defaults to empty string (relative paths)
// When deployed separately, set this to your backend URL
const API_BASE_URL = window.API_CONFIG.apiBaseUrl || "";

/**
 * Build a full API URL from a path
 * @param {string} path - API path (e.g., "/api/league/info")
 * @returns {string} Full URL
 */
function apiUrl(path) {
    return API_BASE_URL + path;
}

/**
 * Check if API is configured with a remote base URL
 */
function isApiRemote() {
    return API_BASE_URL && !API_BASE_URL.startsWith("http") === false;
}
