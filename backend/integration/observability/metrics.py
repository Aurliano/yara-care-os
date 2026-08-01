"""In-process metrics hooks (delegates to shared registry)."""

from common.observability.metrics import METRICS, increment, snapshot

__all__ = ["METRICS", "increment", "snapshot"]
