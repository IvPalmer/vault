"""Functional tests for ProfileMiddleware auth gate (no DB — Profile/JWT mocked).

Run: cd backend && ./venv/bin/python -m pytest api/tests/test_auth_middleware.py
or:  cd backend && ./venv/bin/python -m unittest api.tests.test_auth_middleware
"""
import json
import unittest
from unittest import mock
from uuid import uuid4

import django
from django.conf import settings

if not settings.configured or not getattr(django, "_setup_done", False):
    django.setup()

from django.test import RequestFactory  # noqa: E402

from api.middleware import ProfileMiddleware  # noqa: E402


class FakeProfile:
    def __init__(self, pid):
        self.id = pid
        self.is_active = True


def make_mw(captured):
    def get_response(request):
        captured["request"] = request
        captured["reached_view"] = True
        return "VIEW_OK"
    return ProfileMiddleware(get_response)


class AuthGateTests(unittest.TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.captured = {"reached_view": False}
        self.mw = make_mw(self.captured)

    def _run(self, request):
        return self.mw(request)

    def test_options_bypasses_gate(self):
        resp = self._run(self.rf.options("/api/transactions/"))
        self.assertEqual(resp, "VIEW_OK")
        self.assertTrue(self.captured["reached_view"])

    def test_public_path_no_creds_passes(self):
        resp = self._run(self.rf.get("/api/auth/google/"))
        self.assertEqual(resp, "VIEW_OK")

    def test_boundary_lookalike_is_not_public(self):
        # '/api/authz' must NOT inherit '/api/auth' public status
        resp = self._run(self.rf.get("/api/authz/steal/"))
        self.assertEqual(resp.status_code, 401)
        self.assertFalse(self.captured["reached_view"])

    def test_protected_no_creds_401(self):
        resp = self._run(self.rf.get("/api/transactions/"))
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(json.loads(resp.content)["error"], "Authentication required")

    def test_xprofileid_alone_is_rejected(self):
        # The old hole: X-Profile-ID with no token used to be trusted.
        resp = self._run(
            self.rf.get("/api/transactions/", HTTP_X_PROFILE_ID=str(uuid4()))
        )
        self.assertEqual(resp.status_code, 401)

    def test_valid_jwt_passes_and_sets_profile(self):
        pid = uuid4()
        prof = FakeProfile(pid)
        with mock.patch.object(
            ProfileMiddleware, "jwt_auth", create=True
        ):
            with mock.patch(
                "api.middleware.JWTAuthentication.get_validated_token",
                return_value={"profile_id": str(pid)},
            ), mock.patch(
                "api.middleware.Profile.objects.get", return_value=prof
            ):
                mw = make_mw(self.captured)
                req = self.rf.get(
                    "/api/transactions/", HTTP_AUTHORIZATION="Bearer faketoken"
                )
                resp = mw(req)
        self.assertEqual(resp, "VIEW_OK")
        self.assertTrue(req.profile_authenticated)
        self.assertIs(req.profile, prof)

    def test_jwt_with_profile_target_override(self):
        own = FakeProfile(uuid4())
        target = FakeProfile(uuid4())

        def get_side_effect(id=None, is_active=None, **kw):
            return target if str(id) == str(target.id) else own

        with mock.patch(
            "api.middleware.JWTAuthentication.get_validated_token",
            return_value={"profile_id": str(own.id)},
        ), mock.patch(
            "api.middleware.Profile.objects.get", side_effect=get_side_effect
        ):
            mw = make_mw(self.captured)
            req = self.rf.get(
                "/api/transactions/",
                HTTP_AUTHORIZATION="Bearer faketoken",
                HTTP_X_PROFILE_ID=str(target.id),
            )
            resp = mw(req)
        self.assertEqual(resp, "VIEW_OK")
        self.assertIs(req.profile, target)  # switched to the other profile

    def test_internal_token_path(self):
        target = FakeProfile(uuid4())
        with mock.patch("api.middleware.VAULT_INTERNAL_TOKEN", "s3cret"), mock.patch(
            "api.middleware.Profile.objects.get", return_value=target
        ):
            mw = make_mw(self.captured)
            req = self.rf.get(
                "/api/transactions/",
                HTTP_X_INTERNAL_TOKEN="s3cret",
                HTTP_X_PROFILE_ID=str(target.id),
            )
            resp = mw(req)
        self.assertEqual(resp, "VIEW_OK")
        self.assertTrue(req.profile_authenticated)

    def test_wrong_internal_token_rejected(self):
        with mock.patch("api.middleware.VAULT_INTERNAL_TOKEN", "s3cret"):
            mw = make_mw(self.captured)
            req = self.rf.get(
                "/api/transactions/",
                HTTP_X_INTERNAL_TOKEN="wrong",
                HTTP_X_PROFILE_ID=str(uuid4()),
            )
            resp = mw(req)
        self.assertEqual(resp.status_code, 401)

    def test_unset_internal_token_does_not_authenticate(self):
        # If VAULT_INTERNAL_TOKEN is empty, an X-Internal-Token must NOT pass.
        with mock.patch("api.middleware.VAULT_INTERNAL_TOKEN", ""):
            mw = make_mw(self.captured)
            req = self.rf.get(
                "/api/transactions/",
                HTTP_X_INTERNAL_TOKEN="",
                HTTP_X_PROFILE_ID=str(uuid4()),
            )
            resp = mw(req)
        self.assertEqual(resp.status_code, 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)
