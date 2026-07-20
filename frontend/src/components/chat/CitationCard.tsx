"use client";

import React from "react";
import { BookOpen, Award, Hash } from "lucide-react";
import { Citation } from "@/types/workspace";

interface CitationCardProps {
  citation: Citation;
  onOpenPreview?: (docId: number, page: number, citation: Citation) => void;
}

export function CitationCard({ citation, onOpenPreview }: CitationCardProps) {
  const confidenceScore = (citation.score * 100).toFixed(0);
  const chunkId = citation.chunk_id || `${citation.doc_id}_${citation.page}_${citation.chunk_idx}`;

  const handleJumpToPage = () => {
    if (onOpenPreview) {
      onOpenPreview(citation.doc_id, citation.page, citation);
    } else {
      alert(`Jump to ${citation.filename} - Page ${citation.page}`);
    }
  };

  return (
    <div className="p-3 rounded-lg bg-black/45 border border-slate-800 text-xs font-mono text-slate-400 flex flex-col gap-2 hover:border-indigo-500/30 transition-all hover:bg-slate-900/10">
      <div className="flex items-center justify-between mb-0.5 font-bold text-indigo-400 gap-2">
        <span className="truncate max-w-[220px] text-[10px] flex items-center gap-1">
          [{citation.citation_num}] {citation.filename} · Page {citation.page}
        </span>
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="bg-slate-900 border border-slate-800 px-1.5 py-0.5 rounded text-[8px] text-slate-500 flex items-center gap-0.5" title="Chunk Unique Identifier">
            <Hash className="h-2.5 w-2.5" />
            {chunkId}
          </span>
          <span className="bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded text-[9px] flex items-center gap-1 text-indigo-400">
            <Award className="h-2.5 w-2.5" />
            Match {confidenceScore}%
          </span>
        </div>
      </div>
      
      <p className="text-slate-300 italic font-sans leading-normal line-clamp-3">
        "{citation.highlighted_paragraph.trim()}"
      </p>

      <div className="flex justify-end pt-1">
        <button
          onClick={handleJumpToPage}
          className="text-[9px] uppercase tracking-wider font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5 transition-colors focus:outline-none"
        >
          <BookOpen className="h-3 w-3" /> View Source Page
        </button>
      </div>
    </div>
  );
}
export default CitationCard;
