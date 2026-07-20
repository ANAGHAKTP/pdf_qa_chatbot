"use client";

import React, { useState } from "react";
import { Folder, FileText, Search, Loader } from "lucide-react";
import { Document, Folder as IFolder } from "@/types/workspace";
import { DocumentCard } from "./DocumentCard";
import { RenameDocumentDialog } from "./RenameDocumentDialog";
import { DeleteDocumentDialog } from "./DeleteDocumentDialog";

interface DocumentListProps {
  folders: IFolder[];
  documents: Document[];
  filteredDocuments: Document[];
  selectedDocIds: number[];
  currentFolderId: number | null;
  setCurrentFolderId: (id: number | null) => void;
  toggleDocSelection: (docId: number) => void;
  renameDocument: (docId: number, name: string) => Promise<void>;
  deleteDocument: (docId: number) => Promise<void>;
  isUploading: boolean;
}

export function DocumentList({
  folders,
  documents,
  filteredDocuments,
  selectedDocIds,
  currentFolderId,
  setCurrentFolderId,
  toggleDocSelection,
  renameDocument,
  deleteDocument,
  isUploading,
}: DocumentListProps) {
  // Modal states
  const [renameDoc, setRenameDoc] = useState<Document | null>(null);
  const [deleteDoc, setDeleteDoc] = useState<Document | null>(null);

  const isLibraryEmpty = folders.length === 0 && documents.length === 0;
  const isSearchEmpty = documents.length > 0 && filteredDocuments.length === 0;

  return (
    <div className="flex-1 overflow-y-auto space-y-3.5 pr-1">
      {/* Directory Navigation path */}
      <div className="px-4 py-2 border-b border-slate-800 bg-black/10 flex items-center justify-between gap-1 text-[11px] text-slate-400 rounded-lg">
        <div className="flex items-center gap-1 font-semibold">
          <span className="cursor-pointer hover:text-white transition-colors" onClick={() => setCurrentFolderId(null)}>Root</span>
          {currentFolderId && (
            <>
              <span className="text-slate-600">/</span>
              <span className="text-white">Subdirectory</span>
            </>
          )}
        </div>
        {isUploading && (
          <span className="text-sky-400 font-mono text-[9px] flex items-center gap-1.5 animate-pulse">
            <Loader className="h-3 w-3 animate-spin" /> Uploading files...
          </span>
        )}
      </div>

      {/* Folders List */}
      {folders.map((fold) => (
        <div
          key={fold.id}
          onClick={() => setCurrentFolderId(fold.id)}
          className="flex items-center gap-2.5 p-2.5 rounded-xl bg-[#0E1122]/30 border border-slate-800/60 hover:border-indigo-500/30 cursor-pointer transition-all hover:bg-slate-900/10"
        >
          <Folder className="h-4.5 w-4.5 text-indigo-400 shrink-0" />
          <div className="flex-1 overflow-hidden">
            <p className="text-xs font-semibold text-white truncate">{fold.name}</p>
            <p className="text-[9px] text-slate-500">Folder Directory</p>
          </div>
        </div>
      ))}

      {/* Documents Cards list */}
      <div className="space-y-3">
        {filteredDocuments.map((doc) => (
          <DocumentCard
            key={doc.id}
            doc={doc}
            isSelected={selectedDocIds.includes(doc.id)}
            onSelect={() => toggleDocSelection(doc.id)}
            onRename={() => setRenameDoc(doc)}
            onDelete={() => setDeleteDoc(doc)}
          />
        ))}
      </div>

      {/* Empty Library State */}
      {isLibraryEmpty && (
        <div className="py-12 text-center max-w-sm mx-auto space-y-4">
          <div className="h-12 w-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500 mx-auto">
            <FileText className="h-5 w-5" />
          </div>
          <div>
            <h4 className="text-xs font-semibold text-white">Document Library Empty</h4>
            <p className="text-[10px] text-slate-400 mt-1 leading-relaxed">
              Drag & drop files or click browse to upload enterprise knowledge bases and initialize indexes.
            </p>
          </div>
        </div>
      )}

      {/* Empty Search Results */}
      {isSearchEmpty && (
        <div className="py-12 text-center max-w-sm mx-auto space-y-4">
          <div className="h-12 w-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500 mx-auto">
            <Search className="h-5 w-5" />
          </div>
          <div>
            <h4 className="text-xs font-semibold text-white">No Matching Documents</h4>
            <p className="text-[10px] text-slate-400 mt-1 leading-relaxed">
              Adjust search keywords or status filter options to locate documents.
            </p>
          </div>
        </div>
      )}

      {/* Dialog Modals */}
      <RenameDocumentDialog
        isOpen={renameDoc !== null}
        currentName={renameDoc?.filename || ""}
        onClose={() => setRenameDoc(null)}
        onConfirm={(newName) => renameDocument(renameDoc!.id, newName)}
      />

      <DeleteDocumentDialog
        isOpen={deleteDoc !== null}
        filename={deleteDoc?.filename || ""}
        onClose={() => setDeleteDoc(null)}
        onConfirm={() => deleteDocument(deleteDoc!.id)}
      />
    </div>
  );
}
