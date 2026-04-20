"use client";

import { useState, useEffect, useRef } from "react";
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
  Key,
  Globe,
  Link,
  ChevronDown,
  XCircle,
  User,
  Pencil,
  CloudUpload,
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

type ProviderCatalog = {
  generation_providers: string[];
  generation_models: Record<string, string[]>;
  embedding_providers: string[];
  embedding_models: Record<string, string[]>;
};

type MaskedKeys = {
  keys: Record<string, string>;
  urls: Record<string, string>;
};

export type UserProfile = {
  session_id: string;
  display_name: string;
  avatar_color: string;
  avatar_base64?: string;
};

export function SettingsPanel({
  isOpen,
  onClose,
  onResetComplete,
  userProfile,
  onProfileUpdate,
}: {
  isOpen: boolean;
  onClose: () => void;
  onResetComplete: () => void;
  userProfile: UserProfile | null;
  onProfileUpdate: (profile: UserProfile) => void;
}) {
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [tuning, setTuning] = useState<TuningValues>({
    temperature: 0.1,
    retrieval_limit: 5,
    max_output_tokens: 32768,
  });
  const [catalog, setCatalog] = useState<ProviderCatalog | null>(null);
  const [maskedKeys, setMaskedKeys] = useState<MaskedKeys | null>(null);

  // Provider config state
  const [genBackend, setGenBackend] = useState("");
  const [genModel, setGenModel] = useState("");
  const [genCustomModel, setGenCustomModel] = useState("");
  const [embBackend, setEmbBackend] = useState("");
  const [embModel, setEmbModel] = useState("");
  const [embCustomModel, setEmbCustomModel] = useState("");
  const [openaiBaseUrl, setOpenaiBaseUrl] = useState("");

  // API Key state
  const [genApiKey, setGenApiKey] = useState("");
  const [embApiKey, setEmbApiKey] = useState("");

  // Profile editing state
  const [isEditingName, setIsEditingName] = useState(false);
  const [editName, setEditName] = useState("");
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isSwapping, setIsSwapping] = useState(false);
  const [swapSuccess, setSwapSuccess] = useState(false);
  const [swapError, setSwapError] = useState("");

  const fetchAllData = async () => {
    try {
      const [infoRes, tuningRes, provRes, keysRes] = await Promise.all([
        apiClient.get("/settings/info"),
        apiClient.get("/settings/tuning"),
        apiClient.get("/settings/providers"),
        apiClient.get("/settings/keys"),
      ]);
      if (infoRes.data?.info) {
        setInfo(infoRes.data.info);
        setGenBackend(infoRes.data.info.generation_backend);
        setGenModel(infoRes.data.info.generation_model);
        setEmbBackend(infoRes.data.info.embedding_backend);
        setEmbModel(infoRes.data.info.embedding_model);
      }
      if (tuningRes.data?.tuning) setTuning(tuningRes.data.tuning);
      if (provRes.data) setCatalog(provRes.data);
      if (keysRes.data) {
        setMaskedKeys(keysRes.data);
        setOpenaiBaseUrl(keysRes.data.urls?.openai_base_url || "");
      }
    } catch (err) {
      console.warn("Failed to fetch settings", err);
    }
  };

  useEffect(() => {
    if (!isOpen) return;
    fetchAllData();
  }, [isOpen]);

  // Sync edit name with profile
  useEffect(() => {
    if (userProfile) {
      setEditName(userProfile.display_name || "");
    }
  }, [userProfile]);

  // When generation backend changes, reset the model to first in list
  useEffect(() => {
    if (catalog && genBackend) {
      const models = catalog.generation_models[genBackend] || [];
      if (models.length > 0 && !models.includes(genModel)) {
        setGenModel(models[0]);
      }
      setGenCustomModel("");
    }
  }, [genBackend]);

  useEffect(() => {
    if (catalog && embBackend) {
      const models = catalog.embedding_models[embBackend] || [];
      if (models.length > 0 && !models.includes(embModel)) {
        setEmbModel(models[0]);
      }
      setEmbCustomModel("");
    }
  }, [embBackend]);

  const handleSaveDisplayName = async () => {
    setIsSavingProfile(true);
    try {
      const res = await apiClient.put("/settings/profile", {
        display_name: editName,
      });
      if (res.data?.profile) {
        onProfileUpdate(res.data.profile);
      }
      setIsEditingName(false);
    } catch (err) {
      console.error("Failed to save display name", err);
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploadingAvatar(true);
    try {
      const reader = new FileReader();
      const img = new Image();
      reader.onload = (evt) => {
        img.onload = async () => {
          const canvas = document.createElement("canvas");
          const MAX_SIZE = 150;
          let width = img.width;
          let height = img.height;

          if (width > height) {
            if (width > MAX_SIZE) {
              height *= MAX_SIZE / width;
              width = MAX_SIZE;
            }
          } else {
            if (height > MAX_SIZE) {
              width *= MAX_SIZE / height;
              height = MAX_SIZE;
            }
          }

          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext("2d");
          ctx?.drawImage(img, 0, 0, width, height);

          const base64Avatar = canvas.toDataURL("image/jpeg", 0.8);

          try {
             const res = await apiClient.put("/settings/profile", {
               avatar_base64: base64Avatar,
             });
             if (res.data?.profile) {
               onProfileUpdate(res.data.profile);
             }
          } catch(err) {
             console.error("Failed to upload avatar", err);
          } finally {
             setIsUploadingAvatar(false);
          }
        };
        img.src = evt.target?.result as string;
      };
      reader.readAsDataURL(file);
    } catch (err) {
      console.error(err);
      setIsUploadingAvatar(false);
    }
    
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

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

  const handleApplyProvider = async () => {
    setIsSwapping(true);
    setSwapSuccess(false);
    setSwapError("");
    try {
      const payload: Record<string, string> = {
        generation_backend: genBackend,
        generation_model: genCustomModel || genModel,
        embedding_backend: embBackend,
        embedding_model: embCustomModel || embModel,
      };
      if (genApiKey) payload.generation_api_key = genApiKey;
      if (embApiKey) payload.embedding_api_key = embApiKey;
      if (openaiBaseUrl) payload.openai_base_url = openaiBaseUrl;

      const res = await apiClient.put("/settings/provider", payload);
      if (res.data?.signal === "success") {
        setSwapSuccess(true);
        setGenApiKey("");
        setEmbApiKey("");
        // Refresh info to reflect change
        const newInfo = await apiClient.get("/settings/info");
        if (newInfo.data?.info) setInfo(newInfo.data.info);
        const newKeys = await apiClient.get("/settings/keys");
        if (newKeys.data) setMaskedKeys(newKeys.data);
        setTimeout(() => setSwapSuccess(false), 3000);
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail || "Unknown error";
      setSwapError(detail);
      setTimeout(() => setSwapError(""), 5000);
    } finally {
      setIsSwapping(false);
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

  const showOpenaiUrl = genBackend === "OPENAI" || embBackend === "OPENAI";
  const genModels = catalog?.generation_models[genBackend] || [];
  const embModels = catalog?.embedding_models[embBackend] || [];
  const providers = (catalog?.generation_providers || []).filter((p) => p !== "LOCAL");

  // Avatar helpers
  const getInitials = (name: string) => {
    if (!name || !name.trim()) return "?";
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return parts[0][0].toUpperCase();
  };

  const displayName = userProfile?.display_name || "";
  const avatarColor = userProfile?.avatar_color || "hsl(220, 70%, 50%)";

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          />
          <motion.div
            initial={{ x: 450, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 450, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="fixed right-0 top-0 h-full w-[450px] glass bg-[#12141a]/95 border-l border-white/10 z-50 flex flex-col shadow-2xl"
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

            <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
              {/* ─── Section 0: User Profile ─── */}
              <div>
                <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                  <User size={10} /> User Profile
                </h3>
                <input 
                  type="file" 
                  accept="image/png, image/jpeg, image/webp" 
                  ref={fileInputRef}
                  style={{ display: "none" }}
                  onChange={handleAvatarUpload}
                />
                <div className="flex items-center gap-4 p-4 rounded-xl border border-white/10 bg-white/[0.02]">
                  {/* Avatar Circle */}
                  <div
                    onClick={() => !isUploadingAvatar && fileInputRef.current?.click()}
                    className={`w-14 h-14 rounded-full flex items-center justify-center shrink-0 shadow-lg ring-2 ring-white/10 transition-all cursor-pointer relative overflow-hidden group ${
                      isUploadingAvatar ? "opacity-50 pointer-events-none" : "hover:ring-indigo-500/50"
                    }`}
                    style={!userProfile?.avatar_base64 ? { backgroundColor: avatarColor } : undefined}
                  >
                    {userProfile?.avatar_base64 ? (
                      <img src={userProfile.avatar_base64} alt="User Avatar" className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-lg font-bold text-white/90 select-none">
                        {getInitials(displayName)}
                      </span>
                    )}

                    {!isUploadingAvatar && (
                      <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                         <CloudUpload size={16} className="text-white" />
                      </div>
                    )}
                    {isUploadingAvatar && (
                      <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                         <Loader2 size={16} className="text-white animate-spin" />
                      </div>
                    )}
                  </div>

                  {/* Name + Edit */}
                  <div className="flex-1 min-w-0">
                    {isEditingName ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") handleSaveDisplayName();
                            if (e.key === "Escape") {
                              setIsEditingName(false);
                              setEditName(displayName);
                            }
                          }}
                          maxLength={50}
                          autoFocus
                          placeholder="Enter your name..."
                          className="flex-1 bg-white/5 border border-indigo-500/30 rounded-lg px-3 py-1.5 text-sm text-white/90 outline-none focus:border-indigo-500/60 placeholder:text-white/20"
                        />
                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={handleSaveDisplayName}
                          disabled={isSavingProfile}
                          className="p-1.5 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/30 transition-colors"
                        >
                          {isSavingProfile ? (
                            <Loader2 size={14} className="text-indigo-400 animate-spin" />
                          ) : (
                            <Check size={14} className="text-indigo-400" />
                          )}
                        </motion.button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-white/85 truncate">
                            {displayName || "Anonymous User"}
                          </p>
                          <p className="text-[10px] text-white/30 truncate mt-0.5">
                            {userProfile?.session_id
                              ? `Session: ${userProfile.session_id.substring(0, 8)}...`
                              : "Loading..."}
                          </p>
                        </div>
                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => setIsEditingName(true)}
                          className="p-1.5 rounded-lg hover:bg-white/10 transition-colors shrink-0"
                        >
                          <Pencil size={12} className="text-white/40" />
                        </motion.button>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* ─── Section 1: System Info ─── */}
              <div>
                <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3">
                  System Information
                </h3>
                <div className="space-y-2">
                  <InfoBadge icon={<Brain size={14} />} label="Generation" value={info ? `${info.generation_backend} → ${info.generation_model}` : "Loading..."} color="indigo" />
                  <InfoBadge icon={<Layers size={14} />} label="Embedding" value={info ? `${info.embedding_backend} → ${info.embedding_model}` : "Loading..."} color="emerald" />
                  <InfoBadge icon={<Database size={14} />} label="Vector DB" value={info?.vector_db_backend || "Loading..."} color="amber" />
                  <InfoBadge icon={<Search size={14} />} label="Reranker" value={info?.reranker_backend || "Loading..."} color="cyan" />
                  <InfoBadge icon={<Server size={14} />} label="Database" value={info ? `${info.database_name} @ ${info.database_uri.split("@").pop()}` : "Loading..."} color="violet" />
                </div>
              </div>

              {/* ─── Section 2: Provider Configuration ─── */}
              <div>
                <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3">
                  Provider Configuration
                </h3>
                <div className="space-y-3">
                  {/* Generation Provider */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] text-white/50 uppercase tracking-wider">Generation Provider</label>
                    <div className="relative">
                      <select
                        value={genBackend}
                        onChange={(e) => setGenBackend(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 appearance-none outline-none focus:border-indigo-500/50 cursor-pointer"
                      >
                        {providers.map((p) => (
                          <option key={p} value={p} className="bg-[#1a1d24]">{p}</option>
                        ))}
                      </select>
                      <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 pointer-events-none" />
                    </div>
                  </div>

                  {/* Generation Model */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] text-white/50 uppercase tracking-wider">Generation Model</label>
                    <div className="relative">
                      <select
                        value={genModel}
                        onChange={(e) => setGenModel(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 appearance-none outline-none focus:border-indigo-500/50 cursor-pointer"
                      >
                        {genModels.map((m) => (
                          <option key={m} value={m} className="bg-[#1a1d24]">{m}</option>
                        ))}
                      </select>
                      <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 pointer-events-none" />
                    </div>
                    <input
                      type="text"
                      placeholder="Or type custom model name..."
                      value={genCustomModel}
                      onChange={(e) => setGenCustomModel(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/60 outline-none focus:border-indigo-500/50 placeholder:text-white/20"
                    />
                  </div>

                  <div className="border-t border-white/5 my-2" />

                  {/* Embedding Provider */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] text-white/50 uppercase tracking-wider">Embedding Provider</label>
                    <div className="relative">
                      <select
                        value={embBackend}
                        onChange={(e) => setEmbBackend(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 appearance-none outline-none focus:border-emerald-500/50 cursor-pointer"
                      >
                        {providers.map((p) => (
                          <option key={p} value={p} className="bg-[#1a1d24]">{p}</option>
                        ))}
                      </select>
                      <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 pointer-events-none" />
                    </div>
                  </div>

                  {/* Embedding Model */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] text-white/50 uppercase tracking-wider">Embedding Model</label>
                    <div className="relative">
                      <select
                        value={embModel}
                        onChange={(e) => setEmbModel(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 appearance-none outline-none focus:border-emerald-500/50 cursor-pointer"
                      >
                        {embModels.map((m) => (
                          <option key={m} value={m} className="bg-[#1a1d24]">{m}</option>
                        ))}
                      </select>
                      <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 pointer-events-none" />
                    </div>
                    <input
                      type="text"
                      placeholder="Or type custom model name..."
                      value={embCustomModel}
                      onChange={(e) => setEmbCustomModel(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/60 outline-none focus:border-emerald-500/50 placeholder:text-white/20"
                    />
                  </div>

                  {/* OpenAI Base URL */}
                  {showOpenaiUrl && (
                    <div className="space-y-1.5">
                      <label className="text-[10px] text-white/50 uppercase tracking-wider flex items-center gap-1">
                        <Globe size={10} /> OpenAI Base URL
                      </label>
                      <input
                        type="text"
                        placeholder="https://api.openai.com/v1 (or Ollama/vLLM URL)"
                        value={openaiBaseUrl}
                        onChange={(e) => setOpenaiBaseUrl(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/70 outline-none focus:border-amber-500/50 placeholder:text-white/20"
                      />
                      <p className="text-[10px] text-white/25">For local models: http://localhost:11434/v1</p>
                    </div>
                  )}
                </div>
              </div>

              {/* ─── Section 3: API Keys ─── */}
              <div>
                <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                  <Key size={10} /> API Keys
                </h3>
                <div className="space-y-3">
                  <KeyInput
                    label={`${genBackend} Key (Generation)`}
                    masked={maskedKeys?.keys?.[genBackend.toLowerCase()] || "Not Set"}
                    value={genApiKey}
                    onChange={setGenApiKey}
                  />
                  {embBackend !== genBackend && (
                    <KeyInput
                      label={`${embBackend} Key (Embedding)`}
                      masked={maskedKeys?.keys?.[embBackend.toLowerCase()] || "Not Set"}
                      value={embApiKey}
                      onChange={setEmbApiKey}
                    />
                  )}
                </div>
              </div>

              {/* Apply Provider Button */}
              <div>
                {swapError && (
                  <div className="flex items-center gap-2 p-2.5 rounded-lg bg-red-500/10 border border-red-500/20 mb-3">
                    <XCircle size={14} className="text-red-400 shrink-0" />
                    <p className="text-[11px] text-red-300 leading-snug">{swapError}</p>
                  </div>
                )}
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleApplyProvider}
                  disabled={isSwapping}
                  className={`w-full py-2.5 rounded-xl flex items-center justify-center gap-2 text-sm font-medium transition-all ${
                    swapSuccess
                      ? "bg-emerald-600/30 border border-emerald-500/40 text-emerald-200"
                      : "bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/30 text-indigo-100"
                  }`}
                >
                  {isSwapping ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : swapSuccess ? (
                    <Check size={14} />
                  ) : null}
                  {swapSuccess ? "Provider Swapped!" : "Apply Provider & Keys"}
                </motion.button>
              </div>

              {/* ─── Section 4: Connection URLs ─── */}
              <div>
                <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                  <Link size={10} /> Connection URLs
                </h3>
                <div className="space-y-2">
                  <InfoBadge icon={<Database size={14} />} label="Qdrant" value={maskedKeys?.urls?.qdrant_url || "Not Set"} color="amber" />
                  <InfoBadge icon={<Server size={14} />} label="MongoDB" value={maskedKeys?.urls?.mongodb_uri || "Not Set"} color="violet" />
                </div>
              </div>

              {/* ─── Section 5: Live Tuning ─── */}
              <div>
                <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3">
                  Live Tuning
                </h3>
                <div className="space-y-4">
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
                    <input type="range" min="0" max="2" step="0.1" value={tuning.temperature}
                      onChange={(e) => setTuning((prev) => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                      className="w-full h-1.5 rounded-full appearance-none cursor-pointer accent-indigo-500 bg-white/10" />
                    <div className="flex justify-between text-[10px] text-white/30">
                      <span>Precise</span><span>Creative</span>
                    </div>
                  </div>

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
                    <input type="range" min="1" max="20" step="1" value={tuning.retrieval_limit}
                      onChange={(e) => setTuning((prev) => ({ ...prev, retrieval_limit: parseInt(e.target.value) }))}
                      className="w-full h-1.5 rounded-full appearance-none cursor-pointer accent-emerald-500 bg-white/10" />
                    <div className="flex justify-between text-[10px] text-white/30">
                      <span>Focused (1)</span><span>Broad (20)</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Cpu size={14} className="text-violet-400" />
                        <span className="text-xs text-white/70">Max Output Tokens</span>
                      </div>
                      <input type="number" min="64" max="65536" value={tuning.max_output_tokens}
                        onChange={(e) => setTuning((prev) => ({ ...prev, max_output_tokens: parseInt(e.target.value) || 2048 }))}
                        className="w-24 text-xs font-mono text-violet-400 bg-violet-500/10 px-2 py-1 rounded-md border border-violet-500/20 text-right outline-none focus:border-violet-500/50" />
                    </div>
                  </div>

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
                    {isSaving ? <Loader2 size={14} className="animate-spin" /> : saveSuccess ? <Check size={14} /> : null}
                    {saveSuccess ? "Applied!" : "Apply Tuning"}
                  </motion.button>
                </div>
              </div>

              {/* ─── Section 6: Danger Zone ─── */}
              <div>
                <h3 className="text-[10px] font-bold text-red-400/60 uppercase tracking-widest mb-3">Danger Zone</h3>
                <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/5">
                  <div className="flex items-start gap-3 mb-3">
                    <AlertTriangle size={16} className="text-red-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-white/70 leading-relaxed">
                      This will permanently destroy <strong className="text-red-300">all workspaces</strong>, uploaded files,
                      vector embeddings, and chat history for your current session.
                    </p>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleNuclearReset}
                    disabled={isResetting}
                    className="w-full py-2.5 bg-red-600/20 hover:bg-red-600/40 border border-red-500/30 text-red-200 rounded-xl flex items-center justify-center gap-2 text-sm font-medium transition-all"
                  >
                    {isResetting ? <Loader2 size={14} className="animate-spin" /> : <AlertTriangle size={14} />}
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

/* ─── Sub-Components ─── */

function InfoBadge({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
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

function KeyInput({ label, masked, value, onChange }: { label: string; masked: string; value: string; onChange: (v: string) => void }) {
  return (
    <div className="space-y-1">
      <label className="text-[10px] text-white/50 uppercase tracking-wider">{label}</label>
      <div className="relative">
        <input
          type="password"
          placeholder={masked}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/70 outline-none focus:border-amber-500/50 placeholder:text-white/30"
        />
        <Key size={12} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/20" />
      </div>
    </div>
  );
}
