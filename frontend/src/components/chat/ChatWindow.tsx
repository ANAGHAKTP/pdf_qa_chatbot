"use client";

import React, { useRef, useEffect } from "react";
import { MessageSquare, Activity, Sparkles, ChevronRight, Upload, Database, Clock, FileText, AlertTriangle, Loader2 } from "lucide-react";
import { ChatMessage as IChatMessage, Citation, ConfidenceReport } from "@/types/workspace";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { FollowupSuggestions } from "./FollowupSuggestions";

interface ChatWindowProps {
  sessionId: string | null;
  selectedDocCount: number;
  kpiStats: any;
  isLoadingKpi: boolean;
  messages: IChatMessage[];
  queryInput: string;
  setQueryInput: (val: string) => void;
  onSubmitQuery: (e: React.FormEvent) => void;
  isStreaming: boolean;
  streamedText: string;
  streamedCitations: Citation[];
  streamedConfidence?: ConfidenceReport | null;
  activeStage?: string | null;
  streamedMetrics: any;
  streamError: string | null;
  onStopStreaming: () => void;
  onRegenerateResponse: () => void;
  onFeedback: (msgId: string, rating: number) => Promise<void>;
  followupSuggestions: string[];
  onSelectSuggestion: (sug: string) => void;
  onOpenPdfPreview?: (docId: number, page: number, citation: Citation) => void;
}

