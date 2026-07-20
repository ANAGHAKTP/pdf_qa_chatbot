"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { request } from "@/lib/api";
import { ChatSession } from "@/types/workspace";

export function useConversations(user: any) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [pinnedSessionIds, setPinnedSessionIds] = useState<string[]>([]);

  // Load pins from localStorage on client side
  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("pinned_chat_sessions");
      if (stored) {
        try {
          setPinnedSessionIds(JSON.parse(stored));
        } catch (e) {
          console.error("Failed to parse pinned sessions", e);
        }
      }
    }
  }, []);

  const fetchSessions = useCallback(async () => {
    if (!user) return;
    try {
      const data = await request("/chat/sessions");
      setSessions(data || []);
    } catch (err) {
      console.error("Failed to load chat sessions", err);
    }
  }, [user]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const createChatSession = async (title: string): Promise<ChatSession> => {
    try {
      const session = await request("/chat/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      await fetchSessions();
      setCurrentSessionId(session.id);
      return session;
    } catch (err) {
      console.error("Failed to create chat session", err);
      throw err;
    }
  };

  const renameChatSession = async (sessionId: string, newTitle: string) => {
    try {
      await request(`/chat/sessions/${sessionId}/rename`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_title: newTitle }),
      });
      await fetchSessions();
    } catch (err) {
      console.error("Failed to rename chat session", err);
      throw err;
    }
  };

  const deleteChatSession = async (sessionId: string) => {
    try {
      await request(`/chat/sessions/${sessionId}`, { method: "DELETE" });
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
      }
      setPinnedSessionIds((prev) => {
        const next = prev.filter((id) => id !== sessionId);
        localStorage.setItem("pinned_chat_sessions", JSON.stringify(next));
        return next;
      });
      await fetchSessions();
    } catch (err) {
      console.error("Failed to delete chat session", err);
      throw err;
    }
  };

  const togglePinSession = useCallback((sessionId: string) => {
    setPinnedSessionIds((prev) => {
      const next = prev.includes(sessionId)
        ? prev.filter((id) => id !== sessionId)
        : [...prev, sessionId];
      localStorage.setItem("pinned_chat_sessions", JSON.stringify(next));
      return next;
    });
  }, []);

  // Filter and sort
  const sortedSessions = useMemo(() => {
    return sessions
      .filter((sess) => sess.title.toLowerCase().includes(searchQuery.toLowerCase()))
      .sort((a, b) => {
        const aPinned = pinnedSessionIds.includes(a.id) ? 1 : 0;
        const bPinned = pinnedSessionIds.includes(b.id) ? 1 : 0;

        // Pinned first
        if (aPinned !== bPinned) return bPinned - aPinned;

        // Sort by update time
        const aTime = new Date(a.updated_at || a.created_at).getTime();
        const bTime = new Date(b.updated_at || b.created_at).getTime();
        if (aTime !== bTime) return bTime - aTime;

        // Sort alphabetical
        return a.title.localeCompare(b.title);
      });
  }, [sessions, searchQuery, pinnedSessionIds]);

  return {
    sessions: sortedSessions,
    currentSessionId,
    setCurrentSessionId,
    searchQuery,
    setSearchQuery,
    pinnedSessionIds,
    createChatSession,
    renameChatSession,
    deleteChatSession,
    togglePinSession,
    refreshSessions: fetchSessions,
  };
}
