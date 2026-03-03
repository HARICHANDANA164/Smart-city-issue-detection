from __future__ import annotations

import json
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _call(base: str, path: str, method: str = "GET", data: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(f"{base}{path}", method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    payload = None if data is None else json.dumps(data).encode("utf-8")
    try:
        with urllib.request.urlopen(req, payload, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body) if body else {}


def test_register_login_and_issue_status_flow(tmp_path: Path) -> None:
    db_path = tmp_path / "test_ci.db"
    port = _free_port()
    base = f"http://127.0.0.1:{port}/api/v1"

    env = os.environ.copy()
    env["DB_PATH"] = str(db_path)

    backend_dir = Path(__file__).resolve().parents[2] / "backend"
    env["PYTHONPATH"] = str(backend_dir)
    proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(backend_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        started = False
        for _ in range(30):
            if proc.poll() is not None:
                out, err = proc.communicate(timeout=2)
                raise AssertionError(f"Server failed to start. stdout={out} stderr={err}")
            try:
                status, _ = _call(f"http://127.0.0.1:{port}", "/health")
                if status == 200:
                    started = True
                    break
            except Exception:
                pass
            time.sleep(0.2)
        assert started, "Server did not become healthy in time"

        status, otp_register_citizen = _call(base, "/auth/request-otp", "POST", {"identifier": "citizen@example.com", "purpose": "register"})
        assert status == 200

        status, citizen = _call(
            base,
            "/auth/register",
            "POST",
            {
                "name": "Citizen",
                "identifier": "citizen@example.com",
                "password": "password123",
                "otp": otp_register_citizen["demo_otp"],
                "role": "citizen",
            },
        )
        assert status == 200

        status, otp_login_citizen = _call(base, "/auth/request-otp", "POST", {"identifier": "citizen@example.com", "purpose": "login"})
        assert status == 200
        status, citizen_login = _call(
            base,
            "/auth/login",
            "POST",
            {"identifier": "citizen@example.com", "password": "password123", "otp": otp_login_citizen["demo_otp"]},
        )
        assert status == 200
        citizen_token = citizen_login["access_token"]

        status, otp_register_auth = _call(base, "/auth/request-otp", "POST", {"identifier": "+919876543210", "purpose": "register"})
        assert status == 200
        status, _ = _call(
            base,
            "/auth/register",
            "POST",
            {
                "name": "Authority",
                "identifier": "+919876543210",
                "password": "password123",
                "otp": otp_register_auth["demo_otp"],
                "role": "authority",
            },
        )
        assert status == 200

        status, otp_login_auth = _call(base, "/auth/request-otp", "POST", {"identifier": "+919876543210", "purpose": "login"})
        assert status == 200
        status, authority_login = _call(
            base,
            "/auth/login",
            "POST",
            {"identifier": "+919876543210", "password": "password123", "otp": otp_login_auth["demo_otp"]},
        )
        assert status == 200
        authority_token = authority_login["access_token"]

        status, issue = _call(
            base,
            "/issues",
            "POST",
            {
                "title": "Leak",
                "description": "Major water leak on central street.",
                "category": "Water & Drainage",
                "latitude": 28.612,
                "longitude": 77.229,
                "image_base64": None,
            },
            citizen_token,
        )
        assert status == 200

        status, _ = _call(
            base,
            f"/issues/{issue['id']}/status",
            "PATCH",
            {"status": "Not Started", "comment": "citizen attempt"},
            citizen_token,
        )
        assert status == 403

        status, updated = _call(
            base,
            f"/issues/{issue['id']}/status",
            "PATCH",
            {"status": "Not Started", "comment": "Team assigned"},
            authority_token,
        )
        assert status == 200
        assert updated["status"] == "Not Started"

        status, analytics = _call(base, "/dashboard/analytics")
        assert status == 200
        assert analytics["total_issues"] == 1
    finally:
        proc.terminate()
        proc.wait(timeout=10)
