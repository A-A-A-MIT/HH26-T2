from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RAGResponse:
    status: str
    answer: Optional[str] = None

    grounded: bool = False

    retrieval_confidence: float = 0.0
    grounding_score: float = 0.0

    sources: list[str] = field(default_factory=list)

    reason: Optional[str] = None
    latency_ms: float = 0.0