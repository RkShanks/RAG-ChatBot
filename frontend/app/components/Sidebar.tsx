"use client";

import { motion } from "framer-motion";
import { Folder, FileText, Settings, Database, Trash2 } from "lucide-react";

export function Sidebar() {
  return (
    <motion.aside 
      initial={{ x: -300, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 25 }}
      className="w-72 h-full glass border-r border-[#ffffff0f] flex flex-col p-6 z-10"
    >
      <div className="flex items-center gap-3 mb-10 mt-2">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-[0_0_15px_rgba(79,70,229,0.5)]">
          <Database size={16} className="text-white" />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-white/90">Nimo RAG</h1>
      </div>

      <div className="flex-1 overflow-y-auto pr-2">
        <h2 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-4">Your Knowledge Base</h2>
        
        {/* Mock Project Item */}
        <motion.div 
          whileHover={{ scale: 1.02, backgroundColor: "rgba(255,255,255,0.05)" }}
          className="p-3 rounded-xl cursor-pointer border border-transparent transition-colors mb-2"
        >
          <div className="flex items-center gap-3">
            <Folder size={18} className="text-indigo-400" />
            <span className="text-sm font-medium text-white/80">Corporate Policies</span>
          </div>
        </motion.div>
        
        {/* Mock Files under Project */}
        <div className="pl-6 flex flex-col gap-2 mt-2 border-l border-white/10 ml-3">
          <div className="group flex items-center justify-between p-2 rounded-lg hover:bg-white/5 transition-all cursor-pointer">
            <div className="flex items-center gap-2">
              <FileText size={14} className="text-emerald-400" />
              <span className="text-xs text-white/60 group-hover:text-white/90 transition-colors">HR_Guidelines_2026.pdf</span>
            </div>
            <motion.button whileHover={{ scale: 1.1 }} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded-md transition-all">
               <Trash2 size={12} className="text-red-400" />
            </motion.button>
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
