"use client";

import { useState, useEffect, useCallback } from "react";
import { Sidebar } from "./components/Sidebar";
import { ChatBox } from "./components/ChatBox";
import { SettingsPanel } from "./components/SettingsPanel";
import type { UserProfile } from "./components/SettingsPanel";
import { apiClient } from "./lib/api";
import { useErrorToast } from "./lib/ToastContext";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud } from "lucide-react";

type ProjectInfo = { id: string; name: string };

export default function Home() {
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [files, setFiles] = useState<{id: string, name: string}[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [chatResetKey, setChatResetKey] = useState(0);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const { triggerToast } = useErrorToast();

  // ─── Fetch user profile on mount ───
  const fetchProfile = useCallback(async () => {
    try {
      const res = await apiClient.get("/settings/profile");
      if (res.data?.profile) {
        setUserProfile(res.data.profile);
      }
    } catch (err) {
      console.warn("Could not fetch user profile.", err);
    }
  }, []);

  // ─── Fetch all workspaces from the database ───
  const refreshProjects = useCallback(async () => {
    try {
      const res = await apiClient.get("/data/projects");
      if (res.data?.projects) {
        const mapped: ProjectInfo[] = res.data.projects.map((p: any) => ({
          id: p.project_id,
          name: p.project_name || p.project_id,
        }));
        setProjects(mapped);
        return mapped;
      }
    } catch (err: any) {
      console.warn("Could not fetch projects.", err);
    }
    return [];
  }, []);

  // ─── Create a new workspace and return its ID ───
  const createNewWorkspace = useCallback(() => {
    const newId = "workspace" + Date.now().toString(36);
    setActiveProjectId(newId);
    setFiles([]);
    return newId;
  }, []);

  // ─── Initial hydration ───
  useEffect(() => {
    const hydrate = async () => {
      // Fetch profile and projects in parallel
      await fetchProfile();
      const fetched = await refreshProjects();
      if (fetched.length > 0 && !activeProjectId) {
        setActiveProjectId(fetched[0].id);
      } else if (fetched.length === 0) {
        // Auto-create a workspace so the user can immediately drag-and-drop
        createNewWorkspace();
      }
    };
    hydrate();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ─── Fetch files whenever the active project changes ───
  useEffect(() => {
    if (!activeProjectId) return;
    const fetchExistingFiles = async () => {
      try {
        const res = await apiClient.get(`/data/files/${activeProjectId}`);
        if (res.data?.files) {
          setFiles(res.data.files);
        } else {
          setFiles([]);
        }
      } catch (err: any) {
        if (err.response?.status !== 404) {
          console.warn("Could not fetch existing workspace files.");
        }
        setFiles([]);
      }
    };
    fetchExistingFiles();
  }, [activeProjectId]);

  // ─── Switch workspace ───
  const handleSwitchProject = (projectId: string) => {
    if (projectId === activeProjectId) return;
    setActiveProjectId(projectId);
    // files + chat history will auto-refresh via useEffect dependencies
  };

  // ─── Delete an entire workspace ───
  const handleDeleteProject = async (projectId: string) => {
    const confirmed = window.confirm(
      "⚠️ This will permanently destroy all files, vector embeddings, and chat history for this workspace. Are you sure?"
    );
    if (!confirmed) return;

    try {
      await apiClient.delete(`/data/project/${projectId}`);
      const updated = await refreshProjects();

      if (projectId === activeProjectId) {
        // Switch to the next available project or create a fresh one
        if (updated.length > 0) {
          setActiveProjectId(updated[0].id);
        } else {
          createNewWorkspace();
        }
      }
    } catch {
      // HTTP errors auto-surface via global axios interceptor
    }
  };

  // ─── File Upload (with auto-naming refresh) ───
  const handleFileUpload = async (file: File) => {
    if (!activeProjectId) return;
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const uploadRes = await apiClient.post(`/data/upload/${activeProjectId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const newFileId = uploadRes.data.file_id;

      const processRes = await apiClient.post(`/data/process/${activeProjectId}`, { 
        file_id: newFileId, 
        do_reset: false 
      });

      // Check for pipeline-level failures (Docling chunking, embedding, etc.)
      // These return 200 OK with failure info buried in the response body,
      // so the global interceptor won't catch them — we must check manually.
      const processData = processRes.data;
      if (processData?.failed_files && processData.failed_files.length > 0) {
        const failedNames = processData.failed_files.join(", ");
        triggerToast(`⚠️ Ingestion partially failed for: ${failedNames}. The file was uploaded but could not be fully processed into vectors.`);
      }
      if (processData?.signal === "chunk_insertion_failed" && (!processData.failed_files || processData.failed_files.length === 0)) {
        triggerToast("⚠️ Vector ingestion failed. The document could not be processed. Check backend logs for details.");
      }

      setFiles(prev => [...prev, { id: newFileId, name: file.name }]);

      // Refresh projects to catch auto-naming from backend
      await refreshProjects();
    } catch {
      // HTTP errors (415 unsupported type, 500 server error, etc.) are handled
      // automatically by the global axios interceptor → toast auto-fires.
      // We only need to stop the loading spinner here.
    } finally {
      setIsUploading(false);
    }
  };

  // ─── Drag & Drop ───
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!isDragging) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
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

  // ─── Delete individual file ───
  const handleDeleteFile = async (fileId: string) => {
    if (!activeProjectId) return;
    try {
      await apiClient.delete(`/data/project/${activeProjectId}/file/${fileId}`);
      setFiles(prev => prev.filter(f => f.id !== fileId));
    } catch {
      // HTTP errors auto-surface via global axios interceptor
    }
  };

  // Don't render anything until we have an activeProjectId
  const currentProjectName = projects.find(p => p.id === activeProjectId)?.name || activeProjectId || "New Workspace";

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
                <p className="text-white/50 text-sm font-medium">Automatic chunking into &apos;{currentProjectName}&apos;</p>
             </div>
          </motion.div>
        )}
      </AnimatePresence>

      <Sidebar 
        projects={projects}
        activeProjectId={activeProjectId || ""}
        files={files}
        isUploading={isUploading}
        onFileUpload={handleFileUpload}
        onDeleteFile={handleDeleteFile}
        onNewProject={createNewWorkspace}
        onSwitchProject={handleSwitchProject}
        onDeleteProject={handleDeleteProject}
        onToggleSettings={() => setIsSettingsOpen(true)}
      />
      <ChatBox
        key={chatResetKey}
        activeProjectId={activeProjectId || ""}
        userProfile={userProfile}
      />
      <SettingsPanel
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        userProfile={userProfile}
        onProfileUpdate={(profile) => setUserProfile(profile)}
        onResetComplete={async () => {
          const updated = await refreshProjects();
          if (updated.length > 0) {
            setActiveProjectId(updated[0].id);
          } else {
            setActiveProjectId(null);
            setFiles([]);
          }
          setChatResetKey(prev => prev + 1);
        }}
      />
    </main>
  );
}
