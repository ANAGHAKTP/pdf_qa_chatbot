"use client";

import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import {
  Upload,
  FolderPlus,
  Trash2,
  Edit3,
  MessageSquare,
  Plus,
  FileText,
  Activity,
  Check,
  AlertCircle,
  Settings,
  LogOut,
  ChevronRight,
  Send,
  Loader,
  Copy,
  ThumbsUp,
  ThumbsDown,
  Eye,
  Info,
  Calendar,
  ShieldAlert,
  Folder,
  TrendingUp,
  Database,
  Search,
  BookOpen,
  ArrowRight,
  RefreshCw,
  Clock,
  Sparkles,
  Download,
  Share2,
  Maximize2,
  List,
  AlertTriangle,
  Lightbulb,
  CheckCircle2,
  ScanSearch,
  Building2,
  Users,
  Table as TableIcon
} from "lucide-react";

import { request, saveTokens, clearTokens } from "@/lib/api";
import { User, Folder as IFolder, Document, ChatSession, ChatMessage, DocumentAnalysis } from "@/types";

// ── REUSABLE COMPONENT SKELETON ───────────────────────────────────────────
interface LoadingSkeletonProps {
  className?: string;
}
const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ className = "" }) => {
  return (
    <div className={`animate-shimmer rounded bg-panelBorder/40 ${className}`} />
  );
};

// ── REUSABLE KPI CARD ──────────────────────────────────────────────────────
interface KpiCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  description?: string;
  loading?: boolean;
}
const KpiCard: React.FC<KpiCardProps> = React.memo(({ title, value, icon, description, loading }) => {
  return (
    <div className="glass-card rounded-xl p-4 flex items-center justify-between border border-panelBorder/40 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-accent/5">
      <div className="space-y-1 flex-1 min-w-0">
        <p className="text-[10px] uppercase font-bold tracking-widest text-mutedText truncate">{title}</p>
        {loading ? (
          <LoadingSkeleton className="h-6 w-20 mt-1" />
        ) : (
          <h4 className="text-lg font-bold text-white tracking-tight truncate">{value}</h4>
        )}
        {description && <p className="text-[9px] text-mutedText truncate">{description}</p>}
      </div>
      <div className="h-9 w-9 shrink-0 rounded-lg bg-accent/10 border border-accent/25 flex items-center justify-center text-accent ml-3">
        {icon}
      </div>
    </div>
  );
});
KpiCard.displayName = "KpiCard";

// ── REUSABLE STATUS BADGE ──────────────────────────────────────────────────
interface StatusBadgeProps {
  status: string;
}
const StatusBadge: React.FC<StatusBadgeProps> = React.memo(({ status }) => {
  const normStatus = status.toLowerCase();
  
  if (normStatus === "uploading") {
    return (
      <span className="inline-flex items-center gap-1 text-[9px] font-semibold text-sky-400 bg-sky-950/40 border border-sky-900/60 px-2 py-0.5 rounded-full">
        <Upload className="h-2.5 w-2.5 animate-bounce" /> Uploading
      </span>
    );
  }
  if (normStatus === "indexing" || normStatus === "generating embeddings" || normStatus === "embedding") {
    return (
      <span className="inline-flex items-center gap-1 text-[9px] font-semibold text-amber-400 bg-amber-950/40 border border-amber-900/60 px-2 py-0.5 rounded-full">
        <Database className="h-2.5 w-2.5 animate-spin-slow" /> Indexing
      </span>
    );
  }
  if (normStatus === "processing") {
    return (
      <span className="inline-flex items-center gap-1 text-[9px] font-semibold text-indigo-400 bg-indigo-950/40 border border-indigo-900/60 px-2 py-0.5 rounded-full">
        <Loader className="h-2.5 w-2.5 animate-spin" /> Processing
      </span>
    );
  }
  if (normStatus === "ready" || normStatus === "indexed") {
    return (
      <span className="inline-flex items-center gap-1 text-[9px] font-semibold text-emerald-400 bg-emerald-950/40 border border-emerald-900/60 px-2 py-0.5 rounded-full">
        <Check className="h-2.5 w-2.5" /> Ready
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-[9px] font-semibold text-red-400 bg-red-950/40 border border-red-900/60 px-2 py-0.5 rounded-full">
      <AlertTriangle className="h-2.5 w-2.5" /> Error
    </span>
  );
});
StatusBadge.displayName = "StatusBadge";

// ── REUSABLE EMPTY STATE ───────────────────────────────────────────────────
interface EmptyStateProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
  };
}
const EmptyState: React.FC<EmptyStateProps> = React.memo(({ title, description, icon, action }) => {
  return (
    <div className="glass-card rounded-xl p-8 text-center border border-panelBorder/30 max-w-sm mx-auto flex flex-col items-center justify-center space-y-4 animate-fade-in">
      <div className="h-11 w-11 rounded-full bg-accent/10 border border-accent/25 flex items-center justify-center text-accent">
        {icon}
      </div>
      <div className="space-y-1">
        <h4 className="text-xs font-semibold text-white">{title}</h4>
        <p className="text-[11px] text-mutedText leading-relaxed">{description}</p>
      </div>
      {action && (
        <button
          onClick={action.onClick}
          className="inline-flex items-center gap-1.5 rounded-lg bg-accent hover:bg-accentHover transition-all px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-accent/20"
        >
          {action.icon}
          <span>{action.label}</span>
        </button>
      )}
    </div>
  );
});
EmptyState.displayName = "EmptyState";

// ── REUSABLE PROMPT CARD ───────────────────────────────────────────────────
interface PromptCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  onClick: () => void;
}
const PromptCard: React.FC<PromptCardProps> = React.memo(({ title, description, icon, onClick }) => {
  return (
    <div
      onClick={onClick}
      className="glass-card cursor-pointer rounded-xl p-4 border border-panelBorder/40 transition-all duration-300 hover:-translate-y-0.5 hover:border-accent/40 hover:bg-accent/5 flex flex-col justify-between"
    >
      <div className="flex items-start gap-2.5">
        <div className="h-7 w-7 shrink-0 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
          {icon}
        </div>
        <div className="space-y-0.5">
          <h5 className="text-xs font-semibold text-white">{title}</h5>
          <p className="text-[10px] text-mutedText leading-normal">{description}</p>
        </div>
      </div>
    </div>
  );
});
PromptCard.displayName = "PromptCard";

// ── DYNAMIC CITATION CARD ──────────────────────────────────────────────────
interface CitationCardProps {
  citation: any;
  onViewSource: () => void;
}
const CitationCard: React.FC<CitationCardProps> = React.memo(({ citation, onViewSource }) => {
  return (
    <div className="p-3 rounded-lg bg-black/45 border border-panelBorder/40 text-xs font-mono text-mutedText flex flex-col gap-2 hover:border-accent/20 transition-all">
      <div className="flex items-center justify-between mb-0.5 font-bold text-accent">
        <span className="truncate max-w-[220px]">[{citation.citation_num}] {citation.filename} · Page {citation.page}</span>
        <span className="shrink-0 bg-accent/10 border border-accent/20 px-2 py-0.5 rounded text-[9px]">Match {(citation.score * 100).toFixed(0)}%</span>
      </div>
      <p className="text-foreground/90 italic font-sans leading-normal line-clamp-2">"{citation.highlighted_paragraph.trim()}"</p>
      <div className="flex justify-end">
        <button
          onClick={onViewSource}
          className="text-[9px] uppercase tracking-wider font-bold text-accent hover:text-white flex items-center gap-1 mt-1 transition-all"
        >
          <BookOpen className="h-3 w-3" /> View Source
        </button>
      </div>
    </div>
  );
});
CitationCard.displayName = "CitationCard";

