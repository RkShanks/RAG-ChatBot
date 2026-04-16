"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, User, Sparkles } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Message = {
  role: "system" | "user";
  text: string;
};

export function ChatBox() {
  const [messages, setMessages] = useState<Message[]>([
    { 
      role: "system", 
      text: "Hello! I am **Nimo**. I have access to your uploaded corporate documentation via strict _Hybrid Vector Search_ constraints.\n\n### How can I assist you today?\n- **Summarize** a loaded file.\n- **Extract** key numerical data.\n- **Search** for precise institutional knowledge."
    }
  ]);
  const [inputTitle, setInputTitle] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = () => {
    if(!inputTitle.trim()) return;
    setMessages(prev => [...prev, { role: "user", text: inputTitle }]);
    setInputTitle("");
    setIsTyping(true);
    
    // Mock response simulating backend delay
    setTimeout(() => {
      setIsTyping(false);
      setMessages(prev => [...prev, { 
        role: "system", 
        text: "Based on the retrieved context, this is a mock streamed response formatted with **React Markdown**. \n\n```python\nprint('This supports code blocks natively for a ChatGPT-like experience!')\n```\n\n> This ensures our RAG infrastructure formats outputs professionally before rendering it to the DOM."
      }]);
    }, 1500);
  };

  return (
    <div className="flex-1 flex flex-col h-full relative">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-8 space-y-8">
        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: "spring", stiffness: 200, damping: 20 }}
              key={i}
              className={`flex gap-4 max-w-4xl mx-auto w-full ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 border mt-1 shadow-lg ${msg.role === "system" ? "bg-indigo-500/10 border-indigo-500/30" : "bg-emerald-500/10 border-emerald-500/30"}`}>
                {msg.role === "system" ? <Bot size={20} className="text-indigo-400" /> : <User size={20} className="text-emerald-400" />}
              </div>
              
              <div className={`flex flex-col max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                <div className={`
                  p-5 rounded-2xl glass shadow-xl
                  ${msg.role === "user" ? "bg-emerald-900/20 border-emerald-500/20 text-emerald-50 rounded-tr-sm" : "bg-indigo-900/10 border-indigo-500/30 text-indigo-50 rounded-tl-sm w-full"}
                `}>
                  {/* Markdown Renderer for Desktop-Class Output formatting */}
                  <div className={`prose prose-invert max-w-none text-sm font-light leading-relaxed prose-p:leading-relaxed prose-pre:bg-black/40 prose-pre:border prose-pre:border-white/10 prose-pre:shadow-lg prose-code:text-indigo-300 ${msg.role === "user" ? "" : ""}`}>
                     <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.text}
                     </ReactMarkdown>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
          
          {/* Typing Indicator */}
          {isTyping && (
             <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-4 max-w-4xl mx-auto w-full flex-row"
             >
                <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 border mt-1 bg-indigo-500/10 border-indigo-500/30">
                  <Bot size={20} className="text-indigo-400" />
                </div>
                <div className="p-4 rounded-2xl glass bg-indigo-900/10 border-indigo-500/20 flex items-center gap-2">
                   <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 1 }} className="w-2 h-2 rounded-full bg-indigo-400" />
                   <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 1, delay: 0.2 }} className="w-2 h-2 rounded-full bg-indigo-400" />
                   <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 1, delay: 0.4 }} className="w-2 h-2 rounded-full bg-indigo-400" />
                </div>
             </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input Box Area */}
      <div className="p-6 max-w-4xl mx-auto w-full relative z-20">
        <div className="glass bg-[#1a1d24]/80 rounded-2xl p-2 pl-4 flex items-center gap-3 border border-white/10 shadow-[0_-5px_30px_rgba(0,0,0,0.2)] focus-within:border-indigo-500/50 transition-all">
          <Sparkles size={18} className="text-indigo-400 shrink-0" />
          <input 
            value={inputTitle}
            onChange={(e) => setInputTitle(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask Nimo about your semantic documents..."
            className="flex-1 bg-transparent border-none outline-none text-white/90 font-light placeholder:text-white/30"
            disabled={isTyping}
          />
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleSend}
            disabled={!inputTitle.trim() || isTyping}
            className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-[0_0_15px_rgba(79,70,229,0.3)] transition-colors
              ${(!inputTitle.trim() || isTyping) ? "bg-white/5 cursor-not-allowed hidden" : "bg-indigo-600 hover:bg-indigo-500 "}
            `}
          >
            <Send size={16} className="text-white ml-0.5" />
          </motion.button>
        </div>
        <div className="text-center mt-3 text-[10px] text-white/30 uppercase tracking-widest font-semibold flex items-center justify-center gap-2">
           <span>Powered by Strict Security UUID Isolation</span>
        </div>
      </div>
    </div>
  );
}
