"use client";

import React, { useState } from "react";
import { Upload, FileText, CheckCircle2, AlertCircle } from "lucide-react";

interface UploadDropzoneProps {
  onUpload: (files: FileList) => void;
  isUploading: boolean;
  uploadProgress: Record<string, number>;
}

export function UploadDropzone({ onUpload, isUploading, uploadProgress }: UploadDropzoneProps) {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onUpload(e.dataTransfer.files);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files);
    }
  };

  const progressFiles = Object.entries(uploadProgress).filter(([_, val]) => val < 100 && val >= 0);
  const completedCount = Object.values(uploadProgress).filter((v) => v === 100).length;

  return (
    <div
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      className={`relative border-2 border-dashed rounded-xl p-6 text-center transition-all ${
        dragActive
          ? "border-indigo-500 bg-indigo-500/5 scale-[1.01]"
          : "border-slate-800 hover:border-slate-700 bg-[#0E1122]/30"
      }`}
    >
      {dragActive && (
        <div className="absolute inset-0 bg-indigo-600/10 backdrop-blur-[2px] rounded-xl flex items-center justify-center text-indigo-400 font-bold text-sm pointer-events-none z-10">
          Drop PDF files here to upload
        </div>
      )}

      <div className="flex flex-col items-center justify-center space-y-3">
        <div className="h-10 w-10 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400">
          <Upload className="h-5 w-5" />
        </div>
        
        <div>
          <p className="text-xs font-bold text-white">Drag & drop your files here</p>
          <p className="text-[10px] text-slate-400 mt-1">or click to browse local files (PDF only)</p>
        </div>

        <label className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white cursor-pointer shadow-lg shadow-indigo-600/10 active:translate-y-[1px] transition-all">
          Browse Files
          <input
            type="file"
            multiple
            accept=".pdf"
            onChange={handleFileInput}
            className="hidden"
          />
        </label>
      </div>

      {/* Upload Progress Tracker Overlay */}
      {(isUploading || progressFiles.length > 0) && (
        <div className="mt-4 p-3 rounded-lg bg-black/40 border border-slate-800/80 text-left space-y-2 animate-fade-in text-[10px]">
          <p className="font-bold text-slate-300 flex items-center justify-between">
            <span>Uploading Documents...</span>
            <span className="font-mono text-indigo-400">{completedCount} Completed</span>
          </p>

          <div className="space-y-2 max-h-[120px] overflow-y-auto pr-1">
            {Object.entries(uploadProgress).map(([filename, progress]) => {
              if (progress === -1) {
                return (
                  <div key={filename} className="flex items-center justify-between text-rose-400">
                    <span className="truncate max-w-[200px] flex items-center gap-1.5">
                      <AlertCircle className="h-3.5 w-3.5" /> {filename}
                    </span>
                    <span>Failed</span>
                  </div>
                );
              }
              return (
                <div key={filename} className="space-y-1">
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="truncate max-w-[200px] flex items-center gap-1.5">
                      <FileText className="h-3.5 w-3.5 text-indigo-400" /> {filename}
                    </span>
                    <span className="font-mono font-bold text-indigo-400">{progress}%</span>
                  </div>
                  <div className="h-1 w-full bg-slate-900 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 rounded-full transition-all duration-200"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
