"""Tests for Vault Claude Code patterns: ownership mixin, sync failure queue."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


# -- ProfileOwnershipMixin --

def test_ownership_mixin_filters_by_profile():
    from api.mixins import ProfileOwnershipMixin

    class FakeQuerySet:
        def filter(self, **kwargs):
            self.filter_kwargs = kwargs
            return self

    class FakeParent:
        def get_queryset(self):
            return FakeQuerySet()

    class TestViewSet(ProfileOwnershipMixin, FakeParent):
        pass

    vs = TestViewSet()
    vs.request = MagicMock()
    vs.request.profile = "profile-123"

    qs = vs.get_queryset()
    assert qs.filter_kwargs == {"profile": "profile-123"}


def test_ownership_mixin_create_assigns_profile():
    from api.mixins import ProfileOwnershipMixin

    class FakeParent:
        pass

    class TestViewSet(ProfileOwnershipMixin, FakeParent):
        pass

    vs = TestViewSet()
    vs.request = MagicMock()
    vs.request.profile = "profile-456"

    serializer = MagicMock()
    vs.perform_create(serializer)
    serializer.save.assert_called_once_with(profile="profile-456")


# -- SyncFailureQueue --

def test_sync_queue_add_and_count(tmp_path):
    from api.sync_failure import SyncFailureQueue

    q = SyncFailureQueue(tmp_path / "sync_failures.json")
    q.add("bank_import", {"file": "extract.csv"}, "Parse error line 42")
    assert q.pending_count == 1
    assert q.dead_count == 0


def test_sync_queue_persists_to_disk(tmp_path):
    from api.sync_failure import SyncFailureQueue

    path = tmp_path / "sync_failures.json"
    q = SyncFailureQueue(path)
    q.add("bank_import", {"file": "x.csv"}, "error")

    # Reload from disk
    q2 = SyncFailureQueue(path)
    assert q2.pending_count == 1


def test_sync_queue_max_retries_moves_to_dead(tmp_path):
    from api.sync_failure import SyncFailureQueue

    q = SyncFailureQueue(tmp_path / "sync.json", max_retries=2)
    q.add("api_sync", {"endpoint": "/data"}, "timeout")

    failure = q._failures[0]
    q.mark_failed(failure, "timeout again")  # attempt 2 = max

    assert q.pending_count == 0
    assert q.dead_count == 1


def test_sync_queue_mark_success(tmp_path):
    from api.sync_failure import SyncFailureQueue

    q = SyncFailureQueue(tmp_path / "sync.json")
    q.add("api_sync", {}, "error")
    failure = q._failures[0]
    q.mark_success(failure)
    assert q.pending_count == 0


def test_sync_queue_stats(tmp_path):
    from api.sync_failure import SyncFailureQueue

    q = SyncFailureQueue(tmp_path / "sync.json", max_retries=1)
    q.add("a", {}, "e1")
    q.add("b", {}, "e2")

    # Move one to dead
    failure = q._failures[0]
    q.mark_failed(failure, "final")

    stats = q.stats()
    assert stats["pending"] == 1
    assert stats["dead"] == 1
    assert stats["total"] == 2
