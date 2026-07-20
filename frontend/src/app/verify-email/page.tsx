"use client";

import React, { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/AuthContext";
import { Mail, CheckCircle2, AlertCircle, Loader2, Send } from "lucide-react";

function VerifyEmailContent() {
  const { verifyEmail, resendVerification } = useAuth();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [verifying, setVerifying] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Resend fields
  const [email, setEmail] = useState("");
  const [resending, setResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  useEffect(() => {
    const performVerification = async () => {
      if (!token) return;
      setVerifying(true);
      setError(null);
      try {
        await verifyEmail(token);
        setSuccess(true);
      } catch (err: any) {
        setError(err.message || "Invalid or expired verification token.");
      } finally {
        setVerifying(false);
      }
    };

    performVerification();
  }, [token]);

  const handleResend = async (e: React.FormEvent) => {
    e.preventDefault();
    setResending(true);
    setError(null);
    setResendSuccess(false);
    try {
      await resendVerification(email);
      setResendSuccess(true);
    } catch (err: any) {
      setError(err.message || "Failed to resend verification email.");
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="w-full max-w-md animate-slide-up">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-extrabold tracking-tight text-white">Email Verification</h2>
        <p className="mt-2 text-sm text-slate-400">Activate your DOCMind Enterprise profile</p>
      </div>

      <div className="glass-panel rounded-2xl p-8 shadow-2xl relative">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-indigo-500 to-transparent" />

        {verifying && (
          <div className="text-center py-8 space-y-4">
            <Loader2 className="h-10 w-10 text-indigo-500 animate-spin mx-auto" />
            <p className="text-sm text-slate-300">Validating activation link...</p>
          </div>
        )}

        {!verifying && success && (
          <div className="text-center py-6">
            <div className="mx-auto h-12 w-12 rounded-full bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-6 animate-pulse">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Account Verified!</h3>
            <p className="text-sm text-slate-300 mb-6">
              Your email address has been successfully verified. You can now access your workspace.
            </p>
            <Link
              href="/login"
              className="inline-flex w-full justify-center py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-sm font-semibold text-white shadow-lg transition-all active:translate-y-[1px]"
            >
              Sign In to App
            </Link>
          </div>
        )}

        {!verifying && !success && (
          <div className="space-y-6">
            {error && (
              <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-start gap-3 animate-fade-in">
                <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
                <div className="text-xs text-rose-300 font-medium">{error}</div>
              </div>
            )}

            {resendSuccess && (
              <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-start gap-3 animate-fade-in">
                <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
                <div className="text-xs text-emerald-300 font-medium">
                  A new activation link has been sent to your email.
                </div>
              </div>
            )}

            <div>
              <h3 className="text-lg font-semibold text-white mb-2">
                {token ? "Verification Failed" : "Verify Your Email"}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                {token
                  ? "The link may be expired or already used. Enter your email below to request a new verification link."
                  : "Please check your inbox for the activation link. If you did not receive it, request a new one below."}
              </p>
            </div>

            <form onSubmit={handleResend} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <Mail className="h-4 w-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="glass-input block w-full pl-10 pr-4 py-2 rounded-lg text-sm text-white placeholder-slate-500"
                    placeholder="name@company.com"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={resending}
                className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-sm font-semibold text-white shadow-lg active:translate-y-[1px] disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center justify-center gap-2"
              >
                {resending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    Resend Verification Link
                  </>
                )}
              </button>
            </form>

            <div className="text-center">
              <Link
                href="/login"
                className="text-xs font-medium text-slate-400 hover:text-white transition-colors"
              >
                Back to Sign In
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-violet-600/10 blur-[120px] pointer-events-none" />
      
      <Suspense fallback={
        <div className="text-center py-8">
          <Loader2 className="h-10 w-10 text-indigo-500 animate-spin mx-auto" />
          <p className="text-sm text-slate-300 mt-4">Loading verification state...</p>
        </div>
      }>
        <VerifyEmailContent />
      </Suspense>
    </div>
  );
}
