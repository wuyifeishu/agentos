from dataclasses import dataclass
from enum import Enum


class ModelFamily(Enum):
    GPT = "gpt"


@dataclass
class TokenCount:
    input: int = 0
    output: int = 0


@dataclass
class CostEstimate:
    total: float = 0.0


class TokenCounter:
    pass
