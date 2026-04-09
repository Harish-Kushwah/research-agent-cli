from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceNote:
    name: str
    path: Path
    vault_link: str
    url: str
    domain: str
    content: str


@dataclass(frozen=True)
class LocalModelStatus:
    available: bool
    reason: str


@dataclass(frozen=True)
class RunResult:
    query: str
    report_path: Path
    urls: list[str]
    source_notes: list[SourceNote]
    memory_used: str
    model_status: LocalModelStatus
    thinking: str
    answer: str
