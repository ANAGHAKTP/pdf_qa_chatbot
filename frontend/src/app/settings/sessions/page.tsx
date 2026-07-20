"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/AuthContext";
import { request } from "@/lib/api";
import {
  User,
  LogOut,
  Settings,
  Sparkles,
  Laptop,
  Smartphone,
  Globe,
  Trash2,
  AlertCircle,
  Loader2,
  CheckCircle2,
  ShieldAlert,
} from "lucide-react";

interface SessionData {
  id: number;
  device_name: string | null;
  browser: string | null;
  operating_system: string | null;
  ip_address: string | null;
  last_activity: string;
  created_at: string;
  is_current: boolean;
}

export default function SessionsPage() {
  const { user, logout, loading: authLoading } = useAuth();
  const [sessions, setSessions] = useState<SessionData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const fetchSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await request("/sessions");
      setSessions(data);
    } catch (err: any) {
      setError(err.message || "Failed to load active sessions.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchSessions();
    }
  }, [user]);

  const handleRevoke = async (sessionId: number) => {
    setError(null);
    setFeedback(null);
    try {
      await request(`/sessions/${sessionId}`, { method: "DELETE" });
      setFeedback("Session successfully revoked.");
      // Refresh list
      fetchSessions();
    } catch (err: any) {
      setError(err.message || "Failed to revoke session.");
    }
  };

  const handleRevokeOthers = async () => {
    if (!window.confirm("Are you sure you want to log out of all other devices?")) return;
    setError(null);
    setFeedback(null);
    try {
      await request("/sessions/others", { method: "DELETE" });
      setFeedback("Other sessions successfully revoked.");
      // Refresh list
      fetchSessions();
    } catch (err: any) {
      setError(err.message || "Failed to revoke other sessions.");
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B0D19] text-white">
        <div className="text-center space-y-3">
          <div className="h-8 w-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading profile context...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-[#0B0D19] text-slate-200">
      {/* Top Navbar */}
      <nav className="border-b border-slate-800 bg-[#0E1122]/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-extrabold text-lg">
              D
            </div>
            <span className="font-extrabold text-white tracking-wider text-sm hidden sm:inline-block">
              DOCMIND <span className="text-indigo-400 font-medium">ENTERPRISE</span>
            </span>
          </div>

          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-xs font-semibold text-slate-300 hover:text-white transition-colors"
            >
              Workspace
            </Link>
            <Link
              href="/profile"
              className="text-xs font-semibold text-slate-300 hover:text-white transition-colors flex items-center gap-1"
            >
              <User className="h-3.5 w-3.5" />
              Profile
            </Link>
            <button
              onClick={logout}
              className="px-3 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-900 text-xs font-semibold text-slate-300 hover:text-white transition-all flex items-center gap-1.5 active:translate-y-[1px]"
            >
              <LogOut className="h-3.5 w-3.5" />
              Sign Out
            </button>
          </div>
        </div>
      </nav>

      {/* Main Container */}
      <main className="max-w-4xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Active Sessions</h1>
          <p className="text-sm text-slate-400 mt-1">Review and manage your active login sessions across devices</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Settings Navigation Menu */}
          <div className="space-y-2 md:col-span-1">
            <Link
              href="/profile"
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg hover:bg-slate-900 border border-transparent hover:border-slate-800 text-sm font-semibold text-slate-400 hover:text-slate-200 transition-all"
            >
              <User className="h-4 w-4" />
              Account Profile
            </Link>
            <Link
              href="/settings/sessions"
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-sm font-semibold text-indigo-400 transition-all"
            >
              <Settings className="h-4 w-4" />
              Active Sessions
            </Link>
          </div>

          {/* Settings Panel */}
          <div className="md:col-span-2 space-y-6">
            {error && (
              <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-start gap-3 animate-fade-in">
                <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
                <div className="text-xs text-rose-300 font-medium">{error}</div>
              </div>
            )}

            {feedback && (
              <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-start gap-3 animate-fade-in">
                <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
                <div className="text-xs text-emerald-300 font-medium">{feedback}</div>
              </div>
            )}

            {/* Session Management Header Panel */}
            <div className="glass-panel rounded-xl p-6 relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500/50 to-purple-500/50" />
              
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-indigo-400" />
                  Devices Logged In
                </h2>
                
                {sessions.filter(s => !s.is_current).length > 0 && (
                  <button
                    onClick={handleRevokeOthers}
                    className="px-3 py-1.5 rounded-lg bg-rose-600/15 border border-rose-500/25 hover:bg-rose-600/25 text-rose-400 hover:text-rose-300 text-xs font-semibold active:translate-y-[1px] transition-all flex items-center gap-1.5"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Revoke Other Sessions
                  </button>
                )}
              </div>

              {loading ? (
                <div className="text-center py-8 space-y-3">
                  <Loader2 className="h-8 w-8 text-indigo-500 animate-spin mx-auto" />
                  <p className="text-xs text-slate-400">Loading active sessions...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {sessions.map((session) => {
                    const isMobile = session.device_name?.toLowerCase() === "mobile";
                    const DeviceIcon = isMobile ? Smartphone : Laptop;
                    
                    return (
                      <div
                        key={session.id}
                        className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
                          session.is_current
                            ? "bg-indigo-500/5 border-indigo-500/30"
                            : "bg-slate-900/40 border-slate-800 hover:border-slate-700"
                        }`}
                      >
                        <div className="flex items-center gap-3.5 min-w-0">
                          <div className={`h-10 w-10 rounded-lg flex items-center justify-center shrink-0 ${
                            session.is_current
                              ? "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30"
                              : "bg-slate-800 text-slate-400 border border-slate-700"
                          }`}>
                            <DeviceIcon className="h-5 w-5" />
                          </div>

                          <div className="min-w-0 space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-bold text-white">
                                {session.operating_system || "Unknown OS"} ({session.browser || "Unknown Browser"})
                              </span>
                              {session.is_current && (
                                <span className="inline-flex items-center text-[9px] font-bold text-indigo-400 bg-indigo-950/50 border border-indigo-900/80 px-2 py-0.5 rounded-full">
                                  Current Session
                                </span>
                              )}
                            </div>
                            
                            <div className="flex flex-col sm:flex-row sm:items-center gap-x-3 gap-y-0.5 text-xs text-slate-400">
                              <span className="flex items-center gap-1">
                                <Globe className="h-3 w-3 shrink-0" />
                                {session.ip_address || "Unknown IP"}
                              </span>
                              <span className="hidden sm:inline text-slate-600">•</span>
                              <span>
                                Active: {new Date(session.last_activity).toLocaleString()}
                              </span>
                            </div>
                          </div>
                        </div>

                        {!session.is_current && (
                          <button
                            onClick={() => handleRevoke(session.id)}
                            className="h-8 w-8 rounded-lg border border-slate-800 hover:border-rose-500/30 bg-slate-900/60 hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 flex items-center justify-center transition-all shrink-0 ml-4 active:translate-y-[1px]"
                            title="Revoke session"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
