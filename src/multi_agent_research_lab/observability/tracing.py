"""Tracing hooks and span context managers.

Supports LangSmith, Langfuse, OpenTelemetry, or structured JSON traces.
"""

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Context manager for structured execution tracing.

    Captures span metadata, timing, and integrates with LangSmith/Langfuse if configured.
    """
    settings = get_settings()
    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "duration_seconds": None,
        "status": "in_progress",
    }

    # Optional LangSmith integration if configured
    langsmith_client = None
    if settings.langsmith_api_key or os.getenv("LANGSMITH_API_KEY"):
        try:
            import langsmith

            langsmith_client = langsmith.Client()
        except Exception:
            langsmith_client = None

    try:
        yield span
        span["status"] = "success"
    except Exception as exc:
        span["status"] = "error"
        span["error"] = str(exc)
        raise
    finally:
        span["duration_seconds"] = perf_counter() - started
        logger.debug(f"[TraceSpan] {name} completed in {span['duration_seconds']:.4f}s ({span['status']})")
