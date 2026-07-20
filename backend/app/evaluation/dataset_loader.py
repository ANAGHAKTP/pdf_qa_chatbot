import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class EvaluationTestCase:
    id: str
    document_set: List[str]
    question: str
    expected_answer: str
    expected_citations: List[Dict[str, Any]]
    expected_confidence: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatasetLoader:
    """
    Loads golden datasets from backend/app/evaluation/datasets/ supporting JSON and YAML formats.
    """

    BASE_DIR = os.path.dirname(__file__)
    DATASETS_DIR = os.path.join(BASE_DIR, "datasets")

    @classmethod
    def list_datasets(cls) -> List[Dict[str, Any]]:
        datasets = []
        if not os.path.exists(cls.DATASETS_DIR):
            return datasets

        for domain in os.listdir(cls.DATASETS_DIR):
            domain_path = os.path.join(cls.DATASETS_DIR, domain)
            if os.path.isdir(domain_path):
                files = [f for f in os.listdir(domain_path) if f.endswith(".json") or f.endswith(".yaml") or f.endswith(".yml")]
                datasets.append({
                    "domain": domain,
                    "files": files,
                    "count": len(files)
                })
        return datasets

    @classmethod
    def load_dataset(cls, domain: str, filename: Optional[str] = None) -> List[EvaluationTestCase]:
        cases: List[EvaluationTestCase] = []
        domain_path = os.path.join(cls.DATASETS_DIR, domain)

        if not os.path.exists(domain_path):
            return cases

        target_files = [filename] if filename else os.listdir(domain_path)

        for fname in target_files:
            file_path = os.path.join(domain_path, fname)
            if not os.path.isfile(file_path):
                continue

            try:
                if fname.endswith(".json"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        raw_data = json.load(f)
                elif fname.endswith(".yaml") or fname.endswith(".yml"):
                    import yaml
                    with open(file_path, "r", encoding="utf-8") as f:
                        raw_data = yaml.safe_load(f)
                else:
                    continue

                for item in raw_data:
                    cases.append(EvaluationTestCase(
                        id=item["id"],
                        document_set=item.get("document_set", []),
                        question=item["question"],
                        expected_answer=item.get("expected_answer", ""),
                        expected_citations=item.get("expected_citations", []),
                        expected_confidence=item.get("expected_confidence", "HIGH"),
                        metadata=item.get("metadata", {})
                    ))
            except Exception:
                pass

        return cases
