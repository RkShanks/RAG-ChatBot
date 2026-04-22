"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, Sparkles, Check, Copy, RefreshCw, MessageSquare, BookOpen, ChevronDown } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { apiClient, getSessionId, deleteLastInteraction } from "../lib/api";
import { useErrorToast } from "../lib/ToastContext";
import type { UserProfile } from "./SettingsPanel";function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button onClick={handleCopy} className="text-white/40 hover:text-white transition-colors" title="Copy code">
      {copied ? <Check size={14} /> : <Copy size={14} />}
    </button>
  );
}

function MessageActions({ content, role, onRegenerate, isLast }: { content: string; role: string; onRegenerate?: () => void; isLast: boolean }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity absolute -top-3 right-4 bg-[#1a1d24] border border-white/10 px-2 py-1.5 rounded-lg shadow-xl z-20">
      <button onClick={handleCopy} className="text-white/50 hover:text-white transition-colors" title="Copy text">
        {copied ? <Check size={14} /> : <Copy size={14} />}
      </button>
      {role === "system" && onRegenerate && isLast && (
        <button onClick={onRegenerate} className="text-white/50 hover:text-white transition-colors" title="Regenerate">
          <RefreshCw size={14} />
        </button>
      )}
    </div>
  );
}

type Source = {
  document: string;
  page: string | number;
  score: number;
  text: string;
};

type Message = {
  role: "system" | "user" | "error";
  text: string;
  sources?: Source[];
};

