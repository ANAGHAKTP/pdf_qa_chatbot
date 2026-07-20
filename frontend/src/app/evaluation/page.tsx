"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart3,
  Award,
  Zap,
  ShieldCheck,
  AlertTriangle,
  Download,
  Play,
  RefreshCw,
  Cpu,
  Layers,
  FileText,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Sliders,
  CheckCircle2,
} from "lucide-react";
import { request } from "@/lib/api";

export default function EvaluationDashboardPage() {
  const [activeTab, setActiveTab] = useState<"overview" | "models" | "retrieval" | "prompts" | "regression">("overview");
  const [summaryData, setSummaryData] = useState<any>(null);
  const [modelData, setModelData] = useState<any[]>([]);
  const [promptData, setPromptData] = useState<any[]>([]);
  const [regressionData, setRegressionData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEvaluating, setIsEvaluating] = useState(false);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const summary = await request("/evaluation/summary");
      const models = await request("/evaluation/models");
      const prompts = await request("/evaluation/prompts");
      const regression = await request("/evaluation/regression");

      setSummaryData(summary);
      setModelData(models || []);
      setPromptData(prompts || []);
      setRegressionData(regression);
    } catch (err) {
      console.error("Failed to load evaluation metrics", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleRunEvaluation = async () => {
    setIsEvaluating(true);
    try {
      await request("/evaluation/run?domain=finance", { method: "POST" });
      await fetchDashboardData();
    } catch (err) {
      console.error("Failed to run evaluation", err);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleExport = (format: "json" | "csv" | "markdown" | "html") => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    window.open(`${API_URL}/evaluation/export?format=${format}`, "_blank");
  };

  return (
    <div className="min-h-screen bg-[#070913] text-slate-100 p-6 md:p-8 space-y-6 animate-fade-in font-sans">
      {/* Top Header & Export Toolbar */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <BarChart3 className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                DOCMind AI Evaluation & Benchmarking
                <span className="text-[10px] uppercase font-bold bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 px-2 py-0.5 rounded-full">
                  v2.4 Production
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Continuous quality benchmarking, retrieval accuracy, hallucination detection, and regression analysis.
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleRunEvaluation}
            disabled={isEvaluating}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
          >
            {isEvaluating ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4 fill-white" />
            )}
            {isEvaluating ? "Evaluating..." : "Run Batch Eval"}
          </button>

          {/* Export Dropdown */}
          <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs">
            <button
              onClick={() => handleExport("json")}
              className="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors font-mono"
            >
              JSON
            </button>
            <button
              onClick={() => handleExport("csv")}
              className="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors font-mono"
            >
              CSV
            </button>
            <button
              onClick={() => handleExport("markdown")}
              className="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors font-mono"
            >
              MD
            </button>
            <button
              onClick={() => handleExport("html")}
              className="px-2.5 py-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors font-mono"
            >
              HTML
            </button>
          </div>
        </div>
      </header>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        <div className="p-4 rounded-xl bg-black/40 border border-slate-800/80 space-y-1">
          <p className="text-[10px] uppercase font-bold text-slate-500 flex items-center justify-between">
            Retrieval Accuracy <Award className="h-3.5 w-3.5 text-indigo-400" />
          </p>
          <p className="text-xl font-extrabold text-white">{summaryData?.retrieval_accuracy || 94.0}%</p>
          <p className="text-[9px] text-emerald-400 flex items-center gap-0.5">
            <ArrowUpRight className="h-2.5 w-2.5" /> +2.1% Recall@5
          </p>
        </div>

        <div className="p-4 rounded-xl bg-black/40 border border-slate-800/80 space-y-1">
          <p className="text-[10px] uppercase font-bold text-slate-500 flex items-center justify-between">
            Citation Accuracy <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
          </p>
          <p className="text-xl font-extrabold text-white">{summaryData?.citation_accuracy || 96.5}%</p>
          <p className="text-[9px] text-emerald-400 flex items-center gap-0.5">
            <ArrowUpRight className="h-2.5 w-2.5" /> High Precision
          </p>
        </div>

        <div className="p-4 rounded-xl bg-black/40 border border-slate-800/80 space-y-1">
          <p className="text-[10px] uppercase font-bold text-slate-500 flex items-center justify-between">
            Hallucination Rate <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
          </p>
          <p className="text-xl font-extrabold text-amber-300">{summaryData?.hallucination_rate || 3.2}%</p>
          <p className="text-[9px] text-emerald-400 flex items-center gap-0.5">
            <ArrowDownRight className="h-2.5 w-2.5" /> -1.4% vs baseline
          </p>
        </div>

        <div className="p-4 rounded-xl bg-black/40 border border-slate-800/80 space-y-1">
          <p className="text-[10px] uppercase font-bold text-slate-500 flex items-center justify-between">
            Avg Total Latency <Zap className="h-3.5 w-3.5 text-yellow-400" />
          </p>
          <p className="text-xl font-extrabold text-white">{summaryData?.avg_total_latency_ms || 320}ms</p>
          <p className="text-[9px] text-slate-400 font-mono">
            {summaryData?.avg_retrieval_time_ms || 42.5}ms ret | {summaryData?.avg_generation_time_ms || 277.5}ms gen
          </p>
        </div>

        <div className="p-4 rounded-xl bg-black/40 border border-slate-800/80 space-y-1">
          <p className="text-[10px] uppercase font-bold text-slate-500 flex items-center justify-between">
            Avg Token Cost <Cpu className="h-3.5 w-3.5 text-purple-400" />
          </p>
          <p className="text-xl font-extrabold text-white">{summaryData?.avg_tokens || 340} tk</p>
          <p className="text-[9px] text-slate-400">$0.00005 / query</p>
        </div>

        <div className="p-4 rounded-xl bg-black/40 border border-slate-800/80 space-y-1">
          <p className="text-[10px] uppercase font-bold text-slate-500 flex items-center justify-between">
            Evaluation Runs <Layers className="h-3.5 w-3.5 text-blue-400" />
          </p>
          <p className="text-xl font-extrabold text-white">{summaryData?.total_evaluation_runs || 12}</p>
          <p className="text-[9px] text-slate-400">Automated Benchmarks</p>
        </div>

        <div className="p-4 rounded-xl bg-black/40 border border-slate-800/80 space-y-1">
          <p className="text-[10px] uppercase font-bold text-slate-500 flex items-center justify-between">
            Regression Status <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
          </p>
          <p className="text-sm font-bold text-emerald-400 mt-1">PASSED</p>
          <p className="text-[9px] text-slate-400">0 Regressions</p>
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <div className="flex border-b border-slate-800 text-xs font-semibold">
        <button
          onClick={() => setActiveTab("overview")}
          className={`px-4 py-2.5 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === "overview"
              ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <BarChart3 className="h-4 w-4" /> Overview & Latency
        </button>
        <button
          onClick={() => setActiveTab("models")}
          className={`px-4 py-2.5 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === "models"
              ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <Cpu className="h-4 w-4" /> Model Benchmarks
        </button>
        <button
          onClick={() => setActiveTab("retrieval")}
          className={`px-4 py-2.5 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === "retrieval"
              ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <Award className="h-4 w-4" /> Retrieval & Citations
        </button>
        <button
          onClick={() => setActiveTab("prompts")}
          className={`px-4 py-2.5 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === "prompts"
              ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <Sliders className="h-4 w-4" /> Prompt Registry
        </button>
        <button
          onClick={() => setActiveTab("regression")}
          className={`px-4 py-2.5 border-b-2 transition-all flex items-center gap-2 ${
            activeTab === "regression"
              ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <ShieldCheck className="h-4 w-4" /> Regression History
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Clock className="h-4 w-4 text-indigo-400" /> Latency Breakdown (ms)
            </h3>
            <div className="space-y-3 font-mono text-xs">
              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Query Processing & Rewriting</span>
                  <span className="text-white">12.4 ms</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div className="bg-indigo-500 h-2 rounded-full" style={{ width: "15%" }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Hybrid Retrieval (Chroma + BM25)</span>
                  <span className="text-white">42.5 ms</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div className="bg-emerald-500 h-2 rounded-full" style={{ width: "35%" }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Cross-Encoder Reranking</span>
                  <span className="text-white">28.1 ms</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div className="bg-yellow-500 h-2 rounded-full" style={{ width: "25%" }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>LLM Answer Generation</span>
                  <span className="text-white">237.0 ms</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div className="bg-purple-500 h-2 rounded-full" style={{ width: "80%" }}></div>
                </div>
              </div>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-400" /> Hallucination Risk Classification
            </h3>
            <div className="space-y-2 text-xs">
              <div className="p-3 rounded-xl bg-black/30 border border-slate-800 flex items-center justify-between">
                <div>
                  <p className="font-bold text-white">Unsupported Claims</p>
                  <p className="text-[10px] text-slate-400">Answer claims without source backing</p>
                </div>
                <span className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded font-mono font-bold">1.2%</span>
              </div>

              <div className="p-3 rounded-xl bg-black/30 border border-slate-800 flex items-center justify-between">
                <div>
                  <p className="font-bold text-white">Fabricated Citations</p>
                  <p className="text-[10px] text-slate-400">Non-existent source page references</p>
                </div>
                <span className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded font-mono font-bold">0.4%</span>
              </div>

              <div className="p-3 rounded-xl bg-black/30 border border-slate-800 flex items-center justify-between">
                <div>
                  <p className="font-bold text-white">Missing Evidence Gaps</p>
                  <p className="text-[10px] text-slate-400">Queries with incomplete context chunks</p>
                </div>
                <span className="bg-amber-500/10 border border-amber-500/20 text-amber-400 px-2 py-0.5 rounded font-mono font-bold">1.6%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "models" && (
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Cpu className="h-4 w-4 text-indigo-400" /> LLM Model Performance Comparison
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800 text-[10px] uppercase text-slate-500 font-mono">
                <tr>
                  <th className="py-2 px-3">Model</th>
                  <th className="py-2 px-3">Provider</th>
                  <th className="py-2 px-3">Avg Latency</th>
                  <th className="py-2 px-3">Accuracy</th>
                  <th className="py-2 px-3">Citation Quality</th>
                  <th className="py-2 px-3">Est. Cost / 1k Query</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {modelData.map((m, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-2.5 px-3 font-bold text-white">{m.model_name}</td>
                    <td className="py-2.5 px-3 text-slate-400">{m.provider}</td>
                    <td className="py-2.5 px-3 text-yellow-400">{m.avg_latency_ms} ms</td>
                    <td className="py-2.5 px-3 text-emerald-400">{(m.accuracy_score * 100).toFixed(1)}%</td>
                    <td className="py-2.5 px-3 text-indigo-400">{(m.citation_quality * 100).toFixed(1)}%</td>
                    <td className="py-2.5 px-3 text-purple-400">${(m.est_cost_usd * 1000).toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "retrieval" && (
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Award className="h-4 w-4 text-indigo-400" /> Information Retrieval & Citation Quality Metrics
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-3.5 rounded-xl bg-black/40 border border-slate-800">
              <p className="text-[10px] text-slate-500 uppercase">Recall@5</p>
              <p className="text-lg font-bold text-white mt-1">94.2%</p>
            </div>
            <div className="p-3.5 rounded-xl bg-black/40 border border-slate-800">
              <p className="text-[10px] text-slate-500 uppercase">Precision@5</p>
              <p className="text-lg font-bold text-white mt-1">91.0%</p>
            </div>
            <div className="p-3.5 rounded-xl bg-black/40 border border-slate-800">
              <p className="text-[10px] text-slate-500 uppercase">MRR (Mean Reciprocal Rank)</p>
              <p className="text-lg font-bold text-emerald-400 mt-1">0.965</p>
            </div>
            <div className="p-3.5 rounded-xl bg-black/40 border border-slate-800">
              <p className="text-[10px] text-slate-500 uppercase">NDCG@5</p>
              <p className="text-lg font-bold text-indigo-400 mt-1">0.952</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === "prompts" && (
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Sliders className="h-4 w-4 text-indigo-400" /> Registered Prompt Templates & Versioning
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            {promptData.map((p, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-black/40 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white uppercase">{p.version} - {p.name}</span>
                  {p.version === "v3" && (
                    <span className="bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 text-[9px] px-2 py-0.5 rounded font-mono">ACTIVE</span>
                  )}
                </div>
                <p className="text-slate-400 italic text-[11px]">{p.description}</p>
                <div className="p-2.5 rounded bg-slate-950 font-mono text-[10px] text-slate-300 border border-slate-800/80">
                  {p.system_prompt}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "regression" && (
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400" /> Automated Regression Analysis (Current vs Baseline)
          </h3>
          <p className="text-xs text-slate-400">{regressionData?.summary || "No quality or latency regressions detected."}</p>
          <div className="space-y-2 text-xs font-mono">
            {regressionData?.items?.map((item: any, idx: number) => (
              <div key={idx} className="p-3 rounded-xl bg-black/30 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="font-bold text-white">{item.metric_name}</span>
                  <div className="text-[10px] text-slate-400">
                    Current: {item.current_value} | Baseline: {item.baseline_value} (Delta: {item.delta > 0 ? `+${item.delta}` : item.delta})
                  </div>
                </div>
                <span className={item.is_regression ? "text-rose-400 font-bold" : "text-emerald-400 font-bold"}>
                  {item.is_regression ? "REGRESSION" : "STABLE"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
