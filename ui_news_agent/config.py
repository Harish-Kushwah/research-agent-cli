from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_MODEL = "qwen3.5:4b"
DEFAULT_QUERY = "latest UI UX trends 2026"


@dataclass(frozen=True)
class AppConfig:
    vault_dir: Path = Path("Vault/Harish")
    model: str = DEFAULT_MODEL
    max_results: int = 5

    @property
    def reports_root(self) -> Path:
        return self.vault_dir / "Reports"

    @property
    def sources_root(self) -> Path:
        return self.vault_dir / "Sources"

    @property
    def index_note(self) -> Path:
        return self.vault_dir / "Trends.md"


@dataclass(frozen=True)
class RunPaths:
    query: str
    slug: str
    timestamp: datetime
    report_title: str
    report_path: Path
    report_link_path: str
    sources_dir: Path
    sources_link_dir: str


def build_run_paths(config: AppConfig, query: str, slug: str, timestamp: datetime) -> RunPaths:
    date_parts = [timestamp.strftime("%Y"), timestamp.strftime("%m"), timestamp.strftime("%d")]
    stamp = timestamp.strftime("%Y%m%d-%H%M%S")
    report_dir = config.reports_root.joinpath(*date_parts, slug)
    sources_dir = config.sources_root.joinpath(*date_parts, slug)
    report_filename = f"{slug}-{stamp}.md"
    report_path = report_dir / report_filename
    report_link_path = "/".join(["Reports", *date_parts, slug, report_path.stem])
    sources_link_dir = "/".join(["Sources", *date_parts, slug])
    report_title = f"{query} {timestamp.strftime('%Y-%m-%d %H-%M-%S')}"

    return RunPaths(
        query=query,
        slug=slug,
        timestamp=timestamp,
        report_title=report_title,
        report_path=report_path,
        report_link_path=report_link_path,
        sources_dir=sources_dir,
        sources_link_dir=sources_link_dir,
    )
