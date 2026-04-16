"use client";

import { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { ChatBox } from "./components/ChatBox";

export default function Home() {
  const [activeProjectId, setActiveProjectId] = useState("defaultworkspace");

  return (
    <main className="flex h-screen w-screen overflow-hidden bg-[var(--background)] relative">
      {/* Dynamic Background Effects */}
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-emerald-600/10 rounded-full blur-[120px] pointer-events-none z-0" />
      
      {/* Toast Notification Container Anchor */}
      <div id="toast-root" className="absolute top-4 right-4 z-50 flex flex-col gap-2" />

      <Sidebar activeProjectId={activeProjectId} />
      <ChatBox activeProjectId={activeProjectId} />
    </main>
  );
}
