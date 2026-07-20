"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/lib/AuthContext";
import { WorkspaceLayout } from "@/components/workspace/WorkspaceLayout";

export default function Home() {
  const { user, loading } = useAuth();
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0B0D19] text-white">
        <div className="text-center space-y-3">
          <div className="h-8 w-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading DOCMind Workspace...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return <WorkspaceLayout />;
}
