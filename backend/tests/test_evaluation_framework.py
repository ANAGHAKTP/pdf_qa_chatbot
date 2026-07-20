import pytest
from app.evaluation.dataset_loader import DatasetLoader
from app.evaluation.runner import EvaluationRunner
from app.evaluation.retrieval_metrics import RetrievalEvaluator
from app.evaluation.answer_metrics import AnswerQualityEvaluator
from app.evaluation.citation_metrics import CitationEvaluator
from app.evaluation.hallucination_analyzer import HallucinationAnalyzer
from app.evaluation.prompt_registry import PromptRegistry
from app.evaluation.model_benchmark import ModelBenchmark
from app.evaluation.embedding_benchmark import EmbeddingBenchmark
from app.evaluation.regression import RegressionDetector
from app.evaluation.exporters import EvaluationExporter


def test_dataset_loader():
    datasets = DatasetLoader.list_datasets()
    assert isinstance(datasets, list)

    cases = DatasetLoader.load_dataset("finance")
    assert isinstance(cases, list)
    if cases:
        assert cases[0].id.startswith("fin_")
        assert cases[0].question is not None


def test_retrieval_evaluator():
    retrieved = [
        {"page": 1, "text": "Q3 revenue reached $52.4M."},
        {"page": 2, "text": "EBITDA margin reached 28.5%."}
    ]
    expected = [{"page": 1, "keyword": "revenue"}]

    metrics = RetrievalEvaluator.evaluate(retrieved, expected, k=5)

    assert metrics.recall_at_k == 1.0
    assert metrics.hit_rate == 1.0
    assert metrics.mrr == 1.0


def test_answer_quality_evaluator():
    gen = "Revenue reached $52.4 million in Q3."
    exp = "Total revenue in Q3 was $52.4 million."

    res = AnswerQualityEvaluator.evaluate(gen, exp)

    assert res.bleu_score > 0.0
    assert res.rouge_l_score > 0.0
    assert res.answer_similarity > 0.0


def test_citation_evaluator():
    gen_cits = [{"page": 1, "filename": "doc.pdf"}]
    exp_cits = [{"page": 1, "keyword": "revenue"}]

    res = CitationEvaluator.evaluate(gen_cits, exp_cits)

    assert res.citation_accuracy == 1.0
    assert res.hallucinated_citation_rate == 0.0


def test_hallucination_analyzer():
    gen_ans = "The revenue reached $52.4 million."
    contexts = ["Total revenue in Q3 was $52.4M."]
    citations = [{"page": 1}]

    report = HallucinationAnalyzer.analyze(gen_ans, contexts, citations, confidence_level="HIGH")

    assert report.has_hallucination is False
    assert report.hallucination_score == 0.0


def test_prompt_registry():
    prompts = PromptRegistry.list_prompts()
    assert len(prompts) >= 3

    p3 = PromptRegistry.get_prompt("v3")
    assert p3.version == "v3"
    assert "DOCMind" in p3.system_prompt or "strictly" in p3.system_prompt


def test_model_benchmark():
    queries = [{"latency_ms": 300, "accuracy": 0.95, "tokens": 250, "confidence": "HIGH"}]
    res = ModelBenchmark.benchmark_model("gemini-1.5-flash", queries)

    assert res.model_name == "gemini-1.5-flash"
    assert res.avg_latency_ms == 300.0
    assert res.accuracy_score == 0.95


def test_embedding_benchmark():
    res = EmbeddingBenchmark.benchmark_model("nvidia-nv-embed-v1")

    assert res.model_name == "nvidia-nv-embed-v1"
    assert res.recall_at_k > 0.80
    assert res.search_qps > 100.0


def test_regression_detector():
    current = {"recall_at_k": 0.94, "avg_latency_ms": 300.0}
    baseline = {"recall_at_k": 0.92, "avg_latency_ms": 310.0}

    report = RegressionDetector.compare(current, baseline)

    assert report.has_regression is False
    assert report.regressions_count == 0


def test_evaluation_exporter():
    data = {
        "run_id": "RUN-123",
        "dataset": "finance",
        "metrics": {"Recall@5": 0.95, "Precision@5": 0.90}
    }

    json_str = EvaluationExporter.to_json(data)
    assert "RUN-123" in json_str

    csv_str = EvaluationExporter.to_csv(data)
    assert "Recall@5" in csv_str

    md_str = EvaluationExporter.to_markdown(data)
    assert "# Evaluation Report" in md_str

    html_str = EvaluationExporter.to_html(data)
    assert "<html>" in html_str


def test_evaluation_runner():
    runner = EvaluationRunner()
    report = runner.run_eval("finance")

    assert report.run_id.startswith("eval_")
    assert report.total_cases >= 1
    assert "recall_at_k" in report.metrics
