"use client";

import React, { useRef, useEffect } from "react";
import { Send, StopCircle, Loader2 } from "lucide-react";

interface ChatInputProps {
  value: string;
  onChange: (val: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isStreaming: boolean;
  onStop: () => void;
  disabled: boolean;
}

export function ChatInput({ value, onChange, onSubmit, isStreaming, onStop, disabled }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea to fit text height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled && !isStreaming) {
        onSubmit(e);
      }
    }
  };

  return (
    <form onSubmit={onSubmit} className="relative">
      <div className="rounded-xl border border-slate-800 bg-[#0E1122]/60 backdrop-blur-md overflow-hidden transition-all focus-within:border-indigo-500/80 focus-within:ring-1 focus-within:ring-indigo-500/10">
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? "Select a conversation to begin Q&A..." : "Ask a question about selected documents..."}
          disabled={disabled}
          className="w-full bg-transparent pl-4 pr-16 py-3.5 text-xs text-white placeholder-slate-500 resize-none outline-none max-h-[160px] min-h-[44px]"
        />

        <div className="absolute right-3.5 bottom-2.5 flex items-center gap-1.5">
          {isStreaming ? (
            <button
              type="button"
              onClick={onStop}
              className="h-7 px-2.5 rounded-lg bg-rose-600/15 border border-rose-500/20 hover:bg-rose-600/25 text-rose-400 hover:text-rose-300 text-[9px] uppercase tracking-wider font-bold transition-all flex items-center gap-1 active:translate-y-[1px]"
              title="Stop answer generation"
            >
              <StopCircle className="h-3.5 w-3.5" /> Stop
            </button>
          ) : (
            <button
              type="submit"
              disabled={disabled || !value.trim()}
              className="h-7 w-7 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800/40 text-white disabled:text-slate-500 transition-all flex items-center justify-center active:translate-y-[1px]"
            >
              <Send className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>
    </form>
  );
}
