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

// ─── Global Error Toast Bridge ───
// A simple callback pattern to bridge axios (non-React) with the React Toast system.
// ToastProvider registers itself here on mount.
let _globalErrorHandler: ((message: string) => void) | null = null;

export function registerGlobalErrorHandler(handler: (message: string) => void) {
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
    // DEBUG: trace every error that flows through axios
    console.error('[API Interceptor] Error caught:', error.response?.status, error.response?.data);
    console.error('[API Interceptor] Handler registered?', !!_globalErrorHandler);
    
    if (error.response?.data) {
      const data = error.response.data;
      const errorMessage = data.message || data.dev_detail || data.detail || 'An unexpected error occurred.';
      
      console.error('[API Interceptor] Will show toast:', errorMessage);
      
      if (_globalErrorHandler) {
        _globalErrorHandler(errorMessage);
      } else {
        console.error('[API Interceptor] ⚠️ No handler registered! Toast cannot fire.');
      }
    }
    // Always re-throw so individual catch blocks still work if needed
    return Promise.reject(error);
  }
);
