"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Bot, CheckCircle2, AlertCircle, Database, BrainCircuit, PenTool } from "lucide-react";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const [plan, setPlan] = useState<any>(null);
  
  const endOfLogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfLogRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isProcessing) return;

    setIsProcessing(true);
    setEvents([]);
    setPlan(null);

    try {
      const response = await fetch("http://localhost:8000/api/orchestrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) throw new Error("Failed to start orchestration");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");
      
      if (!reader) return;

      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split(/\r?\n\r?\n/);
        buffer = parts.pop() || ""; // Keep the last incomplete part in the buffer
        
        for (const part of parts) {
          const lines = part.split(/\r?\n/);
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                setEvents((prev) => [...prev, data]);
                
                if (data.type === "plan") {
                  setPlan(data.data);
                }
                
                if (data.type === "done" || data.type === "error") {
                  setIsProcessing(false);
                }
              } catch (err) {
                console.error("Failed to parse SSE JSON", err);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error(error);
      setIsProcessing(false);
    }
  };

  const getAgentIcon = (agentName: string) => {
    switch (agentName) {
      case "Retriever": return <Database className="w-4 h-4 text-blue-400" />;
      case "Analyzer": return <BrainCircuit className="w-4 h-4 text-purple-400" />;
      case "Writer": return <PenTool className="w-4 h-4 text-emerald-400" />;
      default: return <Bot className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100 p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        <header className="space-y-2">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Agentic AI System
          </h1>
          <p className="text-neutral-400 text-sm">Multi-agent task decomposition and orchestration</p>
        </header>

        <form onSubmit={handleSubmit} className="relative">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isProcessing}
            placeholder="E.g., Research quantum computing, analyze its impact on crypto, and write a summary."
            className="w-full bg-neutral-900 border border-neutral-800 rounded-xl px-6 py-4 pr-16 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all text-sm disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!prompt.trim() || isProcessing}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 bg-neutral-800 hover:bg-neutral-700 rounded-lg transition-colors disabled:opacity-50"
          >
            {isProcessing ? <Loader2 className="w-5 h-5 animate-spin text-purple-400" /> : <Send className="w-5 h-5 text-purple-400" />}
          </button>
        </form>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Plan Visualization */}
          <section className="bg-neutral-900/50 border border-neutral-800/50 rounded-xl p-6 h-[600px] overflow-y-auto">
            <h2 className="text-sm font-semibold text-neutral-300 uppercase tracking-wider mb-6 flex items-center gap-2">
              <Bot className="w-4 h-4" /> Execution Plan (DAG)
            </h2>
            
            {!plan ? (
              <div className="flex items-center justify-center h-full text-neutral-600 text-sm">
                Waiting for task decomposition...
              </div>
            ) : (
              <div className="space-y-4 relative">
                {plan.tasks.map((task: any, index: number) => {
                  const isComplete = events.some(e => e.type === "task_complete" && e.task_id === task.id);
                  const isRunning = events.some(e => e.type === "task_start" && e.task_id === task.id) && !isComplete;
                  const isFailed = events.some(e => e.type === "error" && e.message.includes(task.id));

                  let borderColor = "border-neutral-800";
                  let bgColor = "bg-neutral-900";
                  
                  if (isComplete) {
                    borderColor = "border-emerald-500/30";
                    bgColor = "bg-emerald-500/10";
                  } else if (isRunning) {
                    borderColor = "border-blue-500/50";
                    bgColor = "bg-blue-500/10";
                  } else if (isFailed) {
                    borderColor = "border-red-500/50";
                    bgColor = "bg-red-500/10";
                  }

                  return (
                    <div key={task.id} className={`relative p-4 rounded-lg border ${borderColor} ${bgColor} transition-colors duration-500`}>
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-xs font-mono text-neutral-500">{task.id}</span>
                        <div className="flex items-center gap-2 bg-neutral-950 px-2 py-1 rounded-md border border-neutral-800">
                          {getAgentIcon(task.assigned_agent)}
                          <span className="text-xs font-medium text-neutral-300">{task.assigned_agent}</span>
                        </div>
                      </div>
                      <p className="text-sm text-neutral-200">{task.description}</p>
                      
                      {task.dependencies.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-neutral-800/50 flex gap-2 text-xs text-neutral-500">
                          <span className="font-semibold">Depends on:</span>
                          {task.dependencies.map((d: string) => (
                            <span key={d} className="bg-neutral-800 px-1.5 rounded text-neutral-300">{d}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          {/* Event Log */}
          <section className="bg-neutral-900/50 border border-neutral-800/50 rounded-xl p-6 h-[600px] flex flex-col">
            <h2 className="text-sm font-semibold text-neutral-300 uppercase tracking-wider mb-6 flex items-center gap-2">
              <Activity className="w-4 h-4" /> System Stream
            </h2>
            
            <div className="flex-1 overflow-y-auto space-y-4 pr-2 font-mono text-xs">
              {events.length === 0 ? (
                <div className="flex items-center justify-center h-full text-neutral-600 font-sans text-sm">
                  System idle.
                </div>
              ) : (
                events.map((event, idx) => (
                  <div key={idx} className="pb-3 border-b border-neutral-800/30 last:border-0">
                    <span className="text-neutral-500 mr-2">[{new Date().toLocaleTimeString()}]</span>
                    
                    {event.type === "status" && (
                      <span className="text-blue-400">{event.message}</span>
                    )}
                    
                    {event.type === "error" && (
                      <span className="text-red-400 flex items-center gap-1 mt-1">
                        <AlertCircle className="w-3 h-3" /> {event.message}
                      </span>
                    )}
                    
                    {event.type === "task_start" && (
                      <span className="text-neutral-300">
                        Agent <span className="text-purple-400">{event.agent}</span> started task <span className="text-purple-400">{event.task_id}</span>
                      </span>
                    )}
                    
                    {event.type === "task_complete" && (
                      <div className="mt-1">
                        <span className="text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" /> Task {event.task_id} complete.
                        </span>
                        <div className="mt-2 p-2 bg-neutral-950/50 border border-neutral-800 rounded text-neutral-400 whitespace-pre-wrap max-h-40 overflow-y-auto">
                          {typeof event.result === 'string' ? event.result : JSON.stringify(event.result, null, 2)}
                        </div>
                      </div>
                    )}

                    {event.type === "done" && (
                      <span className="text-green-400 font-bold block mt-4 border-t border-green-500/20 pt-4">
                        Orchestration completed successfully!
                      </span>
                    )}
                  </div>
                ))
              )}
              <div ref={endOfLogRef} />
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

const Activity = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
  </svg>
);
