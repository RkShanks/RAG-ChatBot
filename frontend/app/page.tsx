"use client";

import { useState, useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { ChatBox } from "./components/ChatBox";
import { apiClient } from "./lib/api";
import { useErrorToast } from "./lib/ToastContext";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud } from "lucide-react";

export default function Home() {
  const [activeProjectId, setActiveProjectId] = useState("defaultworkspace");
  const [isUploading, setIsUploading] = useState(false);
  const [files, setFiles] = useState<{id: string, name: string}[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const { triggerToast } = useErrorToast();

  useEffect(() => {
    const fetchExistingFiles = async () => {
      try {
        const res = await apiClient.get(`/data/files/${activeProjectId}`);
        if (res.data && res.data.files) {
          setFiles(res.data.files);
        }
      } catch (err: any) {
        if (err.response?.status !== 404) {
          console.warn("Could not fetch existing workspace files.");
        }
      }
    };
    fetchExistingFiles();
  }, [activeProjectId]);

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const uploadRes = await apiClient.post(`/data/upload/${activeProjectId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const newFileId = uploadRes.data.file_id;

      await apiClient.post(`/data/process/${activeProjectId}`, { 
        file_id: newFileId, 
        do_reset: false 
      });

      setFiles(prev => [...prev, { id: newFileId, name: file.name }]);
    } catch (error: any) {
      triggerToast(error.response?.data?.dev_detail || "Vector upload pipeline crushed.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!isDragging) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    // Prevent flickering when leaving child elements
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setIsDragging(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    try {
      await apiClient.delete(`/data/project/${activeProjectId}/file/${fileId}`);
      setFiles(prev => prev.filter(f => f.id !== fileId));
    } catch (e: any) {
      triggerToast(e.response?.data?.dev_detail || "Eradication sequence failed!");
    }
  };


  return (
    <main 
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className="flex h-screen w-screen overflow-hidden bg-[var(--background)] relative"
    >
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-emerald-600/10 rounded-full blur-[120px] pointer-events-none z-0" />
      
      <div id="toast-root" className="absolute top-4 right-4 z-50 flex flex-col gap-2" />

      {/* Global Drag Overlay */}
      <AnimatePresence>
        {isDragging && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-[100] bg-indigo-900/60 backdrop-blur-md border-4 border-dashed border-indigo-400 m-6 rounded-3xl flex items-center justify-center pointer-events-none transition-all"
          >
             <div className="flex flex-col items-center gap-4 bg-[#1a1d24]/90 p-10 rounded-3xl shadow-[0_0_100px_rgba(79,70,229,0.4)] glass">
                <div className="w-20 h-20 rounded-full bg-indigo-500/20 flex items-center justify-center animate-bounce shadow-[0_0_30px_rgba(79,70,229,0.5)]">
                  <UploadCloud size={40} className="text-indigo-400" />
                </div>
                <h2 className="text-2xl font-bold text-white tracking-tight">Drop document to ingest</h2>
                <p className="text-white/50 text-sm font-medium">Automatic chunking will initialize mapping into '{activeProjectId}'</p>
             </div>
          </motion.div>
        )}
      </AnimatePresence>

      <Sidebar 
        activeProjectId={activeProjectId} 
        files={files}
        isUploading={isUploading}
        onFileUpload={handleFileUpload}
        onDeleteFile={handleDeleteFile}
      />
      <ChatBox activeProjectId={activeProjectId} />
    </main>
  );
}
