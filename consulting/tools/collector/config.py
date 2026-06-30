"""Config loader — YAML to dataclass with path resolution."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TargetSource:
    file: str
    format: str = "csv"
    group: str = "default"
    id_column: str = "channelId"
    name_column: str = "channel_name"
    filter: dict[str, Any] | None = None


@dataclass
class Signal:
    pattern: str
    action: str = "abort"  # abort | skip


@dataclass
class Config:
    # -- job --
    job_name: str = "unnamed"
    job_description: str = ""

    # -- targets --
    target_sources: list[TargetSource] = field(default_factory=list)
    dedupe_enabled: bool = True
    dedupe_priority: list[str] = field(default_factory=lambda: ["T1", "T2"])

    # -- url --
    url_template: str = ""
    url_params: dict[str, str] = field(default_factory=dict)

    # -- engine --
    engine_type: str = "nodriver"
    engine_headless: bool = False
    engine_lang: str = "ko-KR"
    engine_profile_dir: str | None = None

    # -- extraction --
    extraction_method: str = "dom_eval"
    expression_file: str | None = None
    wait_poll_ms: int = 2000
    wait_timeout_ms: int = 12000
    checkpoint_wait_ms: int = 0
    signals: dict[str, Signal] = field(default_factory=dict)
    validation_min_rows: int = 1

    # -- output --
    output_dir: str = "output"
    output_file_pattern: str = "{channelId}.csv"
    output_columns: list[str] = field(default_factory=list)

    # -- rate --
    rate_delay_ms: int = 10000
    rate_jitter_ms: int = 5000
    rate_seed: int = 42

    # -- resume --
    resume_skip_existing: bool = True
    resume_skip_progress: bool = True
    resume_progress_glob: str = "_collection_progress_*.ndjson"

    # -- resolved at load time --
    config_dir: Path = field(default_factory=lambda: Path("."))

    def resolve(self, rel: str) -> Path:
        """Resolve a path relative to the config file's directory."""
        p = Path(rel)
        if p.is_absolute():
            return p
        return (self.config_dir / p).resolve()


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def _parse_signal(raw: Any) -> Signal:
    if isinstance(raw, str):
        return Signal(pattern=raw, action="abort")
    if isinstance(raw, dict):
        return Signal(
            pattern=raw.get("pattern", ""),
            action=raw.get("action", "abort"),
        )
    raise ValueError(f"invalid signal spec: {raw}")


def _parse_source(raw: dict[str, Any]) -> TargetSource:
    return TargetSource(
        file=raw["file"],
        format=raw.get("format", "csv"),
        group=raw.get("group", "default"),
        id_column=raw.get("id_column", "channelId"),
        name_column=raw.get("name_column", "channel_name"),
        filter=raw.get("filter"),
    )


def load_config(path: str | Path, overrides: dict[str, Any] | None = None) -> Config:
    """Load a YAML config, resolve relative paths, apply CLI overrides."""
    path = Path(path).resolve()
    text = path.read_text(encoding="utf-8")

    if yaml is not None:
        raw = yaml.safe_load(text)
    else:
        raw = json.loads(text)

    if not isinstance(raw, dict):
        raise ValueError("config must be a YAML/JSON mapping")

    config_dir = path.parent
    job = raw.get("job", {})
    targets = raw.get("targets", {})
    url = raw.get("url", {})
    engine = raw.get("engine", {})
    extraction = raw.get("extraction", {})
    output = raw.get("output", {})
    rate = raw.get("rate", {})
    resume = raw.get("resume", {})
    wait = extraction.get("wait", {})
    raw_signals = extraction.get("signals", {})

    cfg = Config(
        config_dir=config_dir,
        # job
        job_name=job.get("name", "unnamed"),
        job_description=job.get("description", ""),
        # targets
        target_sources=[_parse_source(s) for s in targets.get("sources", [])],
        dedupe_enabled=targets.get("dedupe", {}).get("enabled", True),
        dedupe_priority=targets.get("dedupe", {}).get("priority", ["T1", "T2"]),
        # url
        url_template=url.get("template", ""),
        url_params=url.get("params", {}),
        # engine
        engine_type=engine.get("type", "nodriver"),
        engine_headless=engine.get("headless", False),
        engine_lang=engine.get("lang", "ko-KR"),
        engine_profile_dir=engine.get("profile_dir"),
        # extraction
        extraction_method=extraction.get("method", "dom_eval"),
        expression_file=extraction.get("expression_file"),
        wait_poll_ms=wait.get("poll_ms", 2000),
        wait_timeout_ms=wait.get("timeout_ms", 12000),
        checkpoint_wait_ms=wait.get("checkpoint_wait_ms", 0),
        signals={name: _parse_signal(spec) for name, spec in raw_signals.items()},
        validation_min_rows=extraction.get("validation", {}).get("min_rows", 1),
        # output
        output_dir=output.get("dir", "output"),
        output_file_pattern=output.get("file_pattern", "{channelId}.csv"),
        output_columns=output.get("columns", []),
        # rate
        rate_delay_ms=rate.get("delay_ms", 10000),
        rate_jitter_ms=rate.get("jitter_ms", 5000),
        rate_seed=rate.get("seed", 42),
        # resume
        resume_skip_existing=resume.get("skip_existing", True),
        resume_skip_progress=resume.get("skip_progress", True),
        resume_progress_glob=resume.get("progress_glob", "_collection_progress_*.ndjson"),
    )

    # apply CLI overrides
    if overrides:
        for key, value in overrides.items():
            if value is not None and hasattr(cfg, key):
                setattr(cfg, key, value)

    return cfg
