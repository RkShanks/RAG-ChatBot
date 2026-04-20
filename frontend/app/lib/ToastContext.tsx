"use client";

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, X, Database, FileText, Server, Bot, ShieldAlert } from "lucide-react";
import { registerGlobalErrorHandler, unregisterGlobalErrorHandler, ToastData } from "./api";

type Toast = {
  id: number;
  message: string;
  req_id?: string;
  signal?: string;
};

type ToastContextType = {
  triggerToast: (data: string | ToastData) => void;
};

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const triggerToast = useCallback((data: string | ToastData) => {
    const id = Date.now() + Math.random();
    let newToast: Toast;
    let isCritical = false;

    if (typeof data === "string") {
      newToast = { id, message: data };
      if (data.toLowerCase().includes("server") || data.toLowerCase().includes("network")) {
        isCritical = true; // Catch manual string-based criticals
      }
    } else {
      newToast = { id, ...data };
      if (data.signal === 'server_offline' || data.signal === 'internal_server_error') {
        isCritical = true;
      }
    }

    setToasts(prev => {
      // Prevent rapid duplicate stacking. If a critical internal server error 
      // is already displayed, do not spawn another one.
      const isDuplicate = prev.some(t => 
        t.message === newToast.message || 
        (isCritical && (t.signal === 'server_offline' || t.signal === 'internal_server_error'))
      );
      
      if (isDuplicate) return prev;
      return [...prev, newToast];
    });

    // Restore auto-dismiss for non-critical errors (10 seconds)
    if (!isCritical) {
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, 10000);
    }
  }, []);

  const getIconForSignal = (signal?: string) => {
    if (!signal) return <AlertCircle className="text-red-400 shrink-0 mt-0.5" size={20} />;
    const s = signal.toLowerCase();
    if (s.includes("db") || s.includes("database") || s.includes("project") || s.includes("collection") || s.includes("retrieval")) return <Database className="text-red-400 shrink-0 mt-0.5" size={20} />;
    if (s.includes("file") || s.includes("asset") || s.includes("type") || s.includes("size")) return <FileText className="text-red-400 shrink-0 mt-0.5" size={20} />;
    if (s.includes("server") || s.includes("internal")) return <Server className="text-red-400 shrink-0 mt-0.5" size={20} />;
    if (s.includes("nlp") || s.includes("llm") || s.includes("model")) return <Bot className="text-red-400 shrink-0 mt-0.5" size={20} />;
    if (s.includes("api_key") || s.includes("permission") || s.includes("validation") || s.includes("unauthorized")) return <ShieldAlert className="text-red-400 shrink-0 mt-0.5" size={20} />;
    return <AlertCircle className="text-red-400 shrink-0 mt-0.5" size={20} />;
  };

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
              {getIconForSignal(toast.signal)}
              <div className="flex-1 flex flex-col gap-1.5">
                <p className="text-red-50 text-sm font-medium leading-snug">
                  {toast.message}
                </p>
                {toast.req_id && (
                  <p className="text-[11px] text-red-200/60 font-mono tracking-wide">
                    Req ID: {toast.req_id}
                  </p>
                )}
              </div>
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
