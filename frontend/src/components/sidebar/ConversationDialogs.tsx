"use client";

import React, { useState, useEffect } from "react";
import { MessageSquare, X, Plus, Edit3, Loader2 } from "lucide-react";

interface ConversationDialogsProps {
  createOpen: boolean;
  onCreateClose: () => void;
  onCreateConfirm: (title: string) => Promise<void>;
  
  renameOpen: boolean;
  onRenameClose: () => void;
  onRenameConfirm: (newTitle: string) => Promise<void>;
  currentRenameTitle: string;
}

export function ConversationDialogs({
  createOpen,
  onCreateClose,
  onCreateConfirm,
  renameOpen,
  onRenameClose,
  onRenameConfirm,
  currentRenameTitle,
}: ConversationDialogsProps) {
  // Create state
  const [createTitle, setCreateTitle] = useState("");
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Rename state
  const [renameTitle, setRenameTitle] = useState(currentRenameTitle);
  const [renameLoading, setRenameLoading] = useState(false);
  const [renameError, setRenameError] = useState<string | null>(null);

  useEffect(() => {
    if (createOpen) {
      setCreateTitle("");
      setCreateError(null);
    }
  }, [createOpen]);

  useEffect(() => {
    if (renameOpen) {
      setRenameTitle(currentRenameTitle);
      setRenameError(null);
    }
  }, [renameOpen, currentRenameTitle]);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createTitle.trim()) return;
    setCreateLoading(true);
    setCreateError(null);
    try {
      await onCreateConfirm(createTitle);
      onCreateClose();
    } catch (err: any) {
      setCreateError(err.message || "Failed to create conversation.");
    } finally {
      setCreateLoading(false);
    }
  };

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renameTitle.trim()) return;
    setRenameLoading(true);
    setRenameError(null);
    try {
      await onRenameConfirm(renameTitle);
      onRenameClose();
    } catch (err: any) {
      setRenameError(err.message || "Failed to rename conversation.");
    } finally {
      setRenameLoading(false);
    }
  };

  return (
    <>
      {/* Create Session Dialog */}
      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
          <div className="w-full max-w-md rounded-2xl glass-panel p-6 shadow-2xl border border-slate-800 animate-slide-up relative">
            <button
              onClick={onCreateClose}
              className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>

            <h3 className="text-md font-bold text-white flex items-center gap-2 mb-2">
              <Plus className="h-4.5 w-4.5 text-indigo-400" />
              New Conversation
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Initialize a clean discussion workspace.
            </p>

            {createError && (
              <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-medium">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div>
                <input
                  type="text"
                  required
                  value={createTitle}
                  onChange={(e) => setCreateTitle(e.target.value)}
                  className="glass-input block w-full px-3 py-2 rounded-lg text-xs text-white placeholder-slate-500"
                  placeholder="e.g. Q3 Financial Statement Audit"
                />
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={onCreateClose}
                  className="px-3 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-900/50 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createLoading || !createTitle.trim()}
                  className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg active:translate-y-[1px] disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center gap-1.5"
                >
                  {createLoading ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    "Create Session"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Rename Session Dialog */}
      {renameOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
          <div className="w-full max-w-md rounded-2xl glass-panel p-6 shadow-2xl border border-slate-800 animate-slide-up relative">
            <button
              onClick={onRenameClose}
              className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>

            <h3 className="text-md font-bold text-white flex items-center gap-2 mb-2">
              <Edit3 className="h-4.5 w-4.5 text-indigo-400" />
              Rename Conversation
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Edit the title name for this conversation session.
            </p>

            {renameError && (
              <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-medium">
                {renameError}
              </div>
            )}

            <form onSubmit={handleRenameSubmit} className="space-y-4">
              <div>
                <input
                  type="text"
                  required
                  value={renameTitle}
                  onChange={(e) => setRenameTitle(e.target.value)}
                  className="glass-input block w-full px-3 py-2 rounded-lg text-xs text-white placeholder-slate-500"
                  placeholder="Conversation title"
                />
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={onRenameClose}
                  className="px-3 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-900/50 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={renameLoading || !renameTitle.trim() || renameTitle.trim() === currentRenameTitle}
                  className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg active:translate-y-[1px] disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center gap-1.5"
                >
                  {renameLoading ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Renaming...
                    </>
                  ) : (
                    "Save Changes"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
export default ConversationDialogs;
