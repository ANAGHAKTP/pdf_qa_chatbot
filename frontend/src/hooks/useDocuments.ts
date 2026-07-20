"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { request, clearTokens } from "@/lib/api";
import { Document, Folder, DocStatus } from "@/types/workspace";

export function useDocuments() {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [currentFolderId, setCurrentFolderId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"pinned" | "recent" | "alpha">("recent");
  const [selectedDocIds, setSelectedDocIds] = useState<number[]>([]);
  
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [isAnalyzingDocId, setIsAnalyzingDocId] = useState<number | null>(null);

  const fetchFolderContents = useCallback(async () => {
    try {
      const url = currentFolderId ? `/documents/contents?parent_id=${currentFolderId}` : "/documents/contents";
      const data = await request(url);
      setFolders(data.folders || []);
      setDocuments(data.documents || []);
    } catch (err) {
      console.error("Failed to load folder contents", err);
    }
  }, [currentFolderId]);

  useEffect(() => {
    fetchFolderContents();
  }, [fetchFolderContents]);

  const createFolder = async (name: string) => {
    if (!name.trim()) return;
    try {
      await request("/documents/folders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          parent_id: currentFolderId,
        }),
      });
      fetchFolderContents();
    } catch (err) {
      console.error("Failed to create folder", err);
      throw err;
    }
  };

  const uploadFiles = async (files: FileList | File[]) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const formData = new FormData();
      formData.append("file", file);
      if (currentFolderId) {
        formData.append("folder_id", currentFolderId.toString());
      }

      setUploadProgress((prev) => ({ ...prev, [file.name]: 10 }));

      // Simulate progress up to 90%
      const interval = setInterval(() => {
        setUploadProgress((prev) => {
          const curr = prev[file.name] || 10;
          if (curr >= 90) {
            clearInterval(interval);
            return prev;
          }
          return { ...prev, [file.name]: curr + 15 };
        });
      }, 250);

      try {
        await request("/documents/upload", {
          method: "POST",
          body: formData,
        });
        setUploadProgress((prev) => ({ ...prev, [file.name]: 100 }));
      } catch (err: any) {
        console.error(`Failed to upload ${file.name}:`, err);
        setUploadProgress((prev) => ({ ...prev, [file.name]: -1 })); // -1 means failed
      } finally {
        clearInterval(interval);
      }
    }

    setIsUploading(false);
    fetchFolderContents();
  };

  const renameDocument = async (docId: number, newName: string) => {
    if (!newName.trim()) return;
    try {
      await request(`/documents/${docId}/rename`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_filename: newName.trim() }),
      });
      fetchFolderContents();
    } catch (err) {
      console.error("Failed to rename document", err);
      throw err;
    }
  };

  const deleteDocument = async (docId: number) => {
    try {
      await request(`/documents/${docId}`, { method: "DELETE" });
      setSelectedDocIds((prev) => prev.filter((id) => id !== docId));
      fetchFolderContents();
    } catch (err) {
      console.error("Failed to delete document", err);
      throw err;
    }
  };

  const toggleDocSelection = useCallback((docId: number) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  }, []);

  const selectAllFiltered = useCallback((filteredDocs: Document[]) => {
    setSelectedDocIds((prev) => {
      const filteredIds = filteredDocs.map(d => d.id);
      const allSelected = filteredIds.every(id => prev.includes(id));
      if (allSelected) {
        // Deselect all filtered docs
        return prev.filter(id => !filteredIds.includes(id));
      } else {
        // Select all filtered docs
        const next = [...prev];
        filteredIds.forEach(id => {
          if (!next.includes(id)) next.push(id);
        });
        return next;
      }
    });
  }, []);

  // Filter and sort logic
  const filteredDocuments = useMemo(() => {
    return documents
      .filter((doc) => {
        const matchesSearch = doc.filename.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesStatus = statusFilter === "all" || doc.status === statusFilter;
        return matchesSearch && matchesStatus;
      })
      .sort((a, b) => {
        if (sortBy === "pinned") {
          const aSelected = selectedDocIds.includes(a.id) ? 1 : 0;
          const bSelected = selectedDocIds.includes(b.id) ? 1 : 0;
          if (aSelected !== bSelected) return bSelected - aSelected;
        }
        if (sortBy === "alpha") {
          return a.filename.localeCompare(b.filename);
        }
        // Default "recent" sort
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
  }, [documents, searchQuery, statusFilter, sortBy, selectedDocIds]);

  return {
    folders,
    documents,
    currentFolderId,
    setCurrentFolderId,
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
    sortBy,
    setSortBy,
    selectedDocIds,
    setSelectedDocIds,
    isUploading,
    uploadProgress,
    isAnalyzingDocId,
    setIsAnalyzingDocId,
    createFolder,
    uploadFiles,
    renameDocument,
    deleteDocument,
    toggleDocSelection,
    selectAllFiltered,
    filteredDocuments,
    refreshDocuments: fetchFolderContents,
  };
}