export function ChatWindow({
  sessionId,
  selectedDocCount,
  kpiStats,
  isLoadingKpi,
  messages,
  queryInput,
  setQueryInput,
  onSubmitQuery,
  isStreaming,
  streamedText,
  streamedCitations,
  streamedConfidence,
  activeStage,
  streamedMetrics,
  streamError,
  onStopStreaming,
  onRegenerateResponse,
  onFeedback,
  followupSuggestions,
  onSelectSuggestion,
  onOpenPdfPreview,
}: ChatWindowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamedText, isStreaming, activeStage]);

  return (
    <main className="flex-1 flex flex-col h-full bg-[#080a10]/95 relative overflow-hidden">
      {/* Top Header */}
      <header className="px-6 py-4.5 border-b border-slate-800 flex items-center justify-between bg-black/25">
        <div className="overflow-hidden">
          <h1 className="text-xs font-bold text-white tracking-wider uppercase flex items-center gap-1.5">
            <MessageSquare className="h-4 w-4 text-indigo-400" />
            <span>QA Conversational Sandbox</span>
          </h1>
          <p className="text-[10px] text-slate-400 truncate mt-0.5">
            {selectedDocCount > 0
              ? `Workspace encompasses ${selectedDocCount} active files`
              : "Select documents in Hub to chat"}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isStreaming && activeStage && (
            <div className="flex items-center gap-1.5 rounded-full bg-indigo-950/60 border border-indigo-900/80 px-3 py-1 text-[10px] font-bold text-indigo-400 animate-pulse">
              <Loader2 className="h-3 w-3 animate-spin shrink-0" />
              <span>{activeStage}</span>
            </div>
          )}

          {selectedDocCount > 0 ? (
            <div className="flex items-center gap-1.5 rounded-full bg-emerald-950/40 border border-emerald-900/60 px-3.5 py-1 text-[10px] font-bold text-emerald-400">
              <Activity className="h-3 w-3 shrink-0 animate-pulse" />
              <span className="font-mono">RAG Active</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 rounded-full bg-amber-950/40 border border-amber-900/60 px-3.5 py-1 text-[10px] font-bold text-amber-400 animate-pulse">
              <AlertTriangle className="h-3 w-3 shrink-0" />
              <span className="font-mono">Context Empty</span>
            </div>
          )}
        </div>
      </header>

      {/* KPI Cards Panel */}
      <div className="px-6 pt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 shrink-0">
        <KpiCard
          title="Documents"
          value={kpiStats ? kpiStats.documents_count : 0}
          icon={<FileText className="h-4 w-4" />}
          loading={isLoadingKpi}
        />
        <KpiCard
          title="Conversations"
          value={kpiStats ? kpiStats.chats_count : 0}
          icon={<MessageSquare className="h-4 w-4" />}
          loading={isLoadingKpi}
        />
        <KpiCard
          title="Storage Footprint"
          value={kpiStats ? `${kpiStats.total_storage_mb} MB` : "0.0 MB"}
          icon={<Database className="h-4 w-4" />}
          loading={isLoadingKpi}
        />
        <KpiCard
          title="Average Latency"
          value={kpiStats ? `${kpiStats.average_latency_ms}s` : "0.82s"}
          icon={<Clock className="h-4 w-4" />}
          loading={isLoadingKpi}
        />
      </div>

      {/* Main Sandbox viewport */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4 space-y-5 scroll-smooth">
        {!sessionId ? (
          <div className="flex flex-col items-center justify-center h-full text-center max-w-lg mx-auto space-y-6">
            <div className="space-y-1">
              <Sparkles className="h-10 w-10 text-indigo-400 mx-auto animate-pulse" />
              <h3 className="text-base font-bold text-white tracking-tight">Welcome to DOCMind Enterprise</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Select a conversation or create a new session in the left sidebar to initialize document semantic retrieval vectors.
              </p>
            </div>

            <div className="flex items-center justify-between w-full max-w-md bg-[#0E1122]/30 border border-slate-800 p-4 rounded-xl text-[10px] font-semibold text-slate-400 relative">
              <div className="text-center space-y-1">
                <Upload className="h-4.5 w-4.5 text-indigo-400 mx-auto" />
                <p>1. Upload</p>
              </div>
              <ChevronRight className="h-4 w-4 text-slate-700 shrink-0" />
              <div className="text-center space-y-1">
                <Database className="h-4.5 w-4.5 text-indigo-400 mx-auto" />
                <p>2. Index</p>
              </div>
              <ChevronRight className="h-4 w-4 text-slate-700 shrink-0" />
              <div className="text-center space-y-1">
                <MessageSquare className="h-4.5 w-4.5 text-emerald-400 mx-auto" />
                <p>3. Query</p>
              </div>
              <ChevronRight className="h-4 w-4 text-slate-700 shrink-0" />
              <div className="text-center space-y-1">
                <Sparkles className="h-4.5 w-4.5 text-yellow-400 mx-auto" />
                <p>4. Extract</p>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Thread Messages */}
            {messages.map((msg, index) => {
              const isLastAssistantMsg =
                msg.role === "assistant" &&
                index === messages.length - 1 &&
                !isStreaming;

              return (
                <ChatMessage
                  key={msg.id || index}
                  msg={msg}
                  onFeedback={onFeedback}
                  isLastAssistantMessage={isLastAssistantMsg}
                  onRegenerate={onRegenerateResponse}
                  onOpenPreview={onOpenPdfPreview}
                />
              );
            })}

            {/* Active Streaming Token Node Bubble */}
            {isStreaming && (streamedText || streamedCitations.length > 0 || activeStage) && (
              <ChatMessage
                msg={{
                  id: "streaming-node",
                  role: "assistant",
                  content: streamedText || (activeStage ? `*${activeStage}*` : "..."),
                  citations: streamedCitations,
                  confidence_level: streamedConfidence?.level,
                  confidence_score: streamedConfidence?.score,
                  metrics: streamedMetrics,
                  created_at: new Date().toISOString(),
                }}
              />
            )}

            {/* Error alerts */}
            {streamError && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2 animate-fade-in">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{streamError}</span>
              </div>
            )}

            {/* Suggestions list */}
            {!isStreaming && (
              <FollowupSuggestions suggestions={followupSuggestions} onClick={onSelectSuggestion} />
            )}
          </>
        )}
      </div>

      {/* Input container */}
      <div className="p-6 border-t border-slate-800/80 bg-black/10 shrink-0">
        {selectedDocCount === 0 && sessionId && (
          <div className="mb-3 px-3 py-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[10px] text-amber-400 flex items-center gap-1.5">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>Select at least one document in the explorer list to perform vector search queries.</span>
          </div>
        )}
        <ChatInput
          value={queryInput}
          onChange={setQueryInput}
          onSubmit={onSubmitQuery}
          isStreaming={isStreaming}
          onStop={onStopStreaming}
          disabled={!sessionId || selectedDocCount === 0}
        />
      </div>
    </main>
  );
}

function KpiCard({ title, value, icon, description, loading }: any) {
  return (
    <div className="glass-card rounded-xl p-3.5 flex items-center justify-between border border-slate-800 transition-all duration-300 hover:border-indigo-500/30">
      <div className="space-y-0.5 flex-1 min-w-0">
        <p className="text-[9px] uppercase font-bold tracking-widest text-slate-500 truncate">{title}</p>
        {loading ? (
          <div className="h-5 w-16 bg-slate-800 rounded animate-pulse mt-1" />
        ) : (
          <h4 className="text-sm font-bold text-white tracking-tight truncate">{value}</h4>
        )}
      </div>
      <div className="h-8 w-8 shrink-0 rounded-lg bg-indigo-500/10 border border-indigo-500/25 flex items-center justify-center text-indigo-400 ml-2">
        {icon}
      </div>
    </div>
  );
}
export default ChatWindow;
