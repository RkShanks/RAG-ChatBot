"use client";

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, X } from "lucide-react";
import { registerGlobalErrorHandler, unregisterGlobalErrorHandler } from "./api";

type Toast = {
  id: number;
  message: string;
};

type ToastContextType = {
  triggerToast: (message: string) => void;
};

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const triggerToast = useCallback((message: string) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, message }]);
    
    // Auto-dismiss after 6 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 6000);
  }, []);

  // ─── Register as the global error handler ───
  // The axios interceptor in api.ts calls this callback directly whenever
  // any backend request returns an error (4xx/5xx). This bridges the gap
  // between axios (non-React) and our React toast system.
  useEffect(() => {
    registerGlobalErrorHandler(triggerToast);
    return () => unregisterGlobalErrorHandler();
  }, [triggerToast]);

  const removeToast = (id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ triggerToast }}>
      {children}
      {/* Toast Render Node — fixed viewport, highest z-index */}
      <div className="fixed top-6 right-6 flex flex-col gap-3 z-[200] pointer-events-none">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: 50, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
              className="bg-red-500/10 border border-red-500/50 backdrop-blur-xl p-4 rounded-xl shadow-[0_10px_40px_rgba(239,68,68,0.2)] flex items-start gap-4 min-w-[320px] max-w-[440px] pointer-events-auto"
            >
              <AlertCircle className="text-red-400 shrink-0 mt-0.5" size={20} />
              <p className="text-red-50 text-sm font-medium leading-snug flex-1">
                {toast.message}
              </p>
              <button 
                onClick={() => removeToast(toast.id)}
                className="text-red-400/50 hover:text-red-400 transition-colors shrink-0"
              >
                <X size={16} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useErrorToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useErrorToast must be used within a ToastProvider");
  }
  return context;
}
