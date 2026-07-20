"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/lib/AuthContext";
import { User, LogOut, Shield, Calendar, Mail, Settings, ShieldAlert, ArrowRight, Sparkles } from "lucide-react";

export default function ProfilePage() {
  const { user, logout, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B0D19] text-white">
        <div className="text-center space-y-3">
          <div className="h-8 w-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading user profile...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  const creationDate = new Date(user.created_at).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

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
              href="/settings/sessions"
              className="text-xs font-semibold text-slate-300 hover:text-white transition-colors flex items-center gap-1"
            >
              <Settings className="h-3.5 w-3.5" />
              Sessions
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
          <h1 className="text-3xl font-extrabold text-white tracking-tight">User Settings</h1>
          <p className="text-sm text-slate-400 mt-1">Manage your enterprise account details and authentication state</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Settings Navigation Menu */}
          <div className="space-y-2 md:col-span-1">
            <Link
              href="/profile"
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-sm font-semibold text-indigo-400 transition-all"
            >
              <User className="h-4 w-4" />
              Account Profile
            </Link>
            <Link
              href="/settings/sessions"
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg hover:bg-slate-900 border border-transparent hover:border-slate-800 text-sm font-semibold text-slate-400 hover:text-slate-200 transition-all"
            >
              <Settings className="h-4 w-4" />
              Active Sessions
            </Link>
          </div>

          {/* Settings Panels */}
          <div className="md:col-span-2 space-y-6">
            {/* Account Details Panel */}
            <div className="glass-panel rounded-xl p-6 relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500/50 to-purple-500/50" />
              <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-400" />
                Profile Information
              </h2>

              <div className="space-y-6">
                <div className="flex items-center gap-4">
                  <div className="h-16 w-16 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-extrabold text-2xl">
                    {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">{user.full_name || "Enterprise User"}</h3>
                    <p className="text-xs text-slate-400">Personal Account</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-4 border-t border-slate-800">
                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 flex items-center gap-1.5">
                      <Mail className="h-3 w-3" /> Email Address
                    </span>
                    <p className="text-sm font-medium text-slate-200">{user.email}</p>
                  </div>

                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 flex items-center gap-1.5">
                      <Shield className="h-3 w-3" /> Security Role
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span className="inline-flex items-center text-[10px] font-bold text-indigo-400 bg-indigo-950/40 border border-indigo-900/60 px-2 py-0.5 rounded-full uppercase">
                        {user.role}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 flex items-center gap-1.5">
                      <Calendar className="h-3 w-3" /> Date Joined
                    </span>
                    <p className="text-sm font-medium text-slate-200">{creationDate}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Session Management Quick Link Card */}
            <div className="glass-card rounded-xl p-6 border border-slate-800 flex items-center justify-between">
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-white">Active Sessions</h3>
                <p className="text-xs text-slate-400">
                  You are currently logged in. Monitor your active device sessions for security.
                </p>
              </div>
              <Link
                href="/settings/sessions"
                className="h-10 w-10 rounded-lg bg-indigo-600/10 border border-indigo-500/20 hover:bg-indigo-600/20 flex items-center justify-center text-indigo-400 hover:text-indigo-300 transition-all shrink-0 ml-4"
              >
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
