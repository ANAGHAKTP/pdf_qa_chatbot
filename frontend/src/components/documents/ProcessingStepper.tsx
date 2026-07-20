"use client";

import React from "react";
import { Check, Loader, AlertTriangle, Database } from "lucide-react";
import { DocStatus } from "@/types/workspace";

interface ProcessingStepperProps {
  status: DocStatus;
}

export function ProcessingStepper({ status }: ProcessingStepperProps) {
  const steps: { label: string; statusKey: DocStatus }[] = [
    { label: "Upload", statusKey: "uploading" },
    { label: "Extract", statusKey: "extracting" },
    { label: "Chunk", statusKey: "chunking" },
    { label: "Embed", statusKey: "embedding" },
    { label: "Index", statusKey: "indexing" },
    { label: "Ready", statusKey: "ready" },
  ];

  // Determine current active step index
  const getActiveIndex = () => {
    switch (status) {
      case "uploading": return 0;
      case "extracting": return 1;
      case "chunking": return 2;
      case "embedding": return 3;
      case "indexing": return 4;
      case "ready": return 5;
      default: return -1;
    }
  };

  const activeIndex = getActiveIndex();
  const isFailed = status === "failed";

  return (
    <div className="space-y-3 p-4 rounded-xl bg-black/40 border border-slate-800">
      <div className="flex items-center justify-between">
        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
          Processing Pipeline Status
        </span>
        {isFailed ? (
          <span className="inline-flex items-center gap-1 text-[9px] font-semibold text-rose-400 bg-rose-950/40 border border-rose-900/60 px-2 py-0.5 rounded-full">
            <AlertTriangle className="h-3 w-3" /> Failed
          </span>
        ) : status === "ready" ? (
          <span className="inline-flex items-center gap-1 text-[9px] font-semibold text-emerald-400 bg-emerald-950/40 border border-emerald-900/60 px-2 py-0.5 rounded-full">
            <Check className="h-3 w-3" /> Ready
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-[9px] font-semibold text-amber-400 bg-amber-950/40 border border-amber-900/60 px-2 py-0.5 rounded-full">
            <Loader className="h-3 w-3 animate-spin" /> In Progress
          </span>
        )}
      </div>

      <div className="flex items-center justify-between relative mt-2">
        {/* Horizontal bar backplate */}
        <div className="absolute left-3 right-3 top-3.5 h-[2px] bg-slate-800 -z-10" />
        
        {/* Active colored bar overlay */}
        {!isFailed && activeIndex >= 0 && (
          <div
            className="absolute left-3 top-3.5 h-[2px] bg-indigo-500 transition-all duration-300 -z-10"
            style={{ width: `${(activeIndex / (steps.length - 1)) * 92}%` }}
          />
        )}

        {steps.map((step, idx) => {
          const isCompleted = !isFailed && idx < activeIndex;
          const isActive = !isFailed && idx === activeIndex;
          const isPending = !isFailed && idx > activeIndex;

          return (
            <div key={step.label} className="flex flex-col items-center space-y-1">
              <div
                className={`h-7 w-7 rounded-full flex items-center justify-center border text-[10px] font-bold transition-all ${
                  isCompleted
                    ? "bg-emerald-950/60 border-emerald-500 text-emerald-400"
                    : isActive
                    ? "bg-indigo-950/80 border-indigo-500 text-indigo-400 animate-pulse scale-105"
                    : isFailed
                    ? "bg-rose-950/30 border-rose-900/40 text-rose-500"
                    : "bg-slate-900 border-slate-800 text-slate-500"
                }`}
              >
                {isCompleted ? (
                  <Check className="h-3.5 w-3.5" />
                ) : isActive ? (
                  <Loader className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  idx + 1
                )}
              </div>
              <span
                className={`text-[9px] font-medium tracking-wide ${
                  isActive ? "text-indigo-400 font-bold" : isCompleted ? "text-slate-300" : "text-slate-500"
                }`}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
