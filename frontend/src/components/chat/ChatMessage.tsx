"use client";

import React, { useState, useMemo } from "react";
import { Copy, Check, ThumbsUp, ThumbsDown, Sparkles, ChevronRight } from "lucide-react";
import { ChatMessage as IChatMessage, Citation } from "@/types/workspace";
import { CitationCard } from "./CitationCard";

interface ChatMessageProps {
  msg: IChatMessage;
  onFeedback?: (msgId: string, rating: number) => Promise<void>;
  isLastAssistantMessage?: boolean;
  onRegenerate?: () => void;
  onOpenPreview?: (docId: number, page: number, citation: Citation) => void;
}

export function ChatMessage({ msg, onFeedback, isLastAssistantMessage, onRegenerate, onOpenPreview }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState<number | null>(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedback = async (rating: number) => {
    if (!onFeedback || feedbackGiven !== null) return;
    try {
      await onFeedback(msg.id, rating);
      setFeedbackGiven(rating);
    } catch (e) {
      console.error("Failed to record feedback", e);
    }
  };

  const formattedTime = new Date(msg.created_at).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className={`flex flex-col animate-fade-in ${msg.role === "user" ? "items-end" : "items-start"}`}>
      <div className="flex items-center justify-between w-full mb-1.5 px-2">
        <span className="text-[9px] uppercase font-bold tracking-wider text-slate-500 flex items-center gap-1.5">
          {msg.role === "user" ? "You" : "DOCMind"}
          <span className="text-[8px] font-mono lowercase tracking-normal">· {formattedTime}</span>
        </span>

        {msg.role === "assistant" && (msg.confidence_level || msg.metrics?.confidence_level) && (
          <div className="flex items-center gap-1">
            {(() => {
              const lvl = msg.confidence_level || msg.metrics?.confidence_level || "MEDIUM";
              const score = msg.confidence_score || msg.metrics?.confidence_score;
              const scoreStr = score ? ` (${(score * 100).toFixed(0)}%)` : "";

              if (lvl === "HIGH") {
                return (
                  <span className="inline-flex items-center gap-1 text-[8px] font-bold text-emerald-400 bg-emerald-950/40 border border-emerald-900/60 px-2 py-0.5 rounded-full uppercase">
                    ● High Confidence{scoreStr}
                  </span>
                );
              } else if (lvl === "MEDIUM") {
                return (
                  <span className="inline-flex items-center gap-1 text-[8px] font-bold text-amber-400 bg-amber-950/40 border border-amber-900/60 px-2 py-0.5 rounded-full uppercase">
                    ▲ Medium Confidence{scoreStr}
                  </span>
                );
              } else {
                return (
                  <span className="inline-flex items-center gap-1 text-[8px] font-bold text-rose-400 bg-rose-950/40 border border-rose-900/60 px-2 py-0.5 rounded-full uppercase">
                    ⚠️ Low Confidence{scoreStr}
                  </span>
                );
              }
            })()}
          </div>
        )}
      </div>

      <div
        className={`relative max-w-[85%] rounded-xl p-4 text-xs leading-relaxed border shadow-md ${
          msg.role === "user"
            ? "bg-indigo-600/10 border-indigo-500/20 text-white rounded-tr-sm"
            : "bg-[#0E1122]/40 border-slate-800/80 text-slate-200 rounded-tl-sm gradient-bar"
        }`}
      >
        {/* Markdown Render Body */}
        <MarkdownRenderer content={msg.content} />

        {/* Citations referenced */}
        {msg.citations && msg.citations.length > 0 && (
          <details className="mt-3.5 pt-3.5 border-t border-slate-800/60 space-y-2 group">
            <summary className="text-[9px] uppercase font-bold tracking-wider text-slate-400 hover:text-white cursor-pointer select-none outline-none list-none flex items-center justify-between">
              <span>Sources Referenced ({msg.citations.length})</span>
              <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90 text-indigo-400" />
            </summary>
            <div className="grid grid-cols-1 gap-2 pt-2.5">
              {msg.citations.map((c) => (
                <CitationCard key={c.citation_num} citation={c} onOpenPreview={onOpenPreview} />
              ))}
            </div>
          </details>
        )}

        {/* Assistant metadata metrics and feedback controls */}
        {msg.role === "assistant" && (
          <div className="mt-3.5 pt-3.5 border-t border-slate-800/60 flex flex-col gap-2">
            {msg.metrics && (
              <details className="group">
                <summary className="text-[9px] uppercase font-bold tracking-wider text-slate-400 hover:text-white cursor-pointer select-none outline-none list-none flex items-center justify-between">
                  <span>Query Latency Metrics</span>
                  <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90 text-slate-500" />
                </summary>
                <div className="grid grid-cols-3 gap-2 pt-2 font-mono text-[9px] text-slate-400">
                  <div className="p-2 rounded bg-slate-950/40 border border-slate-800">
                    <p className="font-sans text-[8px] uppercase font-bold text-slate-500">Retr. Speed</p>
                    <p className="text-white mt-0.5">{msg.metrics.retrieval_time_ms.toFixed(0)} ms</p>
                  </div>
                  <div className="p-2 rounded bg-slate-950/40 border border-slate-800">
                    <p className="font-sans text-[8px] uppercase font-bold text-slate-500">LLM Latency</p>
                    <p className="text-white mt-0.5">{msg.metrics.llm_time_ms.toFixed(0)} ms</p>
                  </div>
                  <div className="p-2 rounded bg-slate-950/40 border border-slate-800">
                    <p className="font-sans text-[8px] uppercase font-bold text-slate-500">Token Count</p>
                    <p className="text-white mt-0.5">{msg.metrics.token_count}</p>
                  </div>
                </div>
              </details>
            )}

            <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
              <span className="font-mono text-[8px] text-slate-500">MODEL: NIM Llama3-8B</span>
              
              <div className="flex items-center gap-2">
                {isLastAssistantMessage && onRegenerate && (
                  <button
                    onClick={onRegenerate}
                    className="px-2 py-0.5 rounded bg-slate-800 hover:bg-indigo-600/20 text-slate-300 hover:text-indigo-400 text-[8px] uppercase tracking-wider font-bold transition-all"
                  >
                    Regenerate
                  </button>
                )}
                
                <button
                  onClick={handleCopy}
                  className="p-1.5 rounded bg-slate-800 hover:bg-indigo-600/20 hover:text-white transition-colors"
                  title="Copy answer"
                >
                  {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                </button>
                
                {onFeedback && (
                  <>
                    <button
                      onClick={() => handleFeedback(1)}
                      disabled={feedbackGiven !== null}
                      className={`p-1.5 rounded bg-slate-800 transition-colors ${
                        feedbackGiven === 1
                          ? "bg-emerald-950/40 text-emerald-400 border border-emerald-900/50"
                          : "hover:bg-emerald-950/20 hover:text-emerald-400"
                      }`}
                      title="Thumbs Up"
                    >
                      <ThumbsUp className="h-3 w-3" />
                    </button>
                    <button
                      onClick={() => handleFeedback(-1)}
                      disabled={feedbackGiven !== null}
                      className={`p-1.5 rounded bg-slate-800 transition-colors ${
                        feedbackGiven === -1
                          ? "bg-rose-950/40 text-rose-400 border border-rose-900/50"
                          : "hover:bg-rose-950/20 hover:text-rose-400"
                      }`}
                      title="Thumbs Down"
                    >
                      <ThumbsDown className="h-3 w-3" />
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Custom Markdown renderer with code block "Copy Code" button and styling
function MarkdownRenderer({ content }: { content: string }) {
  const parts = useMemo(() => {
    if (!content) return [];
    return content.split(/(```[\s\S]*?```)/g);
  }, [content]);

  return (
    <div className="space-y-2.5">
      {parts.map((part, index) => {
        if (part.startsWith("```")) {
          const match = part.match(/```(\w*)\n([\s\S]*?)```/);
          const lang = match ? match[1] : "";
          const code = match ? match[2] : part.slice(3, -3);

          return <CodeBlock key={index} language={lang} code={code.trim()} />;
        }

        const lines = part.split("\n");
        let listItems: string[] = [];
        let tableRows: string[][] = [];
        let inList = false;
        let inTable = false;
        const elements: React.ReactNode[] = [];

        const flushList = (key: string | number) => {
          if (listItems.length > 0) {
            elements.push(
              <ul key={`ul-${key}`} className="list-disc pl-5 space-y-1 my-1.5">
                {listItems.map((item, idx) => (
                  <li key={idx} className="text-slate-300 text-xs">
                    {parseInlineStyles(item)}
                  </li>
                ))}
              </ul>
            );
            listItems = [];
          }
          inList = false;
        };

        const flushTable = (key: string | number) => {
          if (tableRows.length > 0) {
            const hasHeader =
              tableRows.length > 1 &&
              tableRows[1].every((cell) => cell.trim().startsWith("---") || cell.trim().startsWith(":-"));
            const dataRows = hasHeader ? tableRows.slice(2) : tableRows;
            const headerRow = hasHeader ? tableRows[0] : null;

            elements.push(
              <div key={`table-${key}`} className="overflow-x-auto my-2 rounded-lg border border-slate-800 bg-black/20">
                <table className="min-w-full divide-y divide-slate-800 text-left text-xs">
                  {headerRow && (
                    <thead className="bg-slate-900/40">
                      <tr>
                        {headerRow.map((cell, idx) => (
                          <th
                            key={idx}
                            className="px-3 py-1.5 font-semibold text-white uppercase tracking-wider text-[10px]"
                          >
                            {parseInlineStyles(cell.trim())}
                          </th>
                        ))}
                      </tr>
                    </thead>
                  )}
                  <tbody className="divide-y divide-slate-800">
                    {dataRows.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-slate-900/10 transition-colors">
                        {row.map((cell, cIdx) => (
                          <td key={cIdx} className="px-3 py-1.5 text-slate-300 text-xs">
                            {parseInlineStyles(cell.trim())}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
            tableRows = [];
          }
          inTable = false;
        };

        lines.forEach((line, lineIdx) => {
          const trimmed = line.trim();

          if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
            flushList(lineIdx);
            inTable = true;
            const cells = trimmed.split("|").slice(1, -1);
            tableRows.push(cells);
            return;
          } else if (inTable) {
            flushTable(lineIdx);
          }

          if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
            inList = true;
            listItems.push(trimmed.slice(2));
            return;
          } else if (inList) {
            flushList(lineIdx);
          }

          if (trimmed.startsWith("# ")) {
            elements.push(
              <h1 key={lineIdx} className="text-sm font-bold text-white mt-3 mb-1.5">
                {parseInlineStyles(trimmed.slice(2))}
              </h1>
            );
            return;
          }
          if (trimmed.startsWith("## ")) {
            elements.push(
              <h2 key={lineIdx} className="text-xs font-bold text-white mt-2 mb-1">
                {parseInlineStyles(trimmed.slice(3))}
              </h2>
            );
            return;
          }

          if (trimmed) {
            elements.push(
              <p key={lineIdx} className="leading-relaxed text-slate-300 text-xs mb-1">
                {parseInlineStyles(trimmed)}
              </p>
            );
          }
        });

        flushList("final");
        flushTable("final");

        return <div key={index} className="space-y-1">{elements}</div>;
      })}
    </div>
  );
}

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-2.5 rounded-lg overflow-hidden border border-slate-800 bg-slate-950/80 font-mono text-[11px] text-indigo-200">
      <div className="bg-slate-900 px-4 py-1.5 flex items-center justify-between text-[9px] uppercase font-bold text-slate-400 border-b border-slate-800/80">
        <span>{language || "code"}</span>
        <button
          onClick={handleCopyCode}
          className="flex items-center gap-1 hover:text-white transition-colors"
        >
          {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
          <span>{copied ? "Copied" : "Copy Code"}</span>
        </button>
      </div>
      <pre className="p-3.5 overflow-x-auto">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function parseInlineStyles(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={idx} className="font-bold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={idx}
          className="bg-slate-900/60 font-mono text-[10px] px-1 py-0.5 rounded text-indigo-300 border border-slate-800/40"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}
