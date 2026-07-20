"use client";

import React, { useState } from "react";
import { Plus, LogOut, Settings } from "lucide-react";
import { ChatSession } from "@/types/workspace";
import { ConversationItem } from "./ConversationItem";
import { ConversationSearch } from "./ConversationSearch";
import { ConversationDialogs } from "./ConversationDialogs";

interface ConversationSidebarProps {
  sessions: ChatSession[];
  currentSessionId: string | null;
  setCurrentSessionId: (id: string | null) => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  pinnedSessionIds: string[];
  createChatSession: (title: string) => Promise<ChatSession>;
  renameChatSession: (id: string, title: string) => Promise<void>;
  deleteChatSession: (id: string) => Promise<void>;
  togglePinSession: (id: string) => void;
  userApiKey: string;
  setUserApiKey: (key: string) => void;
  onLogout: () => void;
  userEmail: string;
  userFullName: string | null;
}

export function ConversationSidebar({
  sessions,
  currentSessionId,
  setCurrentSessionId,
  searchQuery,
  setSearchQuery,
  pinnedSessionIds,
  createChatSession,
  renameChatSession,
  deleteChatSession,
  togglePinSession,
  userApiKey,
  setUserApiKey,
  onLogout,
  userEmail,
  userFullName,
}: ConversationSidebarProps) {
  // Dialog visibility states
  const [createOpen, setCreateOpen] = useState(false);
  const [renameSession, setRenameSession] = useState<ChatSession | null>(null);

  const handleDeleteSession = async (sessId: string) => {
    if (confirm("Delete this conversation session and all its message history?")) {
      await deleteChatSession(sessId);
    }
  };

  return (
    <aside className="w-80 shrink-0 border-r border-slate-800 glass-panel flex flex-col h-full z-10">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-white tracking-tight">
            ◈ DOC<span className="text-indigo-400">Mind</span>
          </span>
          <span className="text-[9px] uppercase font-bold tracking-widest text-emerald-400 bg-emerald-950/40 border border-emerald-900/60 px-1.5 py-0.5 rounded-full">
            ENT
          </span>
        </div>
        <button
          onClick={onLogout}
          className="text-slate-400 hover:text-white transition-colors"
          title="Sign Out"
        >
          <LogOut className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* NVIDIA Override API Key Input */}
      <div className="p-3 border-b border-slate-800 bg-black/20">
        <label className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
          <Settings className="h-3 w-3" />
          <span>NVIDIA API Key Override</span>
        </label>
        <input
          type="password"
          placeholder="nvapi-..."
          value={userApiKey}
          onChange={(e) => setUserApiKey(e.target.value)}
          className="w-full rounded-md px-2.5 py-1.5 text-xs text-white glass-input font-mono"
        />
      </div>

      {/* Conversations Header */}
      <div className="px-4 py-3 flex items-center justify-between text-slate-500 text-[10px] font-bold uppercase tracking-wider shrink-0">
        <span>Conversations</span>
        <button
          onClick={() => setCreateOpen(true)}
          className="text-indigo-400 hover:text-white flex items-center gap-0.5 text-[10px] normal-case tracking-normal transition-colors"
        >
          <Plus className="h-3 w-3" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Search History */}
      <ConversationSearch value={searchQuery} onChange={setSearchQuery} />

      {/* Conversations Scroll List */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-1 pb-4">
        {sessions.map((sess) => (
          <ConversationItem
            key={sess.id}
            session={sess}
            isActive={currentSessionId === sess.id}
            isPinned={pinnedSessionIds.includes(sess.id)}
            onSelect={() => setCurrentSessionId(sess.id)}
            onRename={() => setRenameSession(sess)}
            onDelete={() => handleDeleteSession(sess.id)}
            onTogglePin={() => togglePinSession(sess.id)}
          />
        ))}

        {sessions.length === 0 && (
          <div className="px-2 py-8 text-center text-slate-500 space-y-3">
            <p className="text-[10px]">No conversation sessions found.</p>
            <button
              onClick={() => setCreateOpen(true)}
              className="px-3 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-900/40 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
            >
              Start New Chat
            </button>
          </div>
        )}
      </div>

      {/* User Footer Profile metadata info */}
      <div className="p-3 border-t border-slate-800 flex items-center gap-2.5 bg-black/10 shrink-0">
        <div className="h-7.5 w-7.5 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center font-bold text-indigo-400 text-xs">
          {userEmail ? userEmail[0].toUpperCase() : "U"}
        </div>
        <div className="overflow-hidden flex-1">
          <p className="text-xs font-semibold text-white truncate">{userFullName || "Enterprise User"}</p>
          <p className="text-[9px] text-slate-500 truncate">{userEmail}</p>
        </div>
      </div>

      {/* dialog modals */}
      <ConversationDialogs
        createOpen={createOpen}
        onCreateClose={() => setCreateOpen(false)}
        onCreateConfirm={async (title) => {
          await createChatSession(title);
        }}
        renameOpen={renameSession !== null}
        onRenameClose={() => setRenameSession(null)}
        currentRenameTitle={renameSession?.title || ""}
        onRenameConfirm={async (newTitle) => {
          await renameChatSession(renameSession!.id, newTitle);
        }}
      />
    </aside>
  );
}
export default ConversationSidebar;
