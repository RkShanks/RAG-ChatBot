"use client";

import { useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Folder,
  FolderOpen,
  FileText,
  Settings,
  Database,
  Trash2,
  CirclePlus,
  CloudUpload,
  Loader2,
} from "lucide-react";

type ProjectInfo = { id: string; name: string };

export function Sidebar({
  projects,
  activeProjectId,
  files,
  isUploading,
  onFileUpload,
  onDeleteFile,
  onNewProject,
  onSwitchProject,
  onDeleteProject,
  onToggleSettings,
}: {
  projects: ProjectInfo[];
  activeProjectId: string;
  files: { id: string; name: string }[];
  isUploading: boolean;
  onFileUpload: (f: File) => void;
  onDeleteFile: (id: string) => void;
  onNewProject: () => void;
  onSwitchProject: (id: string) => void;
  onDeleteProject: (id: string) => void;
  onToggleSettings: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <motion.aside
      initial={{ x: -300, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 25 }}
      className="w-72 h-full glass border-r border-[#ffffff0f] flex flex-col p-6 z-20 shadow-2xl relative"
    >
      {/* ─── Brand Header ─── */}
      <div className="flex items-center gap-3 mb-8 mt-2">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-[0_0_15px_rgba(79,70,229,0.5)]">
          <Database size={16} className="text-white" />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-white/90">
          Nimo RAG
        </h1>
      </div>

      {/* ─── New Project Button ─── */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={onNewProject}
        className="w-full py-2.5 bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/30 text-indigo-100 rounded-xl mb-6 flex items-center justify-center gap-2 text-sm font-medium transition-all shadow-[0_0_10px_rgba(79,70,229,0.1)]"
      >
        <CirclePlus size={16} />
        New Workspace
      </motion.button>

      {/* ─── Scrollable Content ─── */}
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        {/* ─── Workspaces Section ─── */}
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[10px] font-bold text-white/40 uppercase tracking-widest">
            Workspaces
          </h2>
          <span className="text-[10px] text-white/20">{projects.length}</span>
        </div>

        <div className="flex flex-col gap-1 mb-5">
          <AnimatePresence>
            {projects.map((project) => {
              const isActive = project.id === activeProjectId;
              return (
                <motion.div
                  key={project.id}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  onClick={() => onSwitchProject(project.id)}
                  className={`group flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all ${
                    isActive
                      ? "bg-indigo-500/15 border border-indigo-500/25 shadow-inner"
                      : "hover:bg-white/5 border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    {isActive ? (
                      <FolderOpen
                        size={16}
                        className="text-indigo-400 shrink-0"
                      />
                    ) : (
                      <Folder
                        size={16}
                        className="text-white/30 group-hover:text-white/50 shrink-0 transition-colors"
                      />
                    )}
                    <span
                      className={`text-sm truncate transition-colors ${
                        isActive
                          ? "text-white/90 font-medium"
                          : "text-white/50 group-hover:text-white/70"
                      }`}
                    >
                      {project.name}
                    </span>
                  </div>
                  <motion.button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteProject(project.id);
                    }}
                    whileHover={{ scale: 1.15 }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded-md transition-all shrink-0"
                  >
                    <Trash2 size={12} className="text-red-400" />
                  </motion.button>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>

        {/* ─── Active Workspace Files ─── */}
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[10px] font-bold text-white/40 uppercase tracking-widest">
            Loaded Files
          </h2>
        </div>

        <div className="pl-2 flex flex-col gap-1 border-l border-white/5 ml-1">
          <AnimatePresence>
            {files.map((file) => (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                key={file.id}
                className="group flex items-center justify-between p-2 rounded-lg hover:bg-white/5 transition-all cursor-pointer"
              >
                <div className="flex items-center gap-2 truncate">
                  <FileText
                    size={14}
                    className="text-emerald-400 shrink-0"
                  />
                  <span className="text-xs text-white/70 group-hover:text-white transition-colors truncate">
                    {file.name}
                  </span>
                </div>
                <motion.button
                  onClick={() => onDeleteFile(file.id)}
                  whileHover={{ scale: 1.1 }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded-md transition-all"
                >
                  <Trash2 size={12} className="text-red-400" />
                </motion.button>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Hidden File Input */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => {
              if (e.target.files?.[0]) {
                onFileUpload(e.target.files[0]);
                e.target.value = "";
              }
            }}
            className="hidden"
            accept=".txt,.pdf,.md"
          />

          {/* Upload Button */}
          <div
            onClick={() => !isUploading && fileInputRef.current?.click()}
            className={`flex items-center gap-2 p-2 rounded-lg border border-transparent transition-all cursor-pointer mt-1
              ${
                isUploading
                  ? "opacity-50 pointer-events-none"
                  : "hover:bg-indigo-500/10 hover:border-indigo-500/30"
              }
            `}
          >
            {isUploading ? (
              <Loader2
                size={14}
                className="text-indigo-400 animate-spin shrink-0"
              />
            ) : (
              <CloudUpload
                size={14}
                className="text-indigo-400 shrink-0"
              />
            )}
            <span className="text-[11px] font-semibold text-indigo-400/80 uppercase tracking-wide">
              {isUploading ? "Ingesting Vector Data..." : "Upload Document"}
            </span>
          </div>
        </div>
      </div>

      {/* ─── Settings Footer ─── */}
      <div className="mt-6 pt-6 border-t border-white/10">
        <button onClick={onToggleSettings} className="flex items-center gap-3 text-sm text-white/50 hover:text-white/90 transition-colors w-full p-2 rounded-lg hover:bg-white/5">
          <Settings size={18} />
          Settings
        </button>
      </div>
    </motion.aside>
  );
}
