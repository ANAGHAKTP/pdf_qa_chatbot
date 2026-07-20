"use client";

import React from "react";
import { Sparkles } from "lucide-react";

interface FollowupSuggestionsProps {
  suggestions: string[];
  onClick: (suggestion: string) => void;
}

export function FollowupSuggestions({ suggestions, onClick }: FollowupSuggestionsProps) {
  if (suggestions.length === 0) return null;

  return (
    <div className="space-y-2 py-2">
      <p className="text-[9px] uppercase font-bold tracking-wider text-slate-500 flex items-center gap-1">
        <Sparkles className="h-3 w-3 text-indigo-400" /> Suggested Follow-up Questions
      </p>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((sug, idx) => (
          <button
            key={idx}
            onClick={() => onClick(sug)}
            className="px-3 py-1.5 rounded-lg bg-indigo-500/5 hover:bg-indigo-500/10 border border-indigo-500/15 text-[10px] text-indigo-300 hover:text-indigo-200 transition-all text-left active:translate-y-[1px] font-medium"
          >
            {sug}
          </button>
        ))}
      </div>
    </div>
  );
}
