import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

// Generates and persists the unique anonymous session constraint
export const getSessionId = () => {
  if (typeof window === 'undefined') return '';
  
  let sessionId = localStorage.getItem('X-Session-ID');
  if (!sessionId) {
    sessionId = uuidv4();
    localStorage.setItem('X-Session-ID', sessionId);
  }
  return sessionId;
};

export const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercept all requests to cleanly enforce the FastAPI backend stateless security protocol
apiClient.interceptors.request.use((config) => {
  config.headers['X-Session-ID'] = getSessionId();
  return config;
});

export type ToastData = {
  message: string;
  req_id?: string;
  signal?: string;
};

// ─── Global Error Toast Bridge ───
// A simple callback pattern to bridge axios (non-React) with the React Toast system.
// ToastProvider registers itself here on mount.
let _globalErrorHandler: ((data: ToastData) => void) | null = null;

export function registerGlobalErrorHandler(handler: (data: ToastData) => void) {
  _globalErrorHandler = handler;
}

export function unregisterGlobalErrorHandler() {
  _globalErrorHandler = null;
}

// ─── Global Response Interceptor ───
// Catches ALL error responses from the FastAPI backend and routes them
// to the registered toast handler. This guarantees every CustomAPIException,
// global_exception_handler, and validation_exception_handler error surfaces
// in the UI automatically — no per-component catch block needed.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // 1. Handle complete network failures or dead backend connections.
    // If the server crashed entirely (e.g., MongoDB disconnection preventing Uvicorn from binding),
    // there won't be an error.response at all.
    if (!error.response) {
      if (_globalErrorHandler) {
        _globalErrorHandler({ 
          message: "Could not connect to the API server. Ensure the backend is running and the database is online.", 
          signal: "server_offline" 
        });
      }
      return Promise.reject(error);
    }

    // 2. Specifically suppress 404 errors from triggering global toasts.
    // Component-level try/catches will handle 404s gracefully (e.g., empty chat history).
    if (error.response?.status === 404) {
      return Promise.reject(error);
    }

    if (error.response?.data) {
      const data = error.response.data;
      const errorMessage = data.message || data.dev_detail || data.detail || 'An unexpected error occurred.';
      const req_id = data.request_id;
      const signal = Array.isArray(data.signal) ? data.signal[0] : data.signal;
      
      if (_globalErrorHandler) {
        _globalErrorHandler({ message: errorMessage, req_id, signal });
      }
    }
    // Always re-throw so individual catch blocks still work if needed
    return Promise.reject(error);
  }
);
