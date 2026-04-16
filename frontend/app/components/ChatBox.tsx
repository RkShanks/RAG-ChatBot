"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, User, Sparkles } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getSessionId } from "../lib/api";
import { useErrorToast } from "../lib/ToastContext";

type Message = {
  role: "system" | "user" | "error";
  text: string;
};

export function ChatBox({ activeProjectId }: { activeProjectId: string }) {
  const [messages, setMessages] = useState<Message[]>([
    { 
      role: "system", 
      text: "Hello! I am **Nimo**. I have access to your uploaded corporate documentation via strict _Hybrid Vector Search_ constraints.\n\n### How can I assist you today?\n- **Summarize** a loaded file.\n- **Extract** key numerical data.\n- **Search** for precise institutional knowledge."
    }
  ]);
  const [inputTitle, setInputTitle] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const { triggerToast } = useErrorToast();
  
  // Create a ref attached to the message container to allow auto-scrolling
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });

  const handleSend = async () => {
    if(!inputTitle.trim() || isTyping) return;
    const userText = inputTitle;
    
    setMessages(prev => [...prev, { role: "user", text: userText }]);
    setInputTitle("");
    setIsTyping(true);
    
    // Add empty system message to hold incoming streamed chunks
    setMessages(prev => [...prev, { role: "system", text: "" }]);
    
    setTimeout(scrollToBottom, 100);

    try {
      const sessionId = getSessionId();
      // Use native fetch to consume Server-Sent Events (SSE) from a POST endpoint!
      const response = await fetch(`http://localhost:8000/api/v1/nlp/ask/stream/${activeProjectId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-ID": sessionId
        },
        body: JSON.stringify({ query: userText, limit: 5 })
      });

      if (!response.body) throw new Error("ReadableStream not supported in this browser.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let streamBuffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        streamBuffer += decoder.decode(value, { stream: true });
        
        // SSE messages are separated by double newlines
        const lines = streamBuffer.split('\n\n');
        
        // Pop the last element (it might be incomplete data)
        streamBuffer = lines.pop() || "";
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.substring(6);
            if (dataStr.trim() === "[DONE]") break;
            
            try {
              const data = JSON.parse(dataStr);
              if (data.type === "answer" || data.type === "chunk") {
                setIsTyping(false); // Hide the 3 bouncing dots as soon as real text starts rendering
                setMessages(prev => {
                  const newArr = [...prev];
                  // Append streamed chunk directly to latest system message
                  newArr[newArr.length - 1].text += (data.text || "");
                  return newArr;
                });
                scrollToBottom();
              } else if (data.type === "error") {
                // Render custom Error Exception signal safely out of the RAG context
                setMessages(prev => {
                  const newArr = [...prev];
                  newArr[newArr.length - 1].role = "error";
                  newArr[newArr.length - 1].text = `**Vector Search Exception:** ${data.text}`;
                  return newArr;
                });
              }
            } catch(e) {
              console.warn("Failed to parse SSE data chunk", e);
            }
          }
        }
      }
    } catch (err: any) {
      console.error(err);
      triggerToast(err.message || "Network Failure: Unable to connect to the FastAPI layer.");
      setMessages(prev => [...prev, { role: "error", text: "**Network Failure**: Unable to connect to the backend APIs." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full relative z-10">
      <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: "spring", stiffness: 200, damping: 20 }}
              key={i}
              className={`flex gap-4 max-w-4xl mx-auto w-full ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 border mt-1 shadow-lg ${msg.role === "system" ? "bg-indigo-500/10 border-indigo-500/30" : msg.role === "error" ? "bg-red-500/10 border-red-500/30" : "bg-emerald-500/10 border-emerald-500/30"}`}>
                {msg.role === "system" ? <Bot size={20} className="text-indigo-400" /> : msg.role === "error" ? <Bot size={20} className="text-red-400" /> : <User size={20} className="text-emerald-400" />}
              </div>
              
              <div className={`flex flex-col max-w-[85%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                <div className={`
                  p-5 rounded-3xl glass shadow-xl
                  ${msg.role === "user" ? "bg-emerald-900/40 border-emerald-500/30 text-emerald-50 rounded-tr-[4px]" : 
                    msg.role === "error" ? "bg-red-900/40 border-red-500/50 text-red-100 rounded-tl-[4px]" : 
                    "bg-indigo-900/20 border-indigo-500/30 text-indigo-50 rounded-tl-[4px] w-full"}
                `}>
                  <div className={`prose prose-invert max-w-none text-[15px] font-light leading-relaxed prose-p:leading-relaxed prose-pre:bg-black/60 prose-pre:border prose-pre:border-white/10 prose-pre:shadow-2xl prose-code:text-indigo-300`}>
                     <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.text || "..."}
                     </ReactMarkdown>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
          <div ref={messagesEndRef} />
          
          {isTyping && (
             <motion.div
                key="typing-indicator"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex gap-4 max-w-4xl mx-auto w-full flex-row"
             >
                <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 border mt-1 bg-indigo-500/10 border-indigo-500/30">
                  <Bot size={20} className="text-indigo-400" />
                </div>
                <div className="p-4 rounded-3xl rounded-tl-[4px] glass bg-indigo-900/20 border-indigo-500/20 flex items-center gap-2 px-5 shadow-lg">
                   <motion.div animate={{ scale: [1, 1.4, 1], opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1 }} className="w-[6px] h-[6px] rounded-full bg-indigo-400" />
                   <motion.div animate={{ scale: [1, 1.4, 1], opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1, delay: 0.2 }} className="w-[6px] h-[6px] rounded-full bg-indigo-400" />
                   <motion.div animate={{ scale: [1, 1.4, 1], opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1, delay: 0.4 }} className="w-[6px] h-[6px] rounded-full bg-indigo-400" />
                </div>
             </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="p-6 max-w-4xl mx-auto w-full relative z-20">
        <div className="glass bg-[#1a1d24]/90 rounded-3xl p-2 pl-5 flex items-center gap-3 border border-white/10 shadow-[0_-5px_40px_rgba(0,0,0,0.3)] focus-within:border-indigo-500/50 focus-within:shadow-[0_0_30px_rgba(79,70,229,0.2)] transition-all">
          <Sparkles size={20} className="text-indigo-500 shrink-0" />
          <input 
            value={inputTitle}
            onChange={(e) => setInputTitle(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Search your active knowledge base..."
            className="flex-1 bg-transparent border-none outline-none text-white/90 text-[15px] font-light placeholder:text-white/30 truncate"
            disabled={isTyping}
          />
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleSend}
            disabled={!inputTitle.trim() || isTyping}
            className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-colors shadow-lg
              ${(!inputTitle.trim() || isTyping) ? "bg-white/5 cursor-not-allowed opacity-50" : "bg-indigo-600 hover:bg-indigo-500 shadow-[0_0_20px_rgba(79,70,229,0.4)]"}
            `}
          >
            <Send size={18} className="text-white ml-0.5" />
          </motion.button>
        </div>
      </div>
    </div>
  );
}
