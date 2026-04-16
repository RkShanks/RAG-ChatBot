import { Sidebar } from "./components/Sidebar";
import { ChatBox } from "./components/ChatBox";

export default function Home() {
  return (
    <main className="flex h-screen w-screen overflow-hidden bg-[var(--background)]">
      {/* Background ambient lighting effects */}
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none -z-10" />
      <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-emerald-600/10 rounded-full blur-[120px] pointer-events-none -z-10" />
      
      <Sidebar />
      <ChatBox />
    </main>
  );
}
