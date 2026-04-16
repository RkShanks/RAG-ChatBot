"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, User, Sparkles } from "lucide-react";

export function ChatBox() {
  const [messages, setMessages] = useState<{role: "system"|"user", text: string}[]>([
    { role: "system", text: "Hello! I am Nimo. I have access to your uploaded corporate documentation. How can I assist you today?" }
  ]);
  const [inputTitle, setInputTitle] = useState("");

  const handleSend = () => {
    if(!inputTitle.trim()) return;
    setMessages([...messages, { role: "user", text: inputTitle }]);
    setInputTitle("");
    
    // Mock response simulating streaming delay
    setTimeout(() => {
      setMessages(prev => [...prev, { role: "system", text: "Based on the retrieved context, this is a mock streamed response demonstrating the glassmorphic chat interface." }]);
    }, 1000);
  };

  return (
    <div className="flex-1 flex flex-col h-full relative">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
              key={i}
              className={`flex gap-4 max-w-4xl mx-auto w-full ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 border ${msg.role === "system" ? "bg-indigo-500/10 border-indigo-500/30" : "bg-emerald-500/10 border-emerald-500/30"}`}>
                {msg.role === "system" ? <Bot size={20} className="text-indigo-400" /> : <User size={20} className="text-emerald-400" />}
              </div>
              <div className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                <div className={`p-4 rounded-2xl glass font-light leading-relaxed text-sm shadow-xl ${msg.role === "user" ? "bg-emerald-900/10 border-emerald-500/20 text-emerald-50" : "bg-indigo-900/10 border-indigo-500/20 text-indigo-50"}`}>
                  {msg.text}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Input Area */}
      <div className="p-6 max-w-4xl mx-auto w-full">
        <div className="glass rounded-2xl p-2 pl-4 flex items-center gap-3 border border-white/10 shadow-[0_4px_30px_rgba(0,0,0,0.1)] hover:border-indigo-500/30 transition-colors focus-within:border-indigo-500/50">
          <Sparkles size={18} className="text-indigo-400 shrink-0" />
          <input 
            value={inputTitle}
            onChange={(e) => setInputTitle(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask Nimo about your policies..."
            className="flex-1 bg-transparent border-none outline-none text-white/90 font-light placeholder:text-white/30"
          />
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleSend}
            className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center shadow-[0_0_15px_rgba(79,70,229,0.3)] hover:bg-indigo-500 transition-colors"
          >
            <Send size={16} className="text-white ml-0.5" />
          </motion.button>
        </div>
        <div className="text-center mt-3 text-[10px] text-white/30 uppercase tracking-widest font-semibold flex items-center justify-center gap-1">
           Powered by Secure Vector Isolation 
        </div>
      </div>
    </div>
  );
}
