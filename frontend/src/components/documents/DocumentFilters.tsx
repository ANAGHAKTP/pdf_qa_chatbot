"use client";

import React from "react";
import { Search, Filter, SortAsc, CheckCircle } from "lucide-react";

interface DocumentFiltersProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  statusFilter: string;
  setStatusFilter: (status: string) => void;
  sortBy: "pinned" | "recent" | "alpha";
  setSortBy: (sort: "pinned" | "recent" | "alpha") => void;
  onSelectAllFiltered: () => void;
  isAllFilteredSelected: boolean;
  filteredCount: number;
}

export function DocumentFilters({
  searchQuery,
  setSearchQuery,
  statusFilter,
  setStatusFilter,
  sortBy,
  setSortBy,
  onSelectAllFiltered,
  isAllFilteredSelected,
  filteredCount,
}: DocumentFiltersProps) {
  return (
    <div className="space-y-3">
      {/* Search Input bar */}
      <div className="relative">
        <input
          type="text"
          placeholder="Filter files by name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-lg pl-8 pr-3 py-1.5 text-xs text-white glass-input"
        />
        <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-slate-500" />
      </div>

      <div className="flex items-center justify-between gap-2.5">
        {/* Status Filter Tab Pills */}
        <div className="flex items-center gap-1">
          {["all", "ready", "indexing", "failed"].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-2 py-0.5.5 rounded text-[9px] font-bold uppercase tracking-wider transition-all border ${
                statusFilter === status
                  ? "bg-indigo-600/10 border-indigo-500/30 text-indigo-400"
                  : "bg-slate-900/40 border-transparent hover:border-slate-800 text-slate-400 hover:text-slate-300"
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {/* Sort Select */}
        <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
          <SortAsc className="h-3.5 w-3.5 shrink-0" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="bg-[#0B0D19] border border-slate-800 hover:border-slate-700 text-slate-300 rounded px-1.5 py-0.5 outline-none cursor-pointer transition-colors text-[9px] font-semibold"
          >
            <option value="recent">Recently Uploaded</option>
            <option value="pinned">RAG Selected</option>
            <option value="alpha">Alphabetical</option>
          </select>
        </div>
      </div>

      {/* Select All Toggle Button */}
      {filteredCount > 0 && (
        <button
          onClick={onSelectAllFiltered}
          className={`flex items-center gap-1.5 w-full justify-center py-1.5 px-3 rounded-lg border text-[10px] font-bold transition-all active:translate-y-[1px] ${
            isAllFilteredSelected
              ? "bg-indigo-500/10 border-indigo-500/30 text-indigo-400"
              : "bg-[#0E1122]/30 border-slate-800 text-slate-300 hover:border-slate-700"
          }`}
        >
          <CheckCircle className="h-3.5 w-3.5" />
          {isAllFilteredSelected ? "Deselect All Filtered" : `Select All Filtered (${filteredCount})`}
        </button>
      )}
    </div>
  );
}
