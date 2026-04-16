"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Cpu,
  Database,
  Thermometer,
  Search,
  FileText,
  AlertTriangle,
  Loader2,
  Check,
  Server,
  Brain,
  Layers,
} from "lucide-react";
import { apiClient } from "../lib/api";

type SystemInfo = {
  generation_backend: string;
  generation_model: string;
  embedding_backend: string;
  embedding_model: string;
  vector_db_backend: string;
  reranker_backend: string;
  database_uri: string;
  database_name: string;
};

type TuningValues = {
  temperature: number;
  retrieval_limit: number;
  max_output_tokens: number;
};

export function SettingsPanel({
  isOpen,
  onClose,
  onResetComplete,
}: {
  isOpen: boolean;
  onClose: () => void;
  onResetComplete: () => void;
}) {
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [tuning, setTuning] = useState<TuningValues>({
    temperature: 0.1,
    retrieval_limit: 5,
    max_output_tokens: 32768,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    const fetchData = async () => {
      try {
        const [infoRes, tuningRes] = await Promise.all([
          apiClient.get("/settings/info"),
          apiClient.get("/settings/tuning"),
        ]);
        if (infoRes.data?.info) setInfo(infoRes.data.info);
        if (tuningRes.data?.tuning) setTuning(tuningRes.data.tuning);
      } catch (err) {
        console.warn("Failed to fetch settings", err);
      }
    };
    fetchData();
  }, [isOpen]);

  const handleApplyTuning = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      await apiClient.put("/settings/tuning", tuning);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err) {
      console.error("Failed to save tuning", err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleNuclearReset = async () => {
    const confirmed = window.confirm(
      "⚠️ NUCLEAR RESET\n\nThis will permanently destroy ALL workspaces, files, vector embeddings, and chat history for your session.\n\nThis action CANNOT be undone. Are you absolutely sure?"
    );
    if (!confirmed) return;

    setIsResetting(true);
    try {
      const res = await apiClient.post("/settings/reset");
      const count = res.data?.destroyed_count || 0;
      alert(`✅ Nuclear Reset complete. ${count} workspace(s) destroyed.`);
      onResetComplete();
      onClose();
    } catch (err) {
      console.error("Nuclear reset failed", err);
      alert("❌ Nuclear Reset failed. Check console for details.");
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          />

          {/* Panel */}
          <motion.div
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="fixed right-0 top-0 h-full w-[420px] glass bg-[#12141a]/95 border-l border-white/10 z-50 flex flex-col shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-white/10">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-600/30 flex items-center justify-center">
                  <Cpu size={16} className="text-indigo-400" />
                </div>
                <h2 className="text-lg font-semibold text-white/90">Settings</h2>
              </div>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              >
                <X size={18} className="text-white/50" />
              </motion.button>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
              {/* ─── Section 1: System Info ─── */}
              <div>
                <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3">
                  System Information
                </h3>
                <div className="space-y-2">
                  <InfoBadge
                    icon={<Brain size={14} />}
                    label="Generation"
                    value={info ? `${info.generation_backend} → ${info.generation_model}` : "Loading..."}
                    color="indigo"
                  />
                  <InfoBadge
                    icon={<Layers size={14} />}
                    label="Embedding"
                    value={info ? `${info.embedding_backend} → ${info.embedding_model}` : "Loading..."}
                    color="emerald"
                  />
                  <InfoBadge
                    icon={<Database size={14} />}
                    label="Vector DB"
                    value={info?.vector_db_backend || "Loading..."}
                    color="amber"
                  />
                  <InfoBadge
                    icon={<Search size={14} />}
                    label="Reranker"
                    value={info?.reranker_backend || "Loading..."}
                    color="cyan"
                  />
                  <InfoBadge
                    icon={<Server size={14} />}
                    label="Database"
                    value={info ? `${info.database_name} @ ${info.database_uri.split("@").pop()}` : "Loading..."}
                    color="violet"
                  />
                </div>
              </div>

              {/* ─── Section 2: Live Tuning ─── */}
              <div>
                <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3">
                  Live Tuning
                </h3>
                <div className="space-y-4">
                  {/* Temperature */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Thermometer size={14} className="text-orange-400" />
                        <span className="text-xs text-white/70">Temperature</span>
                      </div>
                      <span className="text-xs font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-md">
                        {tuning.temperature.toFixed(1)}
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="2"
                      step="0.1"
                      value={tuning.temperature}
                      onChange={(e) =>
                        setTuning((prev) => ({ ...prev, temperature: parseFloat(e.target.value) }))
                      }
                      className="w-full h-1.5 rounded-full appearance-none cursor-pointer accent-indigo-500 bg-white/10"
                    />
                    <div className="flex justify-between text-[10px] text-white/30">
                      <span>Precise</span>
                      <span>Creative</span>
                    </div>
                  </div>

                  {/* Retrieval Limit */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FileText size={14} className="text-emerald-400" />
                        <span className="text-xs text-white/70">Retrieval Limit</span>
                      </div>
                      <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md">
                        {tuning.retrieval_limit}
                      </span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="20"
                      step="1"
                      value={tuning.retrieval_limit}
                      onChange={(e) =>
                        setTuning((prev) => ({ ...prev, retrieval_limit: parseInt(e.target.value) }))
                      }
                      className="w-full h-1.5 rounded-full appearance-none cursor-pointer accent-emerald-500 bg-white/10"
                    />
                    <div className="flex justify-between text-[10px] text-white/30">
                      <span>Focused (1)</span>
                      <span>Broad (20)</span>
                    </div>
                  </div>

                  {/* Max Output Tokens */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Cpu size={14} className="text-violet-400" />
                        <span className="text-xs text-white/70">Max Output Tokens</span>
                      </div>
                      <input
                        type="number"
                        min="64"
                        max="65536"
                        value={tuning.max_output_tokens}
                        onChange={(e) =>
                          setTuning((prev) => ({ ...prev, max_output_tokens: parseInt(e.target.value) || 2048 }))
                        }
                        className="w-24 text-xs font-mono text-violet-400 bg-violet-500/10 px-2 py-1 rounded-md border border-violet-500/20 text-right outline-none focus:border-violet-500/50"
                      />
                    </div>
                  </div>

                  {/* Apply Button */}
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleApplyTuning}
                    disabled={isSaving}
                    className={`w-full py-2.5 rounded-xl flex items-center justify-center gap-2 text-sm font-medium transition-all ${
                      saveSuccess
                        ? "bg-emerald-600/30 border border-emerald-500/40 text-emerald-200"
                        : "bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/30 text-indigo-100"
                    }`}
                  >
                    {isSaving ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : saveSuccess ? (
                      <Check size={14} />
                    ) : null}
                    {saveSuccess ? "Applied!" : "Apply Changes"}
                  </motion.button>
                </div>
              </div>

              {/* ─── Section 3: Danger Zone ─── */}
              <div>
                <h3 className="text-[10px] font-bold text-red-400/60 uppercase tracking-widest mb-3">
                  Danger Zone
                </h3>
                <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/5">
                  <div className="flex items-start gap-3 mb-3">
                    <AlertTriangle size={16} className="text-red-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-white/70 leading-relaxed">
                        This will permanently destroy <strong className="text-red-300">all workspaces</strong>, uploaded files,
                        vector embeddings, and chat history for your current session.
                      </p>
                    </div>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleNuclearReset}
                    disabled={isResetting}
                    className="w-full py-2.5 bg-red-600/20 hover:bg-red-600/40 border border-red-500/30 text-red-200 rounded-xl flex items-center justify-center gap-2 text-sm font-medium transition-all"
                  >
                    {isResetting ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <AlertTriangle size={14} />
                    )}
                    {isResetting ? "Destroying..." : "Nuclear Reset"}
                  </motion.button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

/* ─── Info Badge Sub-Component ─── */
function InfoBadge({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}) {
  const colorMap: Record<string, string> = {
    indigo: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
    emerald: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    amber: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    cyan: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
    violet: "text-violet-400 bg-violet-500/10 border-violet-500/20",
  };

  return (
    <div className={`flex items-center gap-3 p-2.5 rounded-lg border ${colorMap[color] || colorMap.indigo}`}>
      <div className={colorMap[color]?.split(" ")[0]}>{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-[10px] text-white/40 uppercase tracking-wider">{label}</p>
        <p className="text-xs text-white/80 truncate">{value}</p>
      </div>
    </div>
  );
}
