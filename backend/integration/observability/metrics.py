"""Runtime metrics for integration orchestration."""

from __future__ import annotations

from collections import Counter

METRICS: Counter[str] = Counter()


def increment(metric: str, value: int = 1) -> None:
    METRICS[metric] += value


def snapshot() -> dict[str, int]:
    return dict(METRICS)
