from typing import Dict, Any, List
from dataclasses import dataclass, field, asdict

@dataclass
class RegressionItem:
    metric_name: str
    current_value: float
    baseline_value: float
    delta: float
    is_regression: bool
    threshold: float


@dataclass
class RegressionReport:
    has_regression: bool
    regressions_count: int
    items: List[RegressionItem] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_regression": self.has_regression,
            "regressions_count": self.regressions_count,
            "items": [asdict(i) for i in self.items],
            "summary": self.summary
        }


class RegressionDetector:
    """
    Compares current run metrics against baseline run metrics to detect quality or latency regressions.
    """

    THRESHOLDS = {
        "recall_at_k": -0.05,
        "precision_at_k": -0.05,
        "answer_similarity": -0.05,
        "citation_accuracy": -0.05,
        "avg_latency_ms": 150.0  # Latency increase > 150ms is a regression
    }

    @classmethod
    def compare(
        cls,
        current_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float]
    ) -> RegressionReport:
        items: List[RegressionItem] = []
        regressions_count = 0

        for metric, current_val in current_metrics.items():
            if metric not in baseline_metrics:
                continue

            baseline_val = baseline_metrics[metric]
            delta = round(current_val - baseline_val, 4)
            threshold = cls.THRESHOLDS.get(metric, -0.05)

            is_reg = False
            if metric == "avg_latency_ms":
                if delta > threshold:
                    is_reg = True
            else:
                if delta < threshold:
                    is_reg = True

            if is_reg:
                regressions_count += 1

            items.append(RegressionItem(
                metric_name=metric,
                current_value=current_val,
                baseline_value=baseline_val,
                delta=delta,
                is_regression=is_reg,
                threshold=threshold
            ))

        has_reg = regressions_count > 0
        summary = f"Detected {regressions_count} regression(s) relative to baseline." if has_reg else "No regressions detected."

        return RegressionReport(
            has_regression=has_reg,
            regressions_count=regressions_count,
            items=items,
            summary=summary
        )