// ── CUSTOM LIGHTWEIGHT MARKDOWN RENDERER ──────────────────────────────────
interface MarkdownRendererProps {
  content: string;
}
const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  const parts = useMemo(() => {
    if (!content) return [];
    return content.split(/(```[\s\S]*?```)/g);
  }, [content]);

  return (
    <div className="space-y-2.5">
      {parts.map((part, index) => {
        if (part.startsWith("```")) {
          const match = part.match(/```(\w*)\n([\s\S]*?)```/);
          const lang = match ? match[1] : "";
          const code = match ? match[2] : part.slice(3, -3);

          return (
            <div key={index} className="my-2.5 rounded-lg overflow-hidden border border-panelBorder bg-black/40 font-mono text-xs">
              {lang && (
                <div className="bg-panelBorder/30 px-4 py-1 flex items-center justify-between text-[9px] uppercase font-bold text-mutedText border-b border-panelBorder/50">
                  <span>{lang}</span>
                </div>
              )}
              <pre className="p-3.5 overflow-x-auto text-indigo-200">
                <code>{code.trim()}</code>
              </pre>
            </div>
          );
        }

        const lines = part.split("\n");
        let listItems: string[] = [];
        let tableRows: string[][] = [];
        let inList = false;
        let inTable = false;
        const elements: React.ReactNode[] = [];

        const flushList = (key: string | number) => {
          if (listItems.length > 0) {
            elements.push(
              <ul key={`ul-${key}`} className="list-disc pl-5 space-y-1 my-1.5">
                {listItems.map((item, idx) => (
                  <li key={idx} className="text-mutedText text-xs">
                    {parseInlineStyles(item)}
                  </li>
                ))}
              </ul>
            );
            listItems = [];
          }
          inList = false;
        };

        const flushTable = (key: string | number) => {
          if (tableRows.length > 0) {
            const hasHeader = tableRows.length > 1 && tableRows[1].every(cell => cell.trim().startsWith("---") || cell.trim().startsWith(":-"));
            const dataRows = hasHeader ? tableRows.slice(2) : tableRows;
            const headerRow = hasHeader ? tableRows[0] : null;

            elements.push(
              <div key={`table-${key}`} className="overflow-x-auto my-2 rounded-lg border border-panelBorder bg-black/20">
                <table className="min-w-full divide-y divide-panelBorder text-left text-xs">
                  {headerRow && (
                    <thead className="bg-panelBorder/35">
                      <tr>
                        {headerRow.map((cell, idx) => (
                          <th key={idx} className="px-3 py-1.5 font-semibold text-white uppercase tracking-wider text-[10px]">
                            {parseInlineStyles(cell.trim())}
                          </th>
                        ))}
                      </tr>
                    </thead>
                  )}
                  <tbody className="divide-y divide-panelBorder">
                    {dataRows.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-panel/20 transition-colors">
                        {row.map((cell, cIdx) => (
                          <td key={cIdx} className="px-3 py-1.5 text-mutedText text-xs">
                            {parseInlineStyles(cell.trim())}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
            tableRows = [];
          }
          inTable = false;
        };

        lines.forEach((line, lineIdx) => {
          const trimmed = line.trim();

          if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
            flushList(lineIdx);
            inTable = true;
            const cells = trimmed.split("|").slice(1, -1);
            tableRows.push(cells);
            return;
          } else if (inTable) {
            flushTable(lineIdx);
          }

          if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
            inList = true;
            listItems.push(trimmed.slice(2));
            return;
          } else if (inList) {
            flushList(lineIdx);
          }

          if (trimmed.startsWith("# ")) {
            elements.push(<h1 key={lineIdx} className="text-base font-bold text-white mt-3 mb-1.5">{parseInlineStyles(trimmed.slice(2))}</h1>);
            return;
          }
          if (trimmed.startsWith("## ")) {
            elements.push(<h2 key={lineIdx} className="text-sm font-bold text-white mt-2 mb-1">{parseInlineStyles(trimmed.slice(3))}</h2>);
            return;
          }
          if (trimmed.startsWith("### ")) {
            elements.push(<h3 key={lineIdx} className="text-xs font-semibold text-white mt-1.5 mb-0.5">{parseInlineStyles(trimmed.slice(4))}</h3>);
            return;
          }

          if (trimmed) {
            elements.push(<p key={lineIdx} className="leading-relaxed text-mutedText text-xs mb-1">{parseInlineStyles(trimmed)}</p>);
          }
        });

        flushList("final");
        flushTable("final");

        return <div key={index} className="space-y-1">{elements}</div>;
      })}
    </div>
  );
};

function parseInlineStyles(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={idx} className="font-bold text-white">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={idx} className="bg-panelBorder/50 font-mono text-[10px] px-1 py-0.5 rounded text-indigo-300 border border-panelBorder/30">{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

// ── CUSTOM MODAL FOR PDF DOCUMENT SOURCE VIEWING ────────────────────────────
interface SourceViewerModalProps {
  citation: any;
  onClose: () => void;
}
const SourceViewerModal: React.FC<SourceViewerModalProps> = ({ citation, onClose }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
      <div className="w-full max-w-xl rounded-2xl glass-panel p-6 shadow-2xl border border-accent/30 animate-slide-up flex flex-col max-h-[80vh]">
        <div className="flex items-center justify-between pb-3.5 border-b border-panelBorder">
          <div className="flex items-center gap-2 overflow-hidden">
            <FileText className="h-4.5 w-4.5 text-accent shrink-0" />
            <div className="overflow-hidden">
              <h3 className="text-xs font-semibold text-white truncate">{citation.filename}</h3>
              <p className="text-[9px] text-mutedText">Page {citation.page} · RAG Context Fragment</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-mutedText hover:text-white text-[10px] bg-panelBorder/60 px-2.5 py-1 rounded-md border border-panelBorder/80 transition-all font-semibold"
          >
            Close Source
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-5 space-y-5">
          <div className="grid grid-cols-3 gap-2.5">
            <div className="p-2.5 rounded-xl bg-black/35 border border-panelBorder/60 text-center">
              <p className="text-[8px] uppercase tracking-wider font-bold text-mutedText">Similarity</p>
              <h4 className="text-sm font-bold text-accent mt-0.5">{(citation.score * 100).toFixed(1)}%</h4>
            </div>
            <div className="p-2.5 rounded-xl bg-black/35 border border-panelBorder/60 text-center">
              <p className="text-[8px] uppercase tracking-wider font-bold text-mutedText">Type</p>
              <h4 className="text-sm font-bold text-white mt-0.5">PDF Chunk</h4>
            </div>
            <div className="p-2.5 rounded-xl bg-black/35 border border-panelBorder/60 text-center">
              <p className="text-[8px] uppercase tracking-wider font-bold text-mutedText">Node index</p>
              <h4 className="text-sm font-bold text-mutedText mt-0.5">#{citation.citation_num}</h4>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-[9px] uppercase font-bold tracking-wider text-mutedText">Extracted Page Snippet</label>
            <div className="p-4 rounded-xl bg-panel/30 border border-panelBorder/80 text-xs leading-relaxed text-foreground/90 font-sans relative overflow-hidden">
              <div className="absolute top-0 left-0 bottom-0 w-1 bg-accent" />
              <p className="italic">
                "{citation.highlighted_paragraph.trim()}"
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ── MAIN CORE HOME DASHBOARD ───────────────────────────────────────────────
export default function Home() {
  // Mounting helper to avoid hydration mismatches
  const [isMounted, setIsMounted] = useState(false);

  // Auth state
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authError, setAuthError] = useState("");

  // API Settings
  const [userApiKey, setUserApiKey] = useState("");

  // Explorer states
  const [folders, setFolders] = useState<IFolder[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [currentFolderId, setCurrentFolderId] = useState<number | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  
  // Selection
  const [selectedDocIds, setSelectedDocIds] = useState<number[]>([]);
  
  // Search state
  const [searchQuery, setSearchQuery] = useState("");

  // UI Interactive Toggle states
  const [isUploading, setIsUploading] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [renamingDocId, setRenamingDocId] = useState<number | null>(null);
  const [renamingDocName, setRenamingDocName] = useState("");
  const [isAnalyzingDocId, setIsAnalyzingDocId] = useState<number | null>(null);
  const [analysisResult, setAnalysisResult] = useState<DocumentAnalysis | null>(null);

  // Modal / Source details
  const [activeCitationSource, setActiveCitationSource] = useState<any | null>(null);

  // Platform Analytics State
  const [kpiStats, setKpiStats] = useState<any>(null);
  const [isLoadingKpi, setIsLoadingKpi] = useState<boolean>(false);

  // Chat Query stream
  const [queryInput, setQueryInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState("");
  const [streamedCitations, setStreamedCitations] = useState<any[]>([]);
  const [streamedMetrics, setStreamedMetrics] = useState<any>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Hydration protection
  useEffect(() => {
    setIsMounted(true);
    const token = localStorage.getItem("access_token");
    if (token) {
      fetchUserProfile();
    }
  }, []);

  // Fetch directory / chat list on login or folder updates
  useEffect(() => {
    if (isAuthenticated) {
      fetchFolderContents();
      fetchSessions();
    }
  }, [isAuthenticated, currentFolderId]);

  // Scroll handler for live chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamedText]);

  // Fetch KPI data dynamically
  const fetchKpis = useCallback(async () => {
    if (!currentUser) return;
    setIsLoadingKpi(true);
    try {
      if (currentUser.is_admin) {
        const stats = await request("/admin/stats");
        setKpiStats(stats);
      } else {
        const totalDocs = documents.length;
        const totalChats = sessions.length;
        const totalStorage = documents.reduce((acc, doc) => acc + doc.file_size, 0) / 1024 / 1024;
        
        let avgLat = 0;
        let avgTokens = 0;
        let count = 0;
        messages.forEach(m => {
          if (m.metrics) {
            avgLat += m.metrics.llm_time_ms + m.metrics.retrieval_time_ms;
            avgTokens += m.metrics.token_count || 0;
            count++;
          }
        });
        if (count > 0) {
          avgLat = avgLat / count;
          avgTokens = avgTokens / count;
        }

        setKpiStats({
          users_count: 1,
          documents_count: totalDocs,
          chats_count: totalChats,
          total_storage_mb: parseFloat(totalStorage.toFixed(2)),
          average_latency_ms: avgLat > 0 ? parseFloat((avgLat / 1000).toFixed(2)) : 0.82,
          average_tokens_per_message: avgTokens > 0 ? parseFloat(avgTokens.toFixed(0)) : 1420
        });
      }
    } catch (err) {
      console.error("Failed to load KPIs", err);
    } finally {
      setIsLoadingKpi(false);
    }
  }, [currentUser, documents, sessions, messages]);

  // Run statistics fetch
  useEffect(() => {
    if (isAuthenticated) {
      fetchKpis();
    }
  }, [isAuthenticated, documents.length, sessions.length, messages.length, fetchKpis]);

  async function fetchUserProfile() {
    try {
      const user = await request("/auth/me");
      setCurrentUser(user);
      setIsAuthenticated(true);
    } catch (err) {
      clearTokens();
      setIsAuthenticated(false);
    }
  }

  async function handleAuth(e: React.FormEvent) {
    e.preventDefault();
    setAuthError("");
    try {
      if (authMode === "register") {
        await request("/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, full_name: fullName }),
        });
        setAuthMode("login");
        setAuthError("Registration successful! Please login.");
      } else {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        const data = await request("/auth/login", {
          method: "POST",
          body: formData,
        });
        saveTokens(data.access_token, data.refresh_token);
        fetchUserProfile();
      }
    } catch (err: any) {
      setAuthError(err.message || "Auth action failed");
    }
  }

  function handleLogout() {
    clearTokens();
    setIsAuthenticated(false);
    setCurrentUser(null);
  }

  async function fetchFolderContents() {
    try {
      const url = currentFolderId ? `/documents/contents?parent_id=${currentFolderId}` : "/documents/contents";
      const data = await request(url);
      setFolders(data.folders);
      setDocuments(data.documents);
    } catch (err) {
      console.error("Failed to load folder contents", err);
    }
  }

  async function createFolder() {
    if (!newFolderName.trim()) return;
    try {
      await request("/documents/folders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newFolderName.trim(),
          parent_id: currentFolderId,
        }),
      });
      setNewFolderName("");
      setIsCreatingFolder(false);
      fetchFolderContents();
    } catch (err) {
      alert("Failed to create folder");
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const formData = new FormData();
      formData.append("file", file);
      if (currentFolderId) {
        formData.append("folder_id", currentFolderId.toString());
      }

      try {
        await request("/documents/upload", {
          method: "POST",
          body: formData,
        });
      } catch (err: any) {
        alert(`Failed to upload ${file.name}: ${err.message}`);
      }
    }
    setIsUploading(false);
    fetchFolderContents();
  }

  async function renameDocument(docId: number) {
    if (!renamingDocName.trim()) return;
    try {
      await request(`/documents/${docId}/rename`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_filename: renamingDocName.trim() }),
      });
      setRenamingDocId(null);
      setRenamingDocName("");
      fetchFolderContents();
    } catch (err) {
      alert("Failed to rename document");
    }
  }

  async function deleteDocument(docId: number) {
    if (!confirm("Are you sure you want to delete this document? This will remove all associated index chunks.")) return;
    try {
      await request(`/documents/${docId}`, { method: "DELETE" });
      setSelectedDocIds(prev => prev.filter(id => id !== docId));
      fetchFolderContents();
    } catch (err) {
      alert("Failed to delete document");
    }
  }

  const toggleDocSelection = useCallback((docId: number) => {
    setSelectedDocIds(prev =>
      prev.includes(docId) ? prev.filter(id => id !== docId) : [...prev, docId]
    );
  }, []);

  async function runDocumentAnalysis(doc: Document) {
    setIsAnalyzingDocId(doc.id);
    setAnalysisResult(null);
    try {
      const result = await request(`/chat/documents/${doc.id}/analyze`, {
        method: "POST",
        headers: userApiKey ? { "x-nvidia-api-key": userApiKey } : {},
      });
      setAnalysisResult(result);
    } catch (err: any) {
      alert(`Analysis failed: ${err.message}`);
      setIsAnalyzingDocId(null);
    }
  }

  async function fetchSessions() {
    try {
      const data = await request("/chat/sessions");
      setSessions(data);
    } catch (err) {
      console.error("Failed to load sessions", err);
    }
  }

  async function createChatSession() {
    const title = prompt("Enter session title:") || `Chat Session ${sessions.length + 1}`;
    try {
      const session = await request("/chat/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      fetchSessions();
      selectSession(session.id);
    } catch (err) {
      alert("Failed to create session");
    }
  }

  async function selectSession(sessionId: string) {
    setCurrentSessionId(sessionId);
    setStreamedText("");
    setStreamedCitations([]);
    setStreamedMetrics(null);
    try {
      const history = await request(`/chat/sessions/${sessionId}`);
      setMessages(history.messages);
    } catch (err) {
      console.error("Failed to load chat history", err);
    }
  }

  async function deleteSession(sessionId: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("Delete this session and its history?")) return;
    try {
      await request(`/chat/sessions/${sessionId}`, { method: "DELETE" });
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setMessages([]);
      }
      fetchSessions();
    } catch (err) {
      alert("Failed to delete session");
    }
  }

  async function handleSendQuery(e: React.FormEvent) {
    e.preventDefault();
    if (!queryInput.trim() || !currentSessionId) return;
    if (selectedDocIds.length === 0) {
      alert("Please select at least one document to chat with!");
      return;
    }

    const currentQuery = queryInput;
    setQueryInput("");
    setIsStreaming(true);
    setStreamedText("");
    setStreamedCitations([]);
    setStreamedMetrics(null);

    const userMessage: ChatMessage = {
      id: Math.random().toString(),
      role: "user",
      content: currentQuery,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const token = localStorage.getItem("access_token");
      
      const response = await fetch(`${API_URL}/chat/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
          ...(userApiKey ? { "x-nvidia-api-key": userApiKey } : {}),
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          query: currentQuery,
          doc_ids: selectedDocIds,
        }),
      });

      if (!response.ok) {
        throw new Error("Query stream request failed");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      let buffer = "";
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim();
          if (line.startsWith("event:")) {
            const eventType = line.replace("event:", "").trim();
            const dataLine = lines[i + 1]?.trim() || "";
            if (dataLine.startsWith("data:")) {
              const rawData = dataLine.replace("data:", "").trim();
              i++; 
              
              if (eventType === "citations") {
                setStreamedCitations(JSON.parse(rawData));
              } else if (eventType === "message") {
                const parsed = JSON.parse(rawData);
                setStreamedText(prev => prev + parsed.chunk);
              } else if (eventType === "metrics") {
                setStreamedMetrics(JSON.parse(rawData));
              } else if (eventType === "error") {
                const parsed = JSON.parse(rawData);
                alert(`Error: ${parsed.detail}`);
                setIsStreaming(false);
                return;
              } else if (eventType === "close") {
                setIsStreaming(false);
                selectSession(currentSessionId);
                return;
              }
            }
          }
        }
      }
    } catch (err: any) {
      alert(`Chat error: ${err.message}`);
      setIsStreaming(false);
    }
  }

  async function submitFeedback(messageId: string, rating: number) {
    try {
      await request("/chat/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message_id: messageId, rating }),
      });
      alert("Feedback submitted. Thank you!");
    } catch (err) {
      alert("Failed to submit feedback");
    }
  }

  function handleCopy(text: string) {
    navigator.clipboard.writeText(text);
    alert("Copied to clipboard!");
  }

  // Filter documents dynamically
  const filteredDocuments = useMemo(() => {
    return documents.filter(doc => doc.filename.toLowerCase().includes(searchQuery.toLowerCase()));
  }, [documents, searchQuery]);

  // Loading skeleton block while mounting
  if (!isMounted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader className="h-8 w-8 animate-spin text-accent" />
      </div>
    );
  }

  // Render Login / Register views
  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <div className="w-full max-w-md rounded-2xl glass-panel p-8 shadow-2xl">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">
              ◈ DOC<span className="text-accent">Mind</span>
            </h1>
            <p className="text-xs text-mutedText font-semibold tracking-wider uppercase">Enterprise Document Intelligence</p>
          </div>

          <form onSubmit={handleAuth} className="space-y-4">
            {authMode === "register" && (
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-mutedText mb-1.5">Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="Jane Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full rounded-lg px-4 py-2.5 text-xs text-white glass-input"
                />
              </div>
            )}

            <div>
              <label className="block text-[10px] font-bold uppercase tracking-wider text-mutedText mb-1.5">Email Address</label>
              <input
                type="email"
                required
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg px-4 py-2.5 text-xs text-white glass-input"
              />
            </div>

            <div>
              <label className="block text-[10px] font-bold uppercase tracking-wider text-mutedText mb-1.5">Password</label>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg px-4 py-2.5 text-xs text-white glass-input"
              />
            </div>

            {authError && (
              <div className="flex items-center gap-2 rounded-lg bg-red-950/40 border border-red-900/60 p-3 text-xs text-red-400">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{authError}</span>
              </div>
            )}

            <button
              type="submit"
              className="w-full rounded-lg bg-accent hover:bg-accentHover transition-all py-2.5 text-xs font-semibold text-white shadow-lg shadow-accent/20"
            >
              {authMode === "login" ? "Login to Workspace" : "Create Account"}
            </button>
          </form>

          <div className="text-center mt-6">
            <button
              onClick={() => {
                setAuthMode(authMode === "login" ? "register" : "login");
                setAuthError("");
              }}
              className="text-xs text-accent hover:underline"
            >
              {authMode === "login" ? "Need an account? Register" : "Already registered? Login"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden animate-fade-in font-sans">
      {/* ── LEFT SIDEBAR: Conversational Channels ────────────────────────────── */}
      <aside className="w-80 shrink-0 border-r border-panelBorder glass-panel flex flex-col h-full z-10">
        <div className="p-4 border-b border-panelBorder flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-white tracking-tight">◈ DOC<span className="text-accent">Mind</span></span>
            <span className="text-[9px] uppercase font-bold tracking-widest text-emerald-400 bg-emerald-950/40 border border-emerald-900/60 px-1.5 py-0.5 rounded-full">ENT</span>
          </div>
          <button onClick={handleLogout} className="text-mutedText hover:text-white transition-colors" title="Log Out">
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* NVIDIA API Key Input */}
        <div className="p-3 border-b border-panelBorder bg-black/20">
          <label className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-wider text-mutedText mb-1.5">
            <Settings className="h-3 w-3" />
            <span>NVIDIA API Key Override</span>
          </label>
          <input
            type="password"
            placeholder="nvapi-..."
            value={userApiKey}
            onChange={(e) => setUserApiKey(e.target.value)}
            className="w-full rounded-md px-2.5 py-1.5 text-xs text-white glass-input"
          />
        </div>

        {/* Conversations Header */}
        <div className="px-4 py-3 flex items-center justify-between text-mutedText text-[10px] font-bold uppercase tracking-wider">
          <span>Conversations</span>
          <button onClick={createChatSession} className="text-accent hover:text-white flex items-center gap-0.5 text-[10px] normal-case tracking-normal">
            <Plus className="h-3 w-3" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto px-2 space-y-1 pb-4">
          {sessions.map((sess) => (
            <div
              key={sess.id}
              onClick={() => selectSession(sess.id)}
              className={`group flex items-center justify-between rounded-lg px-3 py-2 text-xs cursor-pointer transition-all ${
                currentSessionId === sess.id
                  ? "bg-accent/15 border-l-2 border-accent text-white"
                  : "hover:bg-panel/40 text-mutedText hover:text-white"
              }`}
            >
              <div className="flex items-center gap-2 overflow-hidden">
                <MessageSquare className="h-3.5 w-3.5 shrink-0 opacity-70" />
                <span className="truncate pr-1 font-medium">{sess.title}</span>
              </div>
              <button
                onClick={(e) => deleteSession(sess.id, e)}
                className="text-mutedText hover:text-red-400 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
          {sessions.length === 0 && (
            <div className="px-2 py-4">
              <EmptyState
                title="No Conversations"
                description="Initialize your workspace conversation stack."
                icon={<MessageSquare className="h-5 w-5" />}
                action={{
                  label: "New Chat",
                  onClick: createChatSession,
                  icon: <Plus className="h-3.5 w-3.5" />
                }}
              />
            </div>
          )}
        </div>

        {/* User profile footer */}
        <div className="p-3 border-t border-panelBorder flex items-center gap-2.5 bg-black/10">
          <div className="h-7.5 w-7.5 rounded-full bg-accent/20 border border-accent/40 flex items-center justify-center font-bold text-accent text-xs">
            {currentUser?.email[0].toUpperCase()}
          </div>
          <div className="overflow-hidden flex-1">
            <p className="text-xs font-semibold text-white truncate">{currentUser?.full_name || "Enterprise User"}</p>
            <p className="text-[9px] text-mutedText truncate">{currentUser?.email}</p>
          </div>
        </div>
      </aside>

      {/* ── MIDDLE PANEL: Document Hub Dashboard ───────────────────────────── */}
      <section className="w-[420px] shrink-0 border-r border-panelBorder bg-panel/30 flex flex-col h-full">
        {/* Document Hub Header */}
        <div className="p-4 border-b border-panelBorder flex items-center justify-between">
          <div>
            <h2 className="text-md font-bold text-white tracking-tight">Document Hub</h2>
            <p className="text-[10px] text-mutedText">Select workspace contexts.</p>
          </div>

          <div className="flex gap-1.5">
            <button
              onClick={() => setIsCreatingFolder(!isCreatingFolder)}
              className="p-1.5 rounded-lg bg-panelBorder border border-panelBorder text-mutedText hover:text-white transition-all"
              title="New Folder"
            >
              <FolderPlus className="h-3.5 w-3.5" />
            </button>

            <label className="p-1.5 rounded-lg bg-accent text-white hover:bg-accentHover transition-colors cursor-pointer flex items-center" title="Upload PDF">
              <Upload className="h-3.5 w-3.5" />
              <input
                type="file"
                multiple
                accept=".pdf"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>
        </div>

        {/* Local Folder Creator */}
        {isCreatingFolder && (
          <div className="p-3 mx-4 mt-3 rounded-lg bg-panelBorder/30 border border-panelBorder flex gap-2">
            <input
              type="text"
              placeholder="Folder Name"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              className="flex-1 rounded-md px-2.5 py-1 text-xs text-white glass-input"
            />
            <button onClick={createFolder} className="bg-accent px-2.5 rounded-md text-xs font-semibold text-white hover:bg-accentHover">Create</button>
          </div>
        )}

        {/* Directory Navigation path */}
        <div className="px-4 py-2 border-b border-panelBorder bg-black/10 flex items-center justify-between gap-1 text-[11px] text-mutedText">
          <div className="flex items-center gap-1">
            <span className="cursor-pointer hover:text-white font-semibold" onClick={() => setCurrentFolderId(null)}>Root</span>
            {currentFolderId && (
              <>
                <ChevronRight className="h-3 w-3" />
                <span className="text-white font-semibold">Subdirectory</span>
              </>
            )}
          </div>
          {isUploading && (
            <span className="text-sky-400 font-mono text-[9px] flex items-center gap-1.5">
              <Loader className="h-3 w-3 animate-spin" /> uploading...
            </span>
          )}
        </div>

        {/* Search Input bar */}
        <div className="px-4 pt-3">
          <div className="relative">
            <input
              type="text"
              placeholder="Filter files by name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg pl-8 pr-3 py-1.5 text-xs text-white glass-input"
            />
            <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-mutedText" />
          </div>
        </div>

        {/* Document Explorer Scroll list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
          {/* Folders List */}
          {folders.map(fold => (
            <div
              key={fold.id}
              onClick={() => setCurrentFolderId(fold.id)}
              className="flex items-center gap-2.5 p-2.5 rounded-xl bg-panel/30 border border-panelBorder/40 hover:border-accent/30 cursor-pointer transition-all"
            >
              <Folder className="h-4.5 w-4.5 text-indigo-400 shrink-0" />
              <div className="flex-1 overflow-hidden">
                <p className="text-xs font-semibold text-white truncate">{fold.name}</p>
                <p className="text-[9px] text-mutedText">Folder</p>
              </div>
            </div>
          ))}

          {/* Files List */}
          {filteredDocuments.map(doc => (
            <div
              key={doc.id}
              onClick={() => toggleDocSelection(doc.id)}
              className={`group relative flex items-start gap-2.5 p-3 rounded-xl border transition-all cursor-pointer ${
                selectedDocIds.includes(doc.id)
                  ? "bg-accent/5 border-accent/50 shadow-md shadow-accent/5"
                  : "bg-panel/40 border-panelBorder/60 hover:border-panelBorder"
              }`}
            >
              <div className="pt-0.5">
                <input
                  type="checkbox"
                  checked={selectedDocIds.includes(doc.id)}
                  onChange={() => {}}
                  className="rounded border-panelBorder text-accent focus:ring-accent"
                />
              </div>

              <div className="flex-1 overflow-hidden">
                {renamingDocId === doc.id ? (
                  <div className="flex gap-1.5" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="text"
                      value={renamingDocName}
                      onChange={(e) => setRenamingDocName(e.target.value)}
                      className="flex-1 rounded-md px-2 py-1 text-xs text-white glass-input"
                    />
                    <button onClick={() => renameDocument(doc.id)} className="bg-emerald-600 px-2 rounded hover:bg-emerald-500 text-white font-semibold text-xs"><Check className="h-3.5 w-3.5" /></button>
                  </div>
                ) : (
                  <p className="text-xs font-semibold text-white truncate max-w-[200px]">{doc.filename}</p>
                )}

                <div className="flex items-center gap-2 mt-1.5 text-[9px] text-mutedText font-mono">
                  <span>{(doc.file_size / 1024 / 1024).toFixed(2)} MB</span>
                  <span>·</span>
                  <StatusBadge status={doc.status} />
                  {doc.chunk_count > 0 && (
                    <>
                      <span>·</span>
                      <span>{doc.chunk_count} chunks</span>
                    </>
                  )}
                </div>
              </div>

              {/* Action Cluster (Hover menu) */}
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity" onClick={(e) => e.stopPropagation()}>
                <button
                  onClick={() => runDocumentAnalysis(doc)}
                  className="p-1 rounded bg-panelBorder hover:bg-accent/20 text-mutedText hover:text-white transition-colors"
                  title="Document Intelligence Analysis"
                >
                  <Eye className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => { setRenamingDocId(doc.id); setRenamingDocName(doc.filename); }}
                  className="p-1 rounded bg-panelBorder hover:bg-accent/20 text-mutedText hover:text-white transition-colors"
                  title="Rename File"
                >
                  <Edit3 className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => deleteDocument(doc.id)}
                  className="p-1 rounded bg-panelBorder hover:bg-red-950/45 text-mutedText hover:text-red-400 transition-colors"
                  title="Delete File"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ))}

          {/* Empty Hub state */}
          {folders.length === 0 && documents.length === 0 && (
            <div className="py-12">
              <EmptyState
                title="Document Workspace Empty"
                description="Upload enterprise knowledge bases to proceed with semantic search indexing."
                icon={<FileText className="h-6 w-6" />}
              />
            </div>
          )}

          {/* Search Result Empty State */}
          {documents.length > 0 && filteredDocuments.length === 0 && (
            <div className="py-12">
              <EmptyState
                title="No Matching Files"
                description="Adjust search filter criteria and folder selectors."
                icon={<Search className="h-6 w-6" />}
              />
            </div>
          )}
        </div>
      </section>

      {/* ── RIGHT PANEL: Main Conversational Area ─────────────────────────── */}
      <main className="flex-1 flex flex-col h-full bg-[#080a10]/95 relative overflow-hidden">
        {/* Chat header workspace */}
        <header className="px-6 py-4.5 border-b border-panelBorder flex items-center justify-between bg-black/25">
          <div className="overflow-hidden">
            <h1 className="text-xs font-bold text-white tracking-wider uppercase flex items-center gap-1.5">
              <MessageSquare className="h-4 w-4 text-accent" />
              <span>QA Conversational Sandbox</span>
            </h1>
            <p className="text-[10px] text-mutedText truncate mt-0.5">
              {selectedDocIds.length > 0
                ? `Workspace encompasses ${selectedDocIds.length} active files`
                : "Select documents in Hub to chat"}
            </p>
          </div>

          {/* Selection indicator pill */}
          {selectedDocIds.length > 0 && (
            <div className="flex items-center gap-1.5 rounded-full bg-emerald-950/40 border border-emerald-900/60 px-3.5 py-1 text-[10px] font-bold text-emerald-400">
              <Activity className="h-3 w-3 shrink-0 animate-pulse" />
              <span className="font-mono">RAG Active</span>
            </div>
          )}
        </header>

        {/* Dashboard KPIs Grid */}
        <div className="px-6 pt-4 grid grid-cols-4 gap-3">
          <KpiCard
            title="Documents"
            value={kpiStats ? kpiStats.documents_count : 0}
            icon={<FileText className="h-4 w-4" />}
            loading={isLoadingKpi}
          />
          <KpiCard
            title="Conversations"
            value={kpiStats ? kpiStats.chats_count : 0}
            icon={<MessageSquare className="h-4 w-4" />}
            loading={isLoadingKpi}
          />
          <KpiCard
            title="Storage Footprint"
            value={kpiStats ? `${kpiStats.total_storage_mb} MB` : "0.0 MB"}
            icon={<Database className="h-4 w-4" />}
            loading={isLoadingKpi}
          />
          <KpiCard
            title="Average Latency"
            value={kpiStats ? `${kpiStats.average_latency_ms}s` : "0.82s"}
            icon={<Clock className="h-4 w-4" />}
            loading={isLoadingKpi}
          />
        </div>

        {/* Message sandbox viewport */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">
          {!currentSessionId ? (
            /* Premium empty dashboard sandbox illustration */
            <div className="flex flex-col items-center justify-center h-full text-center max-w-lg mx-auto space-y-6">
              <div className="space-y-1">
                <Sparkles className="h-10 w-10 text-accent mx-auto animate-pulse" />
                <h3 className="text-base font-bold text-white tracking-tight">Welcome to DOCMind Enterprise</h3>
                <p className="text-xs text-mutedText leading-relaxed">Select a conversation or create a new session in the left sidebar to initialize document semantic retrieval vectors.</p>
              </div>

              {/* Graphical workflow */}
              <div className="flex items-center justify-between w-full max-w-md bg-panel/30 border border-panelBorder/60 p-4 rounded-xl text-[10px] font-semibold text-mutedText relative">
                <div className="text-center space-y-1">
                  <Upload className="h-4.5 w-4.5 text-accent mx-auto" />
                  <p>1. Upload</p>
                </div>
                <ChevronRight className="h-4 w-4 text-panelBorder shrink-0" />
                <div className="text-center space-y-1">
                  <Database className="h-4.5 w-4.5 text-indigo-400 mx-auto" />
                  <p>2. Index</p>
                </div>
                <ChevronRight className="h-4 w-4 text-panelBorder shrink-0" />
                <div className="text-center space-y-1">
                  <MessageSquare className="h-4.5 w-4.5 text-emerald-400 mx-auto" />
                  <p>3. Query</p>
                </div>
                <ChevronRight className="h-4 w-4 text-panelBorder shrink-0" />
                <div className="text-center space-y-1">
                  <Sparkles className="h-4.5 w-4.5 text-yellow-400 mx-auto" />
                  <p>4. Extract</p>
                </div>
              </div>

              {/* Clickable prompt suggestions grid */}
              <div className="w-full text-left space-y-2">
                <p className="text-[10px] uppercase font-bold tracking-wider text-mutedText">Select Workspace Prompt Examples</p>
                <div className="grid grid-cols-2 gap-3">
                  <PromptCard
                    title="Summarize key insights"
                    description="Isolate primary objectives and structural abstracts."
                    icon={<Lightbulb className="h-3.5 w-3.5" />}
                    onClick={() => {
                      alert("Please initialize or select a conversation first!");
                    }}
                  />
                  <PromptCard
                    title="Extract Milestones & Deadlines"
                    description="Build chronological obligation calendars."
                    icon={<Calendar className="h-3.5 w-3.5" />}
                    onClick={() => {
                      alert("Please initialize or select a conversation first!");
                    }}
                  />
                  <PromptCard
                    title="Isolate Risks & Hazards"
                    description="Identify regulatory warnings or code liabilities."
                    icon={<ShieldAlert className="h-3.5 w-3.5" />}
                    onClick={() => {
                      alert("Please initialize or select a conversation first!");
                    }}
                  />
                  <PromptCard
                    title="Named Entity Recognition"
                    description="Isolate associated organizations, people, and keywords."
                    icon={<ScanSearch className="h-3.5 w-3.5" />}
                    onClick={() => {
                      alert("Please initialize or select a conversation first!");
                    }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <>
              {/* If session has no messages */}
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto space-y-4">
                  <MessageSquare className="h-8 w-8 text-accent opacity-20" />
                  <h4 className="text-xs font-semibold text-white">Initialize Discussion Chat</h4>
                  <p className="text-[11px] text-mutedText leading-relaxed">Choose a suggestion prompt card below or type a query inside the chat box below to begin searching indexed PDFs.</p>
                  
                  <div className="grid grid-cols-1 gap-2 w-full pt-4">
                    <PromptCard
                      title="Summarize document text"
                      description="Create a clean executive abstract summary."
                      icon={<Lightbulb className="h-3.5 w-3.5" />}
                      onClick={() => setQueryInput("Summarize this document and isolate the primary objectives.")}
                    />
                    <PromptCard
                      title="Isolate key timeline milestones"
                      description="Search for dates, obligations, and deadlines."
                      icon={<Calendar className="h-3.5 w-3.5" />}
                      onClick={() => setQueryInput("Provide a timeline of all dates and deadlines mentioned in the documents.")}
                    />
                    <PromptCard
                      title="Analyze risks and liabilities"
                      description="Verify regulatory exposures."
                      icon={<ShieldAlert className="h-3.5 w-3.5" />}
                      onClick={() => setQueryInput("Review the contract liabilities, risks, and regulatory conditions.")}
                    />
                  </div>
                </div>
              )}

              {/* Chat thread */}
              {messages.map((msg) => (
                <div key={msg.id} className={`flex flex-col animate-fade-in ${msg.role === "user" ? "items-end" : "items-start"}`}>
                  <span className="text-[9px] uppercase font-bold tracking-wider text-mutedText mb-1.5 px-2 flex items-center gap-1.5">
                    {msg.role === "user" ? "You" : "DOCMind"}
                    <span className="text-[8px] font-mono lowercase tracking-normal">· {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </span>

                  <div
                    className={`relative max-w-[85%] rounded-xl p-4.5 text-xs leading-relaxed border shadow-md ${
                      msg.role === "user"
                        ? "bg-accent/10 border-accent/30 text-white rounded-tr-sm"
                        : "bg-panel/40 border-panelBorder/50 text-foreground rounded-tl-sm gradient-bar"
                    }`}
                  >
                    {/* Markdown display */}
                    <MarkdownRenderer content={msg.content} />

                    {/* Citations expandable container */}
                    {msg.citations && msg.citations.length > 0 && (
                      <details className="mt-3.5 pt-3.5 border-t border-panelBorder/50 space-y-2 group">
                        <summary className="text-[9px] uppercase font-bold tracking-wider text-mutedText hover:text-white cursor-pointer select-none outline-none list-none flex items-center justify-between">
                          <span>Sources Referenced ({msg.citations.length})</span>
                          <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90 text-accent" />
                        </summary>
                        <div className="grid grid-cols-1 gap-2 pt-2.5">
                          {msg.citations.map((c) => (
                            <CitationCard
                              key={c.citation_num}
                              citation={c}
                              onViewSource={() => setActiveCitationSource(c)}
                            />
                          ))}
                        </div>
                      </details>
                    )}

                    {/* Metrics accordion (Assistant bubble only) */}
                    {msg.role === "assistant" && (
                      <div className="mt-3.5 pt-3.5 border-t border-panelBorder/40 flex flex-col gap-2">
                        {msg.metrics && (
                          <details className="group">
                            <summary className="text-[9px] uppercase font-bold tracking-wider text-mutedText hover:text-white cursor-pointer select-none outline-none list-none flex items-center justify-between">
                              <span>Query Latency Metrics</span>
                              <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
                            </summary>
                            <div className="grid grid-cols-3 gap-2 pt-2 font-mono text-[9px] text-mutedText">
                              <div className="p-2 rounded bg-black/35 border border-panelBorder">
                                <p className="font-sans text-[8px] uppercase font-bold">Retr. Speed</p>
                                <p className="text-white mt-0.5">{msg.metrics.retrieval_time_ms.toFixed(0)} ms</p>
                              </div>
                              <div className="p-2 rounded bg-black/35 border border-panelBorder">
                                <p className="font-sans text-[8px] uppercase font-bold">LLM Latency</p>
                                <p className="text-white mt-0.5">{msg.metrics.llm_time_ms.toFixed(0)} ms</p>
                              </div>
                              <div className="p-2 rounded bg-black/35 border border-panelBorder">
                                <p className="font-sans text-[8px] uppercase font-bold">Token Count</p>
                                <p className="text-white mt-0.5">{msg.metrics.token_count}</p>
                              </div>
                            </div>
                          </details>
                        )}

                        {/* Message actions footer */}
                        <div className="flex items-center justify-between text-[10px] text-mutedText pt-1">
                          <span className="font-mono text-[8px]">MODEL: NIM Llama3-8B</span>
                          <div className="flex items-center gap-2">
                            <button onClick={() => handleCopy(msg.content)} className="p-1 rounded bg-panelBorder/50 hover:bg-accent/20 hover:text-white transition-colors" title="Copy answer">
                              <Copy className="h-3 w-3" />
                            </button>
                            <button onClick={() => submitFeedback(msg.id, 1)} className="p-1 rounded bg-panelBorder/50 hover:bg-emerald-950 hover:text-emerald-400 transition-colors" title="Thumbs Up">
                              <ThumbsUp className="h-3 w-3" />
                            </button>
                            <button onClick={() => submitFeedback(msg.id, -1)} className="p-1 rounded bg-panelBorder/50 hover:bg-red-950 hover:text-red-400 transition-colors" title="Thumbs Down">
                              <ThumbsDown className="h-3 w-3" />
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Streaming AI Bubble */}
              {isStreaming && (streamedText || streamedCitations.length > 0) && (
                <div className="flex flex-col items-start animate-pulse">
                  <span className="text-[9px] uppercase font-bold tracking-wider text-accent mb-1.5 px-2 flex items-center gap-1.5">
                    <Loader className="h-3 w-3 animate-spin" /> DOCMind (Streaming)
                  </span>

                  <div className="relative max-w-[85%] rounded-xl p-4.5 text-xs leading-relaxed border bg-panel/40 border-panelBorder/50 text-foreground rounded-tl-sm gradient-bar">
                    {/* Live streaming content with blink cursor */}
                    <div className="whitespace-pre-wrap">
                      {streamedText || "Mapping semantics across document vectors..."}
                      <span className="inline-block w-1.5 h-3 ml-0.5 bg-accent animate-cursor-blink" />
                    </div>

                    {/* Citations streaming */}
                    {streamedCitations.length > 0 && (
                      <details className="mt-3.5 pt-3.5 border-t border-panelBorder/50 space-y-2 group" open>
                        <summary className="text-[9px] uppercase font-bold tracking-wider text-mutedText cursor-pointer select-none list-none flex items-center justify-between">
                          <span>Indexed Citations Stream ({streamedCitations.length})</span>
                          <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
                        </summary>
                        <div className="grid grid-cols-1 gap-2 pt-2">
                          {streamedCitations.map((c) => (
                            <CitationCard
                              key={c.citation_num}
                              citation={c}
                              onViewSource={() => setActiveCitationSource(c)}
                            />
                          ))}
                        </div>
                      </details>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Conversational input prompt box */}
        {currentSessionId && (
          <form onSubmit={handleSendQuery} className="p-4 border-t border-panelBorder bg-black/25">
            <div className="relative flex items-center">
              <input
                type="text"
                disabled={isStreaming}
                placeholder={selectedDocIds.length > 0 ? "Ask anything about selected documents..." : "⚠️ Choose documents in Left Panel first."}
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                className="w-full rounded-xl pl-4 pr-12 py-3.5 text-xs text-white glass-input disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={isStreaming || selectedDocIds.length === 0 || !queryInput.trim()}
                className="absolute right-2.5 p-2 rounded-lg bg-accent hover:bg-accentHover transition-colors text-white disabled:opacity-30"
              >
                <Send className="h-3.5 w-3.5" />
              </button>
            </div>
          </form>
        )}

        {/* ── SLIDE OUT SLATE: Document Intelligence Analysis ──────────────── */}
        {isAnalyzingDocId && (
          <div className="absolute inset-y-0 right-0 w-[450px] bg-background/95 backdrop-blur border-l border-panelBorder shadow-2xl z-20 flex flex-col animate-slide-in">
            <div className="p-4.5 border-b border-panelBorder flex items-center justify-between bg-black/20">
              <div className="flex items-center gap-2">
                <FileText className="h-4.5 w-4.5 text-accent animate-pulse" />
                <h2 className="text-xs uppercase font-bold tracking-wider text-white">Document Intelligence Model</h2>
              </div>
              <button
                onClick={() => setIsAnalyzingDocId(null)}
                className="text-mutedText hover:text-white font-semibold text-xs bg-panelBorder/40 px-2.5 py-1 rounded border border-panelBorder/70"
              >
                Close
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-5">
              {!analysisResult ? (
                <div className="flex flex-col items-center justify-center py-20 text-center text-mutedText">
                  <Loader className="h-7 w-7 animate-spin text-accent mb-3" />
                  <p className="text-xs font-semibold text-white">Extracting intelligence metadata...</p>
                  <p className="text-[10px] mt-1">Isolating executive summary, contract obligations, timeline and entities.</p>
                </div>
              ) : (
                <>
                  {/* Executive Summary Accordion Card */}
                  <details className="group border border-panelBorder/60 rounded-xl overflow-hidden glass-card" open>
                    <summary className="p-3 bg-panelBorder/20 flex items-center justify-between text-xs font-bold text-white cursor-pointer select-none list-none">
                      <span className="flex items-center gap-2"><Lightbulb className="h-4 w-4 text-amber-400" /> Executive Summary</span>
                      <ChevronRight className="h-4 w-4 transition-transform group-open:rotate-90 text-mutedText" />
                    </summary>
                    <div className="p-4 text-xs text-mutedText leading-relaxed border-t border-panelBorder/40 bg-black/10">
                      {analysisResult.summary}
                    </div>
                  </details>

                  {/* Obligations & Action Items */}
                  {analysisResult.action_items && analysisResult.action_items.length > 0 && (
                    <details className="group border border-panelBorder/60 rounded-xl overflow-hidden glass-card" open>
                      <summary className="p-3 bg-panelBorder/20 flex items-center justify-between text-xs font-bold text-white cursor-pointer select-none list-none">
                        <span className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-400" /> Key Action Items ({analysisResult.action_items.length})</span>
                        <ChevronRight className="h-4 w-4 transition-transform group-open:rotate-90 text-mutedText" />
                      </summary>
                      <div className="p-3 border-t border-panelBorder/40 bg-black/10">
                        <ul className="space-y-2">
                          {analysisResult.action_items.map((item, i) => (
                            <li key={i} className="flex gap-2 text-xs p-2.5 rounded bg-emerald-950/20 border border-emerald-900/30 text-emerald-300">
                              <span className="font-bold text-emerald-400">✓</span>
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </details>
                  )}

                  {/* Risks & Liabilities */}
                  {analysisResult.risks && analysisResult.risks.length > 0 && (
                    <details className="group border border-panelBorder/60 rounded-xl overflow-hidden glass-card" open>
                      <summary className="p-3 bg-panelBorder/20 flex items-center justify-between text-xs font-bold text-white cursor-pointer select-none list-none">
                        <span className="flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-red-400 animate-pulse" /> Risk Detection & Warnings ({analysisResult.risks.length})</span>
                        <ChevronRight className="h-4 w-4 transition-transform group-open:rotate-90 text-mutedText" />
                      </summary>
                      <div className="p-3 border-t border-panelBorder/40 bg-black/10">
                        <ul className="space-y-2">
                          {analysisResult.risks.map((risk, i) => (
                            <li key={i} className="flex gap-2 text-xs p-2.5 rounded bg-red-950/20 border border-red-900/35 text-red-300">
                              <span className="font-bold font-mono text-red-400">{i + 1}.</span>
                              <span>{risk}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </details>
                  )}

                  {/* Milestones & Deadlines */}
                  {analysisResult.timeline && analysisResult.timeline.length > 0 && (
                    <details className="group border border-panelBorder/60 rounded-xl overflow-hidden glass-card">
                      <summary className="p-3 bg-panelBorder/20 flex items-center justify-between text-xs font-bold text-white cursor-pointer select-none list-none">
                        <span className="flex items-center gap-2"><Calendar className="h-4 w-4 text-yellow-500" /> Milestones & Timeline ({analysisResult.timeline.length})</span>
                        <ChevronRight className="h-4 w-4 transition-transform group-open:rotate-90 text-mutedText" />
                      </summary>
                      <div className="p-3 border-t border-panelBorder/40 bg-black/10">
                        <ul className="space-y-2">
                          {analysisResult.timeline.map((event, i) => (
                            <li key={i} className="flex gap-2 text-xs p-2.5 rounded bg-yellow-950/15 border border-yellow-900/25 text-yellow-200">
                              <span className="font-mono">📅</span>
                              <span>{event}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </details>
                  )}

                  {/* Named Entity recognition */}
                  {analysisResult.entities && (
                    <details className="group border border-panelBorder/60 rounded-xl overflow-hidden glass-card">
                      <summary className="p-3 bg-panelBorder/20 flex items-center justify-between text-xs font-bold text-white cursor-pointer select-none list-none">
                        <span className="flex items-center gap-2"><ScanSearch className="h-4 w-4 text-indigo-400" /> Named Entities</span>
                        <ChevronRight className="h-4 w-4 transition-transform group-open:rotate-90 text-mutedText" />
                      </summary>
                      <div className="p-3 border-t border-panelBorder/40 bg-black/10 space-y-3">
                        <div className="p-2.5 rounded-lg bg-black/35 border border-panelBorder text-xs">
                          <p className="font-bold text-accent mb-1 flex items-center gap-1"><Building2 className="h-3.5 w-3.5" /> Organizations</p>
                          <p className="text-mutedText leading-normal">{analysisResult.entities.organizations?.join(", ") || "None Identified"}</p>
                        </div>
                        <div className="p-2.5 rounded-lg bg-black/35 border border-panelBorder text-xs">
                          <p className="font-bold text-accent mb-1 flex items-center gap-1"><Users className="h-3.5 w-3.5" /> Key People</p>
                          <p className="text-mutedText leading-normal">{analysisResult.entities.people?.join(", ") || "None Identified"}</p>
                        </div>
                      </div>
                    </details>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </main>

      {/* ── SOURCE DOCUMENT ACCURACY VIEWER MODAL ──────────────────────────── */}
      {activeCitationSource && (
        <SourceViewerModal
          citation={activeCitationSource}
          onClose={() => setActiveCitationSource(null)}
        />
      )}
    </div>
  );
}
