"use client";

import React, { useState } from "react";
import { Trash2, X, Loader2, AlertTriangle } from "lucide-react";

interface DeleteDocumentDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  filename: string;
}

export function DeleteDocumentDialog({ isOpen, onClose, onConfirm, filename }: DeleteDocumentDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDelete = async () => {
    setLoading(true);
    setError(null);
    try {
      await onConfirm();
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to delete document.");
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
      <div className="w-full max-w-md rounded-2xl glass-panel p-6 shadow-2xl border border-slate-800 animate-slide-up relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
        >
          <X className="h-4 w-4" />
        </button>

        <h3 className="text-md font-bold text-white flex items-center gap-2 mb-2">
          <AlertTriangle className="h-4.5 w-4.5 text-rose-500 animate-pulse" />
          Delete Document
        </h3>
        
        <div className="p-3.5 rounded-lg bg-rose-950/20 border border-rose-900/30 text-rose-300 text-xs leading-normal mb-4">
          Warning: This action is permanent! Deleting <span className="font-semibold text-white">"{filename}"</span> will purge all associated embedding vectors and index fragments.
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-medium">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            disabled={loading}
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-900/50 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={handleDelete}
            className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-xs font-semibold text-white shadow-lg active:translate-y-[1px] disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center gap-1.5"
          >
            {loading ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <Trash2 className="h-3.5 w-3.5" />
                Confirm Delete
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
