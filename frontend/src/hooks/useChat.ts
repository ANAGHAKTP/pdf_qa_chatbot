"use client";

import { useState, useCallback, useEffect } from "react";
import { request } from "@/lib/api";
import { useStreaming } from "@/hooks/useStreaming";
import { ChatMessage } from "@/types/workspace";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [queryInput, setQueryInput] = useState("");
  const [followupSuggestions, setFollowupSuggestions] = useState<string[]>([]);
  
  const {
    isStreaming,
    streamedText,
    streamedCitations,
    streamedConfidence,
    activeStage,
    streamedMetrics,
    streamError,
    setStreamError,
    startStream,
    abortActiveStream,
  } = useStreaming();

  const loadChatHistory = useCallback(async (sessionId: string) => {
    setMessages([]);
    setStreamError(null);
    setFollowupSuggestions([]);
    try {
      const history = await request(`/chat/sessions/${sessionId}`);
      setMessages(history.messages || []);
      
      // Seed initial suggestions if session has no messages
      if (!history.messages || history.messages.length === 0) {
        setFollowupSuggestions([
          "Summarize this document and isolate the primary objectives.",
          "Provide a timeline of all dates and deadlines mentioned in the documents.",
          "Review the contract liabilities, risks, and regulatory conditions.",
        ]);
      } else {
        generateSuggestionsAfterMessage(history.messages[history.messages.length - 1]?.content);
      }
    } catch (err) {
      console.error("Failed to load chat history", err);
    }
  }, []);

  const generateSuggestionsAfterMessage = (content?: string) => {
    if (!content) return;
    const lower = content.toLowerCase();
    if (lower.includes("summary") || lower.includes("summarize")) {
      setFollowupSuggestions([
        "What are the main risks identified?",
        "Are there any specific action items or tasks?",
        "Extract key dates and timeline milestones.",
      ]);
    } else if (lower.includes("risk") || lower.includes("liabilit")) {
      setFollowupSuggestions([
        "How can these risks be mitigated?",
        "What are the legal or compliance requirements?",
        "Summarize the key timelines involved.",
      ]);
    } else {
      setFollowupSuggestions([
        "Can you clarify the primary findings?",
        "Give me a bulleted summary of this answer.",
        "List all key organizations or people mentioned.",
      ]);
    }
  };

  const sendQuery = async (
    sessionId: string,
    docIds: number[],
    userApiKey?: string,
    alternateQuery?: string
  ) => {
    const query = alternateQuery || queryInput;
    if (!query.trim()) return;

    if (docIds.length === 0) {
      alert("Please select at least one document to chat with!");
      return;
    }

    setQueryInput("");
    setFollowupSuggestions([]);

    const userMessage: ChatMessage = {
      id: Math.random().toString(),
      role: "user",
      content: query,
      created_at: new Date().toISOString(),
    };
    
    // Append user message immediately
    setMessages((prev) => [...prev, userMessage]);

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const token = localStorage.getItem("access_token") || "";

    const headers: Record<string, string> = {
      "Authorization": `Bearer ${token}`,
    };
    if (userApiKey) {
      headers["x-nvidia-api-key"] = userApiKey;
    }

    const body = {
      session_id: sessionId,
      query: query,
      doc_ids: docIds,
    };

    await startStream(`${API_URL}/chat/query`, body, headers);
  };

  const regenerateLastResponse = async (
    sessionId: string,
    docIds: number[],
    userApiKey?: string
  ) => {
    // Find the last user message
    const userMsgs = messages.filter((m) => m.role === "user");
    if (userMsgs.length === 0) return;

    const lastUserQuery = userMsgs[userMsgs.length - 1].content;
    
    // Remove trailing assistant message if present
    setMessages((prev) => {
      const next = [...prev];
      if (next.length > 0 && next[next.length - 1].role === "assistant") {
        next.pop();
      }
      return next;
    });

    await sendQuery(sessionId, docIds, userApiKey, lastUserQuery);
  };

  const submitMessageFeedback = async (messageId: string, rating: number) => {
    try {
      await request("/chat/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message_id: messageId, rating }),
      });
    } catch (err) {
      console.error("Failed to submit feedback", err);
      throw err;
    }
  };

  // Sync completed stream to message history list
  useEffect(() => {
    if (!isStreaming && streamedText) {
      const assistantMessage: ChatMessage = {
        id: Math.random().toString(),
        role: "assistant",
        content: streamedText,
        citations: streamedCitations,
        metrics: streamedMetrics,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      generateSuggestionsAfterMessage(streamedText);
    }
  }, [isStreaming, streamedText, streamedCitations, streamedMetrics]);

  return {
    messages,
    queryInput,
    setQueryInput,
    followupSuggestions,
    isStreaming,
    streamedText,
    streamedCitations,
    streamedConfidence,
    activeStage,
    streamedMetrics,
    streamError,
    loadChatHistory,
    sendQuery,
    regenerateLastResponse,
    submitMessageFeedback,
    abortQuery: abortActiveStream,
  };
}
