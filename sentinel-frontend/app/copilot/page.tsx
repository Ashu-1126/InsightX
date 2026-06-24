"use client";
import { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";
import { intelligence } from "@/lib/api";
import type { RAGResponse, Pattern } from "@/lib/types";
import { MessageSquareText, Send, Brain, TrendingUp, BookOpen, Loader2 } from "lucide-react";

const SUGGESTED_QUERIES = [
  "Why is Zone C high risk right now?",
  "What should I do when methane exceeds threshold?",
  "Show me patterns from historical incidents",
  "What are the hot work safety requirements?",
  "How do confined space permits work?",
  "What actions should be taken for explosion risk?",
];

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: RAGResponse["sources"];
  timestamp: string;
}

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm SENTINEL AI Copilot — your industrial safety intelligence assistant.\n\nI have access to:\n• Live sensor readings and active risks\n• Safety regulations (OISD, DGMS, Factory Act)\n• Historical incident patterns\n• Active permit status\n\nAsk me anything about plant safety.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [activeTab, setActiveTab] = useState<"chat" | "patterns">("chat");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { intelligence.patterns().then(setPatterns).catch(() => {}); }, []);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function sendMessage(query = input) {
    if (!query.trim() || loading) return;
    const userMsg: Message = { role: "user", content: query, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await intelligence.query(query, true);
      const aiMsg: Message = {
        role: "assistant",
        content: res.answer,
        sources: res.sources,
        timestamp: res.timestamp,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: "I encountered an error fetching the response. Please check the backend connection.",
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
    }
  }

  const confidenceColor = (c: number) => c >= 0.85 ? "text-success" : c >= 0.7 ? "text-warning" : "text-muted";

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar />
      <TopBar title="AI Safety Copilot" subtitle="RAG-powered safety intelligence assistant" />
      <main className="ml-60 pt-14 h-screen flex">

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Tabs */}
          <div className="flex border-b border-border px-6 pt-4">
            {[
              { id: "chat" as const, label: "Chat", icon: MessageSquareText },
              { id: "patterns" as const, label: "Incident Patterns", icon: TrendingUp },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-all
                  ${activeTab === id ? "border-primary text-primary" : "border-transparent text-muted hover:text-text"}`}
              >
                <Icon className="w-4 h-4" />{label}
              </button>
            ))}
          </div>

          {activeTab === "chat" ? (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    {msg.role === "assistant" && (
                      <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center mr-3 flex-shrink-0 mt-0.5">
                        <Brain className="w-4 h-4 text-primary" />
                      </div>
                    )}
                    <div className={`max-w-2xl ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col gap-2`}>
                      <div
                        className={`rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap leading-relaxed
                          ${msg.role === "user"
                            ? "bg-primary/15 border border-primary/25 text-text rounded-tr-sm"
                            : "bg-surface2 border border-border text-text rounded-tl-sm"
                          }`}
                      >
                        {msg.content}
                      </div>

                      {/* Sources */}
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {msg.sources.map((src) => (
                            <span key={src.id} className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded border border-border bg-surface text-muted">
                              <BookOpen className="w-2.5 h-2.5" />
                              {src.title.slice(0, 30)}… ({Math.round(src.relevance_score * 100)}%)
                            </span>
                          ))}
                        </div>
                      )}

                      <p className="text-[10px] text-muted font-mono px-1">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center">
                      <Brain className="w-4 h-4 text-primary" />
                    </div>
                    <div className="bg-surface2 border border-border rounded-2xl rounded-tl-sm px-4 py-3">
                      <Loader2 className="w-4 h-4 text-primary animate-spin" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Suggestions */}
              <div className="px-6 pb-2">
                <div className="flex flex-wrap gap-2">
                  {SUGGESTED_QUERIES.slice(0, 3).map((q) => (
                    <button
                      key={q}
                      onClick={() => sendMessage(q)}
                      className="text-xs px-3 py-1.5 rounded-full border border-border bg-surface2 text-muted hover:text-text hover:border-primary/40 transition-all"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>

              {/* Input */}
              <div className="p-6 pt-3 border-t border-border">
                <form
                  onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
                  className="flex gap-3"
                >
                  <input
                    className="input flex-1"
                    placeholder="Ask about safety risks, permits, regulations…"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    disabled={loading}
                  />
                  <button
                    type="submit"
                    disabled={loading || !input.trim()}
                    className="px-4 py-2 rounded-lg bg-primary text-bg font-semibold text-sm hover:bg-primary/90 transition-all disabled:opacity-40"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </>
          ) : (
            /* Patterns tab */
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {patterns.map((p, i) => (
                  <div key={i} className="card space-y-2">
                    <div className="flex items-start gap-2">
                      <TrendingUp className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                      <p className="text-sm font-semibold text-text">{p.pattern}</p>
                    </div>
                    <p className="text-xs text-muted pl-6">{p.insight}</p>
                    <div className="flex items-center justify-between pl-6">
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface2 border border-border text-muted">
                        {p.category}
                      </span>
                      <span className={`text-[10px] font-mono ${confidenceColor(p.confidence)}`}>
                        {Math.round(p.confidence * 100)}% confidence
                      </span>
                    </div>
                    {p.source && (
                      <p className="text-[10px] text-muted/60 pl-6 font-mono">Source: {p.source}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right sidebar — suggested queries */}
        <div className="w-64 bg-surface border-l border-border p-4 space-y-4">
          <div>
            <p className="label mb-3">Suggested Questions</p>
            <div className="space-y-2">
              {SUGGESTED_QUERIES.map((q) => (
                <button
                  key={q}
                  onClick={() => { setActiveTab("chat"); sendMessage(q); }}
                  className="w-full text-left text-xs text-muted hover:text-text hover:bg-surface2 p-2.5 rounded-lg border border-transparent hover:border-border transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          <div className="border-t border-border pt-4">
            <p className="label mb-2">Knowledge Base</p>
            <div className="space-y-1 text-xs text-muted">
              <p>• OISD-116 Safety Standards</p>
              <p>• DGMS Regulations</p>
              <p>• Factory Act Guidelines</p>
              <p>• Incident Pattern Reports</p>
              <p>• Emergency Response Protocols</p>
              <p>• Near Miss Analysis</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
