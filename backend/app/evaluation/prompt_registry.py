from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class PromptTemplate:
    version: str
    name: str
    system_prompt: str
    description: str


class PromptRegistry:
    """
    Manages prompt versions (Prompt V1, V2, V3) for benchmark comparisons.
    """

    PROMPTS: Dict[str, PromptTemplate] = {
        "v1": PromptTemplate(
            version="v1",
            name="Baseline Concise Prompt",
            system_prompt="Answer the user query concisely based on the context. Include page numbers.",
            description="Simple baseline prompt."
        ),
        "v2": PromptTemplate(
            version="v2",
            name="Structured Citation Prompt",
            system_prompt="You are DOCMind AI. Answer accurately using context chunks. Format citations like [1] for page 1.",
            description="Enhanced citation formatting prompt."
        ),
        "v3": PromptTemplate(
            version="v3",
            name="Strict Evidence Guard Prompt",
            system_prompt="Answer strictly from provided context. Explicitly reference Text, Tables (Table 1), and Figures (Figure 1). Never hallucinate outside context.",
            description="Strict multimodal evidence guard prompt."
        ),
    }

    @classmethod
    def get_prompt(cls, version: str = "v3") -> PromptTemplate:
        return cls.PROMPTS.get(version.lower(), cls.PROMPTS["v3"])

    @classmethod
    def list_prompts(cls) -> List[Dict[str, Any]]:
        return [asdict(p) for p in cls.PROMPTS.values()]
