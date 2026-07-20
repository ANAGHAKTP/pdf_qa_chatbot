"use client";

import React, { useState } from "react";
import {
  X,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  FileText,
  BookOpen,
  Award,
  Layers,
  Search,
} from "lucide-react";
import { Document, Citation } from "@/types/workspace";

interface PdfPreviewPanelProps {
  isOpen: boolean;
  onClose: () => void;
  document: Document | null;
  targetPage?: number;
  highlightCitation?: Citation | null;
}

export function PdfPreviewPanel({
  isOpen,
  onClose,
  document,
  targetPage = 1,
  highlightCitation = null,
}: PdfPreviewPanelProps) {
  const [currentPage, setCurrentPage] = useState(targetPage);
  const [zoomScale, setZoomScale] = useState(100);
  const [activeTab, setActiveTab] = useState<"preview" | "outline" | "metadata">("preview");

  if (!isOpen || !document) return null;

  const totalPages = document.page_count || 1;
  const isScanned = document.metadata?.is_scanned || false;
  const ocrConfidence = document.metadata?.ocr_confidence ? (document.metadata.ocr_confidence * 100).toFixed(0) : "100";
  const tableCount = document.metadata?.table_count || 0;
  const figureCount = document.metadata?.figure_count || 0;
  const language = (document.metadata?.language || document.language || "en").toUpperCase();
  const category = document.metadata?.document_category || "General Document";

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4 animate-fade-in">
      <div className="w-full max-w-5xl h-[85vh] rounded-2xl glass-panel shadow-2xl border border-slate-800 flex flex-col overflow-hidden animate-slide-up relative">
        {/* Top Preview Header */}
        <header className="px-5 py-3 border-b border-slate-800 flex items-center justify-between bg-black/40">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="h-8 w-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <FileText className="h-4 w-4" />
            </div>
            <div className="overflow-hidden">
              <h3 className="text-xs font-bold text-white truncate">{document.filename}</h3>
              <div className="flex items-center gap-2 text-[9px] text-slate-400">
                <span>Page {currentPage} of {totalPages}</span>
                <span>·</span>
                <span className="text-indigo-400 uppercase font-semibold">{category}</span>
                <span>·</span>
                <span className="bg-slate-900 border border-slate-800 px-1 rounded">{language}</span>
              </div>
            </div>
          </div>

          {/* Controls Bar */}
          <div className="flex items-center gap-3">
            {/* Zoom controls */}
            <div className="flex items-center gap-1 bg-slate-900/60 border border-slate-800 rounded-lg p-1 text-[10px]">
              <button
                onClick={() => setZoomScale(Math.max(50, zoomScale - 15))}
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                title="Zoom Out"
              >
                <ZoomOut className="h-3.5 w-3.5" />
              </button>
              <span className="font-mono px-1.5 text-slate-300">{zoomScale}%</span>
              <button
                onClick={() => setZoomScale(Math.min(200, zoomScale + 15))}
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                title="Zoom In"
              >
                <ZoomIn className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Page navigation */}
            <div className="flex items-center gap-1 bg-slate-900/60 border border-slate-800 rounded-lg p-1 text-[10px]">
              <button
                onClick={handlePrevPage}
                disabled={currentPage <= 1}
                className="p-1 rounded hover:bg-slate-800 disabled:opacity-40 text-slate-400 hover:text-white transition-colors"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
              </button>
              <span className="font-mono px-2 text-slate-300">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={handleNextPage}
                disabled={currentPage >= totalPages}
                className="p-1 rounded hover:bg-slate-800 disabled:opacity-40 text-slate-400 hover:text-white transition-colors"
              >
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>

            <button
              onClick={onClose}
              className="h-7 w-7 rounded-lg bg-slate-900 hover:bg-rose-950/40 border border-slate-800 text-slate-400 hover:text-rose-300 flex items-center justify-center transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </header>

        {/* Viewport Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Main Document Viewer Canvas */}
          <div className="flex-1 overflow-auto p-6 bg-[#060810] flex flex-col items-center justify-start space-y-4">
            {/* Citation Highlight Banner if active */}
            {highlightCitation && (
              <div className="w-full max-w-2xl p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-xs text-indigo-300 space-y-1.5 animate-fade-in shadow-lg">
                <div className="flex items-center justify-between font-bold text-[10px] uppercase tracking-wider text-indigo-400">
                  <span className="flex items-center gap-1">
                    <BookOpen className="h-3.5 w-3.5" /> Cited Passages on Page {highlightCitation.page}
                  </span>
                  <span className="bg-indigo-600/20 border border-indigo-500/30 px-2 py-0.5 rounded flex items-center gap-1">
                    <Award className="h-2.5 w-2.5" /> Match {(highlightCitation.score * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="italic font-sans text-slate-200 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 leading-relaxed">
                  "{highlightCitation.highlighted_paragraph}"
                </p>
              </div>
            )}

            {/* Embedded Page Frame */}
            <div
              className="bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl text-slate-300 space-y-4 min-h-[600px] w-full max-w-2xl transition-all"
              style={{ transform: `scale(${zoomScale / 100})`, transformOrigin: "top center" }}
            >
              <div className="border-b border-slate-800 pb-3 flex justify-between text-[10px] text-slate-500 font-mono">
                <span>{document.filename}</span>
                <span>PAGE {currentPage}</span>
              </div>

              {/* Document Text Rendering View */}
              <div className="space-y-3 font-sans text-xs text-slate-300 leading-relaxed py-4">
                <h2 className="text-sm font-bold text-white border-b border-slate-800/60 pb-1">
                  Section Overview - Page {currentPage}
                </h2>
                <p>
                  This digital PDF page view incorporates multimodal extracted metadata, structural layout breaks, and chunk citations.
                </p>

                {highlightCitation && (
                  <mark className="bg-yellow-500/20 text-yellow-200 border-l-2 border-yellow-400 p-2 block rounded my-2 font-mono text-[11px]">
                    ★ HIGHLIGHTED CITATION EXCERPT: {highlightCitation.highlighted_paragraph}
                  </mark>
                )}

                <p className="text-slate-400 italic">
                  [Full PDF page stream loaded from server API: {API_URL}/documents/{document.id}/preview?page={currentPage}]
                </p>
              </div>
            </div>
          </div>

          {/* Right Sidebar Metadata Panel */}
          <aside className="w-72 border-l border-slate-800 bg-[#0A0D1B] p-4 flex flex-col space-y-4 shrink-0 overflow-y-auto">
            <div className="flex border-b border-slate-800 text-[10px] font-bold uppercase tracking-wider">
              <button
                onClick={() => setActiveTab("preview")}
                className={`flex-1 py-2 text-center border-b-2 transition-all ${
                  activeTab === "preview"
                    ? "border-indigo-500 text-indigo-400"
                    : "border-transparent text-slate-500 hover:text-slate-300"
                }`}
              >
                Structure
              </button>
              <button
                onClick={() => setActiveTab("metadata")}
                className={`flex-1 py-2 text-center border-b-2 transition-all ${
                  activeTab === "metadata"
                    ? "border-indigo-500 text-indigo-400"
                    : "border-transparent text-slate-500 hover:text-slate-300"
                }`}
              >
                Metadata
              </button>
            </div>

            {activeTab === "preview" ? (
              <div className="space-y-3 text-xs">
                <div className="p-3 rounded-xl bg-black/20 border border-slate-800/80 space-y-2">
                  <p className="text-[9px] uppercase font-bold text-slate-500">Document Outline</p>
                  <div className="space-y-1.5 text-[10px]">
                    <div className="p-1.5 rounded bg-slate-900/60 border border-slate-800/60 text-slate-300 cursor-pointer hover:text-white" onClick={() => setCurrentPage(1)}>
                      1. Executive Summary (p. 1)
                    </div>
                    <div className="p-1.5 rounded bg-slate-900/60 border border-slate-800/60 text-slate-300 cursor-pointer hover:text-white" onClick={() => setCurrentPage(Math.min(2, totalPages))}>
                      2. Financial Data Tables (p. 2)
                    </div>
                    <div className="p-1.5 rounded bg-slate-900/60 border border-slate-800/60 text-slate-300 cursor-pointer hover:text-white" onClick={() => setCurrentPage(Math.min(3, totalPages))}>
                      3. Regulatory Risk Analysis (p. 3)
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-black/20 border border-slate-800/80 space-y-2">
                  <p className="text-[9px] uppercase font-bold text-slate-500">Extracted Assets</p>
                  <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                    <div className="p-2 rounded bg-slate-950/40 border border-slate-800">
                      <p className="text-[8px] uppercase text-slate-500">Tables</p>
                      <p className="text-white font-bold text-sm mt-0.5">{tableCount}</p>
                    </div>
                    <div className="p-2 rounded bg-slate-950/40 border border-slate-800">
                      <p className="text-[8px] uppercase text-slate-500">Figures</p>
                      <p className="text-white font-bold text-sm mt-0.5">{figureCount}</p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-3 text-[10px] text-slate-300">
                <div className="p-3 rounded-xl bg-black/20 border border-slate-800/80 space-y-2">
                  <p className="text-[9px] uppercase font-bold text-slate-500">Processing Stats</p>
                  <div className="space-y-1 font-mono">
                    <div className="flex justify-between py-1 border-b border-slate-900">
                      <span className="text-slate-500">OCR Status</span>
                      <span className={isScanned ? "text-amber-400 font-bold" : "text-emerald-400 font-bold"}>
                        {isScanned ? `Scanned (${ocrConfidence}%)` : "Digital PDF"}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-900">
                      <span className="text-slate-500">Detected Language</span>
                      <span className="text-white uppercase">{language}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-900">
                      <span className="text-slate-500">Total Pages</span>
                      <span className="text-white">{totalPages}</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-500">Chunk Count</span>
                      <span className="text-white">{document.chunk_count}</span>
                    </div>
                  </div>
                </div>

                {document.metadata?.keywords && (
                  <div className="p-3 rounded-xl bg-black/20 border border-slate-800/80 space-y-2">
                    <p className="text-[9px] uppercase font-bold text-slate-500">Keyword Tags</p>
                    <div className="flex flex-wrap gap-1">
                      {document.metadata.keywords.map((kw: string, idx: number) => (
                        <span key={idx} className="bg-indigo-500/10 border border-indigo-500/20 px-1.5 py-0.5 rounded text-[8px] text-indigo-300">
                          #{kw}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
}
export default PdfPreviewPanel;
