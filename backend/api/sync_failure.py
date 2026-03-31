"""Dead-letter queue for failed sync operations.

Inspired by Claude Code's event retry with exponential backoff.
When data sync fails (bank imports, external API calls), the failure
is queued for retry instead of silently dropped.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SyncFailure:
    """A failed sync operation with retry metadata."""

    def __init__(
        self,
        source: str,
        payload: Dict[str, Any],
        error: str,
        attempt_count: int = 1,
        created_at: Optional[str] = None,
        next_retry: Optional[str] = None,
    ) -> None:
        self.source = source
        self.payload = payload
        self.error = error
        self.attempt_count = attempt_count
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        if next_retry:
            self.next_retry = next_retry
        else:
            # Exponential backoff: 1m, 2m, 4m, 8m, ...
            delay = timedelta(minutes=2 ** (attempt_count - 1))
            self.next_retry = (
                datetime.now(timezone.utc) + delay
            ).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "payload": self.payload,
            "error": self.error,
            "attempt_count": self.attempt_count,
            "created_at": self.created_at,
            "next_retry": self.next_retry,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncFailure":
        return cls(**data)


class SyncFailureQueue:
    """File-based dead-letter queue for failed sync operations.

    Stores failures as JSON and supports retry with exponential backoff.
    """

    def __init__(
        self,
        storage_path: Path,
        max_retries: int = 5,
    ) -> None:
        self.storage_path = storage_path
        self.max_retries = max_retries
        self._failures: List[SyncFailure] = []
        self._dead: List[SyncFailure] = []
        self._load()

    def _load(self) -> None:
        """Load failures from disk."""
        if not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text())
            self._failures = [
                SyncFailure.from_dict(f) for f in data.get("pending", [])
            ]
            self._dead = [
                SyncFailure.from_dict(f) for f in data.get("dead", [])
            ]
        except (json.JSONDecodeError, KeyError):
            logger.warning("Could not load sync failures from %s", self.storage_path)

    def _save(self) -> None:
        """Persist failures to disk."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "pending": [f.to_dict() for f in self._failures],
            "dead": [f.to_dict() for f in self._dead],
        }
        self.storage_path.write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )

    def add(self, source: str, payload: Dict[str, Any], error: str) -> None:
        """Add a failed sync operation to the queue."""
        failure = SyncFailure(source=source, payload=payload, error=error)
        self._failures.append(failure)
        self._save()
        logger.info("Sync failure queued: %s (%s)", source, error[:100])

    def get_retryable(self) -> List[SyncFailure]:
        """Get failures that are ready to retry."""
        now = datetime.now(timezone.utc).isoformat()
        return [f for f in self._failures if f.next_retry <= now]

    def mark_success(self, failure: SyncFailure) -> None:
        """Remove a failure after successful retry."""
        self._failures = [
            f for f in self._failures
            if not (f.source == failure.source and f.created_at == failure.created_at)
        ]
        self._save()

    def mark_failed(self, failure: SyncFailure, error: str) -> None:
        """Record a retry failure. Moves to dead queue after max retries."""
        failure.attempt_count += 1
        failure.error = error

        if failure.attempt_count >= self.max_retries:
            self._failures = [
                f for f in self._failures
                if not (f.source == failure.source and f.created_at == failure.created_at)
            ]
            self._dead.append(failure)
            logger.warning(
                "Sync failure moved to dead queue: %s (after %d attempts)",
                failure.source, failure.attempt_count,
            )
        else:
            delay = timedelta(minutes=2 ** (failure.attempt_count - 1))
            failure.next_retry = (
                datetime.now(timezone.utc) + delay
            ).isoformat()

        self._save()

    @property
    def pending_count(self) -> int:
        return len(self._failures)

    @property
    def dead_count(self) -> int:
        return len(self._dead)

    def stats(self) -> Dict[str, Any]:
        return {
            "pending": self.pending_count,
            "dead": self.dead_count,
            "total": self.pending_count + self.dead_count,
        }
