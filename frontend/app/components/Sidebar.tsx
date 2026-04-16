"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Folder, FileText, Settings, Database, Trash2, PlusCircle, UploadCloud, Loader2 } from "lucide-react";
import { apiClient } from "../lib/api";
import { useErrorToast } from "../lib/ToastContext";

export function Sidebar({ activeProjectId }: { activeProjectId: string }) {
  const [isUploading, setIsUploading] = useState(false);
  const [files, setFiles] = useState<{id: string, name: string}[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { triggerToast } = useErrorToast();

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      // 1. Upload to FastAPI
      const uploadRes = await apiClient.post(`/data/upload/${activeProjectId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const newFileId = uploadRes.data.file_id;

      // 2. Trigger Heavy NLP Ingestion Processing
      await apiClient.post(`/data/process/${activeProjectId}`, { 
        file_id: newFileId, 
        do_reset: false 
      });

      // 3. Update React State to reflect new Data Lake asset
      setFiles(prev => [...prev, { id: newFileId, name: file.name }]);

    } catch (error: any) {
      triggerToast(error.response?.data?.dev_detail || "Vector upload pipeline crushed.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    try {
      // Fires our Custom Stage 2.5 Backend Pipeline!!
      await apiClient.delete(`/data/project/${activeProjectId}/file/${fileId}`);
      setFiles(prev => prev.filter(f => f.id !== fileId));
    } catch (e: any) {
      triggerToast(e.response?.data?.dev_detail || "Eradication sequence failed!");
    }
  };

  return (
    <motion.aside 
      initial={{ x: -300, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 25 }}
      className="w-72 h-full glass border-r border-[#ffffff0f] flex flex-col p-6 z-20 shadow-2xl relative"
    >
      <div className="flex items-center gap-3 mb-8 mt-2">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-[0_0_15px_rgba(79,70,229,0.5)]">
          <Database size={16} className="text-white" />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-white/90">Nimo RAG</h1>
      </div>

      <motion.button 
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="w-full py-2.5 bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/30 text-indigo-100 rounded-xl mb-6 flex items-center justify-center gap-2 text-sm font-medium transition-all shadow-[0_0_10px_rgba(79,70,229,0.1)]"
      >
        <PlusCircle size={16} />
        New Project
      </motion.button>

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Active Workspace</h2>
        </div>
        
        <div className="mb-4">
          <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20 mb-2 shadow-inner">
            <div className="flex items-center gap-3">
              <Folder size={18} className="text-indigo-400" />
              <span className="text-sm font-medium text-white/90 truncate">{activeProjectId}</span>
            </div>
          </div>
          
          {/* Loaded Files Mapping */}
          <div className="pl-6 flex flex-col gap-1 border-l border-white/5 ml-3">
            <AnimatePresence>
              {files.map(file => (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  key={file.id} 
                  className="group flex items-center justify-between p-2 rounded-lg hover:bg-white/5 transition-all cursor-pointer"
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileText size={14} className="text-emerald-400 shrink-0" />
                    <span className="text-xs text-white/70 group-hover:text-white transition-colors truncate">{file.name}</span>
                  </div>
                  <motion.button onClick={() => handleDeleteFile(file.id)} whileHover={{ scale: 1.1 }} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded-md transition-all">
                    <Trash2 size={12} className="text-red-400" />
                  </motion.button>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Hidden File Input */}
            <input 
              type="file" 
              ref={fileInputRef}
              onChange={handleFileUpload} 
              className="hidden" 
              accept=".txt,.pdf,.docx"
            />

            {/* Upload Button */}
            <div 
              onClick={() => !isUploading && fileInputRef.current?.click()}
              className={`flex items-center gap-2 p-2 rounded-lg border border-transparent transition-all cursor-pointer mt-1
                ${isUploading ? "opacity-50 pointer-events-none" : "hover:bg-indigo-500/10 hover:border-indigo-500/30"}
              `}
            >
              {isUploading ? <Loader2 size={14} className="text-indigo-400 animate-spin shrink-0" /> : <UploadCloud size={14} className="text-indigo-400 shrink-0" />}
              <span className="text-[11px] font-semibold text-indigo-400/80 uppercase tracking-wide">{isUploading ? "Ingesting Vector Data..." : "Upload Document"}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-white/10">
        <button className="flex items-center gap-3 text-sm text-white/50 hover:text-white/90 transition-colors w-full p-2 rounded-lg hover:bg-white/5">
          <Settings size={18} />
          Settings
        </button>
      </div>
    </motion.aside>
  );
}
