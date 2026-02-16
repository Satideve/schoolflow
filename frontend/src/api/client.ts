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
  const token = localStorage.getItem("access_token");

  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }

  config.withCredentials = false;
  return config;
});


/**
 * Set or clear the Authorization header.
 */
export function setAuthToken(token?: string) {
  if (token) {
    localStorage.setItem("access_token", token);
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    localStorage.removeItem("access_token");
    delete api.defaults.headers.common["Authorization"];
  }
}

