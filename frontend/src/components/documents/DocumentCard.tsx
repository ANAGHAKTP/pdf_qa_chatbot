"use client";

import React, { useState } from "react";
import {
  FileText,
  Calendar,
  Database,
  Layers,
  Globe,
  Settings,
  Trash2,
  Edit3,
  ChevronDown,
  ChevronUp,
  FileSpreadsheet,
} from "lucide-react";
import { Document } from "@/types/workspace";
import { ProcessingStepper } from "./ProcessingStepper";

interface DocumentCardProps {
  doc: Document;
  isSelected: boolean;
  onSelect: () => void;
  onRename: () => void;
  onDelete: () => void;
}

export function DocumentCard({ doc, isSelected, onSelect, onRename, onDelete }: DocumentCardProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  const formattedSize = (doc.file_size / 1024).toFixed(0) + " KB";
  const formattedDate = new Date(doc.created_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      className={`glass-card rounded-xl border relative overflow-hidden transition-all duration-300 ${
        isSelected
          ? "bg-indigo-500/5 border-indigo-500/40 shadow-lg shadow-indigo-600/5"
          : "border-slate-800 bg-[#0E1122]/30 hover:border-slate-700"
      }`}
    >
      <div className="p-4 flex items-start justify-between gap-3">
        {/* Left Checkbox and Icon */}
        <div className="flex items-start gap-3 min-w-0 flex-1">
          <button
            type="button"
            onClick={onSelect}
            className={`h-4.5 w-4.5 rounded border flex items-center justify-center shrink-0 transition-all ${
              isSelected
                ? "bg-indigo-600 border-indigo-500 text-white"
                : "border-slate-800 bg-slate-950/60 text-transparent hover:border-slate-700"
            }`}
          >
            <span className="text-[10px] font-bold">✓</span>
          </button>

          <div className="min-w-0 space-y-1">
            <h4
              onClick={onSelect}
              className="text-xs font-bold text-white hover:text-indigo-400 cursor-pointer truncate transition-colors"
              title={doc.filename}
            >
              {doc.filename}
            </h4>

            {/* Metadata Pills */}
            <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 text-[9px] text-slate-400">
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3 shrink-0" />
                {formattedDate}
              </span>
              <span className="flex items-center gap-1">
                <Database className="h-3 w-3 shrink-0" />
                {formattedSize}
              </span>
              <span className="flex items-center gap-1">
                <Layers className="h-3 w-3 shrink-0" />
                {doc.chunk_count} Chunks
              </span>
              {doc.page_count && (
                <span className="flex items-center gap-1 bg-slate-900 border border-slate-800 px-1 rounded">
                  {doc.page_count} Pages
                </span>
              )}
              {doc.language && (
                <span className="flex items-center gap-1 bg-slate-900 border border-slate-800 px-1 rounded uppercase">
                  <Globe className="h-2.5 w-2.5 shrink-0" />
                  {doc.language}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Right Actions Menu Button */}
        <div className="relative shrink-0">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="h-7 w-7 rounded-lg hover:bg-slate-800/80 border border-transparent hover:border-slate-800 flex items-center justify-center text-slate-400 hover:text-white transition-all active:translate-y-[1px]"
          >
            <Settings className="h-3.5 w-3.5" />
          </button>

          {showMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowMenu(false)}
              />
              <div className="absolute right-0 mt-1 w-32 rounded-lg bg-[#0F1224] border border-slate-800 shadow-xl z-20 overflow-hidden text-[10px] animate-fade-in">
                <button
                  onClick={() => {
                    onRename();
                    setShowMenu(false);
                  }}
                  className="flex items-center gap-1.5 w-full px-3 py-2 text-left text-slate-300 hover:bg-slate-900 hover:text-white transition-colors"
                >
                  <Edit3 className="h-3.5 w-3.5" /> Rename
                </button>
                <button
                  onClick={() => {
                    setShowDetails(!showDetails);
                    setShowMenu(false);
                  }}
                  className="flex items-center gap-1.5 w-full px-3 py-2 text-left text-slate-300 hover:bg-slate-900 hover:text-white transition-colors"
                >
                  {showDetails ? (
                    <>
                      <ChevronUp className="h-3.5 w-3.5" /> Hide Details
                    </>
                  ) : (
                    <>
                      <ChevronDown className="h-3.5 w-3.5" /> View Details
                    </>
                  )}
                </button>
                <button
                  onClick={() => {
                    onDelete();
                    setShowMenu(false);
                  }}
                  className="flex items-center gap-1.5 w-full px-3 py-2 text-left text-rose-400 hover:bg-rose-950/20 hover:text-rose-300 border-t border-slate-900 transition-colors"
                >
                  <Trash2 className="h-3.5 w-3.5" /> Delete
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Stepper Details Accordion */}
      {showDetails && (
        <div className="px-4 pb-4 animate-fade-in border-t border-slate-900/60 pt-3 bg-black/10">
          <ProcessingStepper status={doc.status} />
        </div>
      )}
    </div>
  );
}
