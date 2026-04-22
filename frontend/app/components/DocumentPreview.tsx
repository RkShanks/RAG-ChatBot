"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Loader2, FileText, AlertTriangle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { apiClient } from "../lib/api";

type Props = {
  projectId: string;
  assetId: string;
  fileName: string;
  onClose: () => void;
};

const MD_EXTENSIONS = new Set(["md", "markdown"]);

function isMdFile(name: string): boolean {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  return MD_EXTENSIONS.has(ext);
}

export function DocumentPreview({ projectId, assetId, fileName, onClose }: Props) {
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setContent(null);
    setError(null);
    apiClient
      .get(`/documents/preview/${projectId}/${assetId}`)
      .then((res) => setContent(res.data.preview))
      .catch(() => setError("Could not load preview. The file may be unavailable or unsupported."));
  }, [projectId, assetId]);

  // Close on Escape key
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <AnimatePresence>
      {/* Backdrop */}
      <motion.div
        key="backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
      />

      {/* Modal */}
      <motion.div
        key="modal"
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-6 pointer-events-none"
      >
        <div
          className="pointer-events-auto w-full max-w-3xl max-h-[80vh] flex flex-col rounded-2xl border border-white/10 bg-[#12141a]/95 shadow-2xl backdrop-blur-xl overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center gap-3 px-6 py-4 border-b border-white/10 shrink-0">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/15 border border-indigo-500/25 flex items-center justify-center shrink-0">
              <FileText size={14} className="text-indigo-400" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-sm font-semibold text-white/90 truncate">{fileName}</h2>
              <p className="text-[10px] text-white/30">Document Preview — first 3000 characters</p>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-white/10 text-white/40 hover:text-white transition-colors shrink-0"
              title="Close (Esc)"
            >
              <X size={16} />
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
            {content === null && error === null && (
              <div className="flex flex-col items-center justify-center h-40 gap-3 text-white/40">
                <Loader2 size={24} className="animate-spin text-indigo-400" />
                <span className="text-sm">Extracting document text...</span>
              </div>
            )}

            {error && (
              <div className="flex flex-col items-center justify-center h-40 gap-3 text-red-400/70">
                <AlertTriangle size={24} />
                <span className="text-sm text-center max-w-xs">{error}</span>
              </div>
            )}

            {content !== null && !error && (
              isMdFile(fileName) ? (
                <div className="prose prose-invert max-w-none text-[14px] leading-relaxed prose-p:leading-relaxed">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
                </div>
              ) : (
                <pre className="text-[13px] text-white/70 font-mono leading-relaxed whitespace-pre-wrap break-words">
                  {content}
                </pre>
              )
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
