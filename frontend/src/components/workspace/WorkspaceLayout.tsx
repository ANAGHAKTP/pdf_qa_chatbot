"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/lib/AuthContext";
import { useDocuments } from "@/hooks/useDocuments";
import { useConversations } from "@/hooks/useConversations";
import { useChat } from "@/hooks/useChat";
import { request } from "@/lib/api";

// Sub-components
import { ConversationSidebar } from "@/components/sidebar/ConversationSidebar";
import { UploadDropzone } from "@/components/documents/UploadDropzone";
import { DocumentFilters } from "@/components/documents/DocumentFilters";
import { DocumentList } from "@/components/documents/DocumentList";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { PdfPreviewPanel } from "@/components/documents/PdfPreviewPanel";
import { Document, Citation } from "@/types/workspace";

export function WorkspaceLayout() {
  const { user, logout } = useAuth();
  
  // Custom Hooks
  const {
    folders,
    documents,
    currentFolderId,
    setCurrentFolderId,
    searchQuery: docSearchQuery,
    setSearchQuery: setDocSearchQuery,
    statusFilter,
    setStatusFilter,
    sortBy: docSortBy,
    setSortBy: setDocSortBy,
    selectedDocIds,
    setSelectedDocIds,
    isUploading,
    uploadProgress,
    createFolder,
    uploadFiles,
    renameDocument,
    deleteDocument,
    toggleDocSelection,
    selectAllFiltered,
    filteredDocuments,
  } = useDocuments();

  const {
    sessions,
    currentSessionId,
    setCurrentSessionId,
    searchQuery: sessionSearchQuery,
    setSearchQuery: setSessionSearchQuery,
    pinnedSessionIds,
    createChatSession,
    renameChatSession,
    deleteChatSession,
    togglePinSession,
  } = useConversations(user);

  const {
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
    abortQuery,
  } = useChat();

  // Workspace specific API overrides
  const [userApiKey, setUserApiKey] = useState("");

  // PDF Preview Panel states
  const [previewDoc, setPreviewDoc] = useState<Document | null>(null);
  const [previewTargetPage, setPreviewTargetPage] = useState(1);
  const [previewCitation, setPreviewCitation] = useState<Citation | null>(null);

  const handleOpenPdfPreview = useCallback(
    (docId: number, page: number, citation?: Citation) => {
      const doc = documents.find((d) => d.id === docId);
      if (doc) {
        setPreviewDoc(doc);
        setPreviewTargetPage(page);
        setPreviewCitation(citation || null);
      } else {
        alert(`Document #${docId} page ${page}`);
      }
    },
    [documents]
  );

  // KPI Analytics statistics states
  const [kpiStats, setKpiStats] = useState<any>(null);
  const [isLoadingKpi, setIsLoadingKpi] = useState(false);

  // Sync active session history updates
  useEffect(() => {
    if (currentSessionId) {
      loadChatHistory(currentSessionId);
    }
  }, [currentSessionId, loadChatHistory]);

  // Query KPI metrics dynamically
  const fetchKpis = useCallback(async () => {
    if (!user) return;
    setIsLoadingKpi(true);
    try {
      if (user.role === "ADMIN" || user.is_admin) {
        const stats = await request("/admin/stats");
        setKpiStats(stats);
      } else {
        const totalDocs = documents.length;
        const totalChats = sessions.length;
        const totalStorage = documents.reduce((acc, doc) => acc + doc.file_size, 0) / 1024 / 1024;
        
        let avgLat = 0;
        let avgTokens = 0;
        let count = 0;
        messages.forEach(m => {
          if (m.metrics) {
            avgLat += m.metrics.llm_time_ms + m.metrics.retrieval_time_ms;
            avgTokens += m.metrics.token_count || 0;
            count++;
          }
        });
        if (count > 0) {
          avgLat = avgLat / count;
          avgTokens = avgTokens / count;
        }

        setKpiStats({
          users_count: 1,
          documents_count: totalDocs,
          chats_count: totalChats,
          total_storage_mb: parseFloat(totalStorage.toFixed(2)),
          average_latency_ms: avgLat > 0 ? parseFloat((avgLat / 1000).toFixed(2)) : 0.82,
          average_tokens_per_message: avgTokens > 0 ? parseFloat(avgTokens.toFixed(0)) : 1420
        });
      }
    } catch (err) {
      console.error("Failed to load KPIs", err);
    } finally {
      setIsLoadingKpi(false);
    }
  }, [user, documents, sessions, messages]);

  // Run statistics update
  useEffect(() => {
    if (user) {
      fetchKpis();
    }
  }, [user, documents.length, sessions.length, messages.length, fetchKpis]);

  const handleQuerySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (currentSessionId) {
      sendQuery(currentSessionId, selectedDocIds, userApiKey);
    }
  };

  const handleRegenerate = () => {
    if (currentSessionId) {
      regenerateLastResponse(currentSessionId, selectedDocIds, userApiKey);
    }
  };

  const isAllFilteredSelected = filteredDocuments.length > 0 && 
    filteredDocuments.every(d => selectedDocIds.includes(d.id));

  return (
    <div className="flex h-screen bg-[#0B0D19] text-slate-100 overflow-hidden font-sans">
      {/* 1. Left Sidebar Panels */}
      <ConversationSidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        setCurrentSessionId={setCurrentSessionId}
        searchQuery={sessionSearchQuery}
        setSearchQuery={setSessionSearchQuery}
        pinnedSessionIds={pinnedSessionIds}
        createChatSession={createChatSession}
        renameChatSession={renameChatSession}
        deleteChatSession={deleteChatSession}
        togglePinSession={togglePinSession}
        userApiKey={userApiKey}
        setUserApiKey={setUserApiKey}
        onLogout={logout}
        userEmail={user?.email || ""}
        userFullName={user?.full_name || ""}
      />

      {/* 2. Middle Panels: Document Library Workspace */}
      <section className="w-[420px] shrink-0 border-r border-slate-800 bg-[#0E1122]/20 flex flex-col h-full z-10 p-4 space-y-4">
        <div>
          <h2 className="text-md font-bold text-white tracking-tight">Document Library</h2>
          <p className="text-[10px] text-slate-500">Upload and configure document context folders.</p>
        </div>

        {/* Drag and Drop Zone */}
        <UploadDropzone
          onUpload={uploadFiles}
          isUploading={isUploading}
          uploadProgress={uploadProgress}
        />

        {/* Filters and sorting */}
        <DocumentFilters
          searchQuery={docSearchQuery}
          setSearchQuery={setDocSearchQuery}
          statusFilter={statusFilter}
          setStatusFilter={setStatusFilter}
          sortBy={docSortBy}
          setSortBy={setDocSortBy}
          onSelectAllFiltered={() => selectAllFiltered(filteredDocuments)}
          isAllFilteredSelected={isAllFilteredSelected}
          filteredCount={filteredDocuments.length}
        />

        {/* Scroll list */}
        <DocumentList
          folders={folders}
          documents={documents}
          filteredDocuments={filteredDocuments}
          selectedDocIds={selectedDocIds}
          currentFolderId={currentFolderId}
          setCurrentFolderId={setCurrentFolderId}
          toggleDocSelection={toggleDocSelection}
          renameDocument={renameDocument}
          deleteDocument={deleteDocument}
          isUploading={isUploading}
        />
      </section>

      {/* 3. Right Panels: Chat Interface Area */}
      <ChatWindow
        sessionId={currentSessionId}
        selectedDocCount={selectedDocIds.length}
        kpiStats={kpiStats}
        isLoadingKpi={isLoadingKpi}
        messages={messages}
        queryInput={queryInput}
        setQueryInput={setQueryInput}
        onSubmitQuery={handleQuerySubmit}
        isStreaming={isStreaming}
        streamedText={streamedText}
        streamedCitations={streamedCitations}
        streamedConfidence={streamedConfidence}
        activeStage={activeStage}
        streamedMetrics={streamedMetrics}
        streamError={streamError}
        onStopStreaming={abortQuery}
        onRegenerateResponse={handleRegenerate}
        onFeedback={submitMessageFeedback}
        followupSuggestions={followupSuggestions}
        onSelectSuggestion={(sug) => sendQuery(currentSessionId!, selectedDocIds, userApiKey, sug)}
        onOpenPdfPreview={handleOpenPdfPreview}
      />

      {/* PDF Preview Modal Panel */}
      <PdfPreviewPanel
        isOpen={previewDoc !== null}
        onClose={() => setPreviewDoc(null)}
        document={previewDoc}
        targetPage={previewTargetPage}
        highlightCitation={previewCitation}
      />
    </div>
  );
}
export default WorkspaceLayout;
