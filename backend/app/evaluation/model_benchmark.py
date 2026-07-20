import time
from typing import List, Dict, Any
from dataclasses import dataclass, field, asdict

@dataclass
class ModelBenchmarkResult:
    model_name: str
    provider: str
    avg_latency_ms: float
    est_cost_usd: float
    total_tokens: int
    accuracy_score: float
    citation_quality: float
    confidence_distribution: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ModelBenchmark:
    """
    Benchmarks LLM performance across models (Gemini, OpenAI, Claude, Local LLMs, NVIDIA NIM).
    """

    MODEL_PRICING_PER_1K_TOKENS = {
        "gemini-1.5-flash": 0.00015,
        "nvidia-nemotron": 0.00020,
        "gpt-4o-mini": 0.00030,
        "claude-3-haiku": 0.00025,
        "local-llama-3": 0.0,
    }

    @classmethod
    def benchmark_model(
        cls,
        model_name: str,
        queries_run: List[Dict[str, Any]]
    ) -> ModelBenchmarkResult:
        provider = "Google" if "gemini" in model_name.lower() else ("NVIDIA" if "nvidia" in model_name.lower() else "OpenAI")
        total_tokens = sum(q.get("tokens", 250) for q in queries_run) or 250
        rate = cls.MODEL_PRICING_PER_1K_TOKENS.get(model_name.lower(), 0.0002)
        est_cost = round((total_tokens / 1000.0) * rate, 5)

        avg_latency = float(sum(q.get("latency_ms", 450) for q in queries_run) / max(len(queries_run), 1))
        accuracy = float(sum(q.get("accuracy", 0.90) for q in queries_run) / max(len(queries_run), 1))
        citation_quality = float(sum(q.get("citation_score", 0.95) for q in queries_run) / max(len(queries_run), 1))

        conf_dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for q in queries_run:
            c = q.get("confidence", "HIGH")
            conf_dist[c] = conf_dist.get(c, 0) + 1

        return ModelBenchmarkResult(
            model_name=model_name,
            provider=provider,
            avg_latency_ms=round(avg_latency, 2),
            est_cost_usd=est_cost,
            total_tokens=total_tokens,
            accuracy_score=round(accuracy, 4),
            citation_quality=round(citation_quality, 4),
            confidence_distribution=conf_dist
        )
