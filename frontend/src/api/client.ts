/* C:\coding_projects\dev\schoolflow\frontend\src\api\client.ts */
import axios from "axios";

/**
 * Base API URL comes from Vite env.
 * Default fallback is http://localhost:8000 (backend container).
 */
const baseURL = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const api = axios.create({
  baseURL,
  withCredentials: false,
  headers: {
    "ngrok-skip-browser-warning": "true",
  },
});

api.interceptors.request.use((config) => {
  config.withCredentials = false;
  return config;
});

/**
 * Set or clear the Authorization header.
 */
export function setAuthToken(token?: string) {
  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
}

export default api;
