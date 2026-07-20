"use client";

import React from "react";
import { Search } from "lucide-react";

interface ConversationSearchProps {
  value: string;
  onChange: (val: string) => void;
}

export function ConversationSearch({ value, onChange }: ConversationSearchProps) {
  return (
    <div className="relative p-3 border-b border-slate-800 bg-black/10">
      <input
        type="text"
        placeholder="Search conversation history..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg pl-8 pr-3 py-1.5 text-xs text-white glass-input"
      />
      <Search className="absolute left-5 top-5 h-3.5 w-3.5 text-slate-500" />
    </div>
  );
}
export default ConversationSearch;
