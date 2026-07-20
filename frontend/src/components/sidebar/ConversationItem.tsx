"use client";

import React, { useState } from "react";
import { MessageSquare, Trash2, Edit3, Pin, PinOff } from "lucide-react";
import { ChatSession } from "@/types/workspace";

interface ConversationItemProps {
  session: ChatSession;
  isActive: boolean;
  isPinned: boolean;
  onSelect: () => void;
  onRename: () => void;
  onDelete: () => void;
  onTogglePin: () => void;
}

export function ConversationItem({
  session,
  isActive,
  isPinned,
  onSelect,
  onRename,
  onDelete,
  onTogglePin,
}: ConversationItemProps) {
  const [showOptions, setShowOptions] = useState(false);

  return (
    <div
      onClick={onSelect}
      className={`group flex items-center justify-between rounded-xl px-3 py-2 text-xs cursor-pointer transition-all border ${
        isActive
          ? "bg-indigo-500/10 border-indigo-500/30 text-white font-semibold"
          : "hover:bg-slate-900/40 border-transparent text-slate-400 hover:text-white"
      }`}
    >
      <div className="flex items-center gap-2 overflow-hidden flex-1 min-w-0">
        <MessageSquare className="h-3.5 w-3.5 shrink-0 opacity-70" />
        <span className="truncate pr-1">{session.title}</span>
        {isPinned && <Pin className="h-2.5 w-2.5 text-indigo-400 shrink-0" />}
      </div>

      <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity shrink-0">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onTogglePin();
          }}
          className={`p-1 rounded hover:bg-slate-800 transition-colors ${isPinned ? "text-indigo-400" : "text-slate-500 hover:text-slate-300"}`}
          title={isPinned ? "Unpin session" : "Pin session"}
        >
          {isPinned ? <PinOff className="h-3 w-3" /> : <Pin className="h-3 w-3" />}
        </button>

        <button
          onClick={(e) => {
            e.stopPropagation();
            onRename();
          }}
          className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-white transition-colors"
          title="Rename conversation"
        >
          <Edit3 className="h-3 w-3" />
        </button>

        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-rose-400 transition-colors"
          title="Delete conversation"
        >
          <Trash2 className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}
export default ConversationItem;