function SourceCitations({ sources }: { sources: Source[] }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="mt-3 border-t border-white/10 pt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-[10px] text-indigo-400/60 hover:text-indigo-400 flex items-center gap-1.5 transition-colors"
      >
        <BookOpen size={10} />
        {sources.length} source{sources.length !== 1 ? 's' : ''} used
        <ChevronDown size={10} className={`transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} />
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-2 space-y-1.5">
              {sources.map((s, i) => (
                <div key={i} className="p-2 bg-white/5 rounded-lg border border-white/10">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-medium text-white/60 truncate">
                      [{i + 1}] {s.document} — p.{s.page}
                    </span>
                    <span className="text-[10px] text-indigo-400 shrink-0 ml-2">
                      {(s.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-[11px] text-white/35 mt-1 line-clamp-2">{s.text}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function ChatBox({
  activeProjectId,
  userProfile,
}: {
  activeProjectId: string;
  userProfile: UserProfile | null;
}) {
  const [messages, setMessages] = useState<Message[]>([
    { 
      role: "system", 
      text: "Hello! I am **Nimo**. I have access to your uploaded corporate documentation via strict _Hybrid Vector Search_ constraints.\n\n### How can I assist you today?\n- **Summarize** a loaded file.\n- **Extract** key numerical data.\n- **Search** for precise institutional knowledge."
    }
  ]);
  const [inputTitle, setInputTitle] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const { triggerToast } = useErrorToast();

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await apiClient.get(`/nlp/history/${activeProjectId}`);
        if (res.data && res.data.history && res.data.history.length > 0) {
           const dbMessages = res.data.history.map((h: any) => ({
              role: h.role === "assistant" ? "system" : h.role,
              text: h.content,
              // Bug 3 fix: restore persisted sources so citations survive page refresh
              ...(h.sources && h.sources.length > 0 ? { sources: h.sources } : {}),
           }));
           
           setMessages([
              { 
                role: "system", 
                text: "Hello! I am **Nimo**. I have access to your uploaded corporate documentation via strict _Hybrid Vector Search_ constraints.\n\n### How can I assist you today?\n- **Summarize** a loaded file.\n- **Extract** key numerical data.\n- **Search** for precise institutional knowledge."
              },
              ...dbMessages
           ]);
           // Intelligently auto-scroll after hydration
           setTimeout(() => messagesEndRef.current?.scrollIntoView(), 150);
        } else {
             // Reset to clean slate if switching to an empty project
             setMessages([]);
        }
      } catch (err: any) {
        if(err.response?.status !== 404) {
             console.warn("Could not fetch chat history.", err);
        }
      }
    };
    fetchHistory();
  }, [activeProjectId]);
  
  // Create a ref attached to the message container to allow auto-scrolling
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });

  const handleSendMessage = async (userText: string) => {
    if(!userText.trim() || isTyping) return;
    
    setMessages(prev => [...prev, { role: "user", text: userText }]);
    setInputTitle("");
    setIsTyping(true);
    
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

      // Handle non-OK HTTP responses (project not found, no files, validation errors)
      if (!response.ok) {
        let errorMsg = "Something went wrong. Please try again.";
        try {
          const errData = await response.json();
          // Use the user-facing message from ResponseEnums if available
          errorMsg = errData.message || errData.dev_detail || errData.detail || errorMsg;
        } catch {
          // Response wasn't JSON, use status text
          errorMsg = `Server error (${response.status}): ${response.statusText}`;
        }
        setIsTyping(false);
        setMessages(prev => [...prev, { role: "error", text: `**Error:** ${errorMsg}` }]);
        scrollToBottom();
        return;
      }

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
                  const lastMsg = newArr[newArr.length - 1];
                  
                  if (lastMsg.role === "user") {
                    // Inject newly spawned System bubble natively with first chunk
                    newArr.push({ role: "system", text: data.text || "" });
                  } else {
                    const lastIndex = newArr.length - 1;
                    newArr[lastIndex] = {
                      ...newArr[lastIndex],
                      text: newArr[lastIndex].text + (data.text || "")
                    };
                  }
                  return newArr;
                });
                scrollToBottom();
              } else if (data.type === "sources") {
                // Attach sources to the last assistant message
                setMessages(prev => {
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  if (updated[lastIdx]?.role === "system") {
                    updated[lastIdx] = { ...updated[lastIdx], sources: data.sources };
                  }
                  return updated;
                });
              } else if (data.type === "error") {
                // Render custom Error Exception signal safely in a dedicated error bubble
                setIsTyping(false);
                setMessages(prev => [...prev, { role: "error", text: `**Vector Search Exception:** ${data.text}` }]);
                scrollToBottom();
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


  const handleSend = () => {
    handleSendMessage(inputTitle);
  };

  const handleRegenerate = async () => {
    if (isTyping) return;
    try {
      const lastUserMsg = [...messages].reverse().find(m => m.role === "user");
      if (!lastUserMsg) return;

      const res = await deleteLastInteraction(activeProjectId);
      if (res.status !== 200) {
        triggerToast("Failed to clean previous history for regeneration.");
        return;
      }
      
      setMessages(prev => {
        const copy = [...prev];
        while (copy.length > 0) {
          const popped = copy.pop();
          if (popped?.role === 'user') break;
        }
        return copy;
      });
      
      await handleSendMessage(lastUserMsg.text);
    } catch(err) {
      triggerToast("Error attempting to regenerate response.");
    }
  };

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
              {/* Avatar */}
              {msg.role === "user" ? (
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 border mt-1 shadow-lg ring-1 ring-white/10 transition-all overflow-hidden"
                  style={!userProfile?.avatar_base64 ? { backgroundColor: avatarColor } : undefined}
                >
                  {userProfile?.avatar_base64 ? (
                    <img src={userProfile.avatar_base64} alt="User" className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-sm font-bold text-white/90 select-none">
                      {getInitials(displayName)}
                    </span>
                  )}
                </div>
              ) : (
                <div className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 border mt-1 shadow-lg ${msg.role === "error" ? "bg-red-500/10 border-red-500/30" : "bg-indigo-500/10 border-indigo-500/30 p-[2px]"} overflow-hidden`}>
                  {msg.role === "error" ? (
                    <Bot size={24} className="text-red-400" />
                  ) : (
                    <img src="/nimo-avatar.png" alt="Nimo" className="w-full h-full object-cover rounded-full" />
                  )}
                </div>
              )}
              
              <div className={`flex flex-col max-w-[85%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                {/* Display name label */}
                {msg.role === "user" && displayName && (
                  <span className="text-[10px] text-white/30 mb-1 mr-1 font-medium">{displayName}</span>
                )}
                {msg.role === "system" && i > 0 && (
                  <span className="text-[10px] text-indigo-400/40 mb-1 ml-1 font-medium">Nimo</span>
                )}

                <div className={`
                  p-5 rounded-3xl glass shadow-xl relative group
                  ${msg.role === "user" ? "bg-emerald-900/40 border-emerald-500/30 text-emerald-50 rounded-tr-[4px]" : 
                    msg.role === "error" ? "bg-red-900/40 border-red-500/50 text-red-100 rounded-tl-[4px]" : 
                    "bg-indigo-900/20 border-indigo-500/30 text-indigo-50 rounded-tl-[4px] w-full"}
                `}>
                  {/* Action Bar */}
                  <MessageActions 
                    content={msg.text} 
                    role={msg.role} 
                    onRegenerate={handleRegenerate} 
                    isLast={i === messages.length - 1} 
                  />

                  <div className={`prose prose-invert max-w-none text-[15px] font-light leading-relaxed prose-p:leading-relaxed prose-pre:bg-transparent prose-pre:border-0 prose-pre:p-0 prose-pre:shadow-none prose-code:text-indigo-300`}>
                     <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          code(props) {
                            const {children, className, node, ref, ...rest} = props
                            const match = /language-(\w+)/.exec(className || '')
                            if (!match) {
                              return <code ref={ref} className="bg-white/10 px-1.5 py-0.5 rounded text-[13px] font-mono text-indigo-200" {...rest}>{children}</code>
                            }
                            return (
                              <div className="relative group/code mt-4 mb-4 rounded-xl overflow-hidden border border-white/10 shadow-2xl">
                                <div className="absolute top-0 right-0 w-full flex justify-end bg-black/40 px-3 py-1.5 items-center gap-3 border-b border-white/5 z-10">
                                  <span className="text-[10px] text-white/40 font-mono lowercase mr-auto px-1 tracking-wider">{match[1]}</span>
                                  <CopyButton text={String(children).replace(/\n$/, '')} />
                                </div>
                                {/* @ts-ignore: React 19 types mismatch with react-syntax-highlighter */}
                                <SyntaxHighlighter
                                  {...(rest as any)}
                                  PreTag="div"
                                  children={String(children).replace(/\n$/, '')}
                                  language={match[1]}
                                  style={oneDark}
                                  customStyle={{ margin: 0, paddingTop: '38px', paddingBottom: '16px', paddingLeft: '16px', paddingRight: '16px', backgroundColor: '#0d1117' }}
                                  wrapLongLines={true}
                                />
                              </div>
                            )
                          }
                        }}
                     >
                        {msg.text}
                     </ReactMarkdown>
                  </div>
                  {/* Source Citations — rendered below the markdown, inside the assistant bubble */}
                  {msg.role === "system" && msg.sources && msg.sources.length > 0 && (
                    <SourceCitations sources={msg.sources} />
                  )}
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
                <div className="w-12 h-12 rounded-full flex items-center justify-center shrink-0 border mt-1 bg-indigo-500/10 border-indigo-500/30 p-[2px] overflow-hidden">
                  <img src="/nimo-avatar.png" alt="Nimo typing..." className="w-full h-full object-cover rounded-full" />
                </div>
                <div className="p-4 rounded-3xl rounded-tl-[4px] glass bg-indigo-900/20 border-indigo-500/20 flex items-center gap-2 px-5 shadow-lg">
                   <motion.div animate={{ scale: [1, 1.4, 1], opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1 }} className="w-[6px] h-[6px] rounded-full bg-indigo-400" />
                   <motion.div animate={{ scale: [1, 1.4, 1], opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1, delay: 0.2 }} className="w-[6px] h-[6px] rounded-full bg-indigo-400" />
                   <motion.div animate={{ scale: [1, 1.4, 1], opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1, delay: 0.4 }} className="w-[6px] h-[6px] rounded-full bg-indigo-400" />
                 </div>
              </motion.div>
           )}

          {!isTyping && messages.length === 0 && (
            <motion.div 
              key="empty-state"
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex-1 flex flex-col items-center justify-center gap-5 mt-24 opacity-80"
            >
              <div className="w-24 h-24 rounded-full bg-indigo-500/10 flex items-center justify-center shadow-[0_0_40px_rgba(79,70,229,0.15)] ring-1 ring-white/10 overflow-hidden p-[2px]">
                <img src="/nimo-avatar.png" alt="Nimo Avatar" className="w-full h-full rounded-full object-cover shadow-inner" />
              </div>
              <div className="text-center space-y-2">
                <h3 className="text-xl font-medium text-white/80 tracking-wide">Start a Conversation</h3>
                <p className="text-[14px] text-white/40 max-w-xs text-center leading-relaxed">
                  Search the vector database or ask Nimo a question.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="p-6 max-w-4xl mx-auto w-full relative z-20">
        <div className="glass bg-[#1a1d24]/90 rounded-3xl p-3 pl-5 flex items-end gap-3 border border-white/10 shadow-[0_-5px_40px_rgba(0,0,0,0.3)] focus-within:border-indigo-500/50 focus-within:shadow-[0_0_30px_rgba(79,70,229,0.2)] transition-all">
          <Sparkles size={20} className="text-indigo-500 shrink-0 mb-3" />
          <textarea
            value={inputTitle}
            onChange={(e) => setInputTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Search your active knowledge base..."
            className="flex-1 bg-transparent border-none outline-none text-white/90 text-[15px] font-light placeholder:text-white/30 resize-none min-h-[44px] max-h-40 overflow-y-auto pt-2 disabled:opacity-50 custom-scrollbar"
            rows={inputTitle.split('\n').length > 5 ? 5 : inputTitle.split('\n').length || 1}
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
