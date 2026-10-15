"""Boots the API on a free port with a temporary database and calls every endpoint. Standard library only."""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (method, path, body, expected status) — read-only first, destructive last; ids come from seed.py
CHECKS = [
    ("GET", "/health", None, 200),
    ("GET", "/", None, 200),
    ("GET", "/tasks", None, 200),
    ("GET", "/tasks/1", None, 200),
    ("GET", "/tasks/9999", None, 404),
    ("GET", "/tasks/search?q=API&status=pending", None, 200),
    ("GET", "/tasks/stats", None, 200),
    ("GET", "/users", None, 200),
    ("GET", "/users/1", None, 200),
    ("GET", "/users/1/tasks", None, 200),
    ("GET", "/reports/summary", None, 200),
    ("GET", "/reports/user/1", None, 200),
    ("GET", "/categories", None, 200),
    ("POST", "/login", {"email": "joao@email.com", "password": "1234"}, 200),
    ("POST", "/login", {"email": "joao@email.com", "password": "errada"}, 401),
    ("POST", "/tasks", {"title": "Nova task smoke", "description": "criada no teste", "priority": 2,
                        "user_id": 1, "category_id": 1, "due_date": "2030-01-01", "tags": ["a", "b"]}, 201),
    ("POST", "/tasks", {}, 400),
    ("POST", "/tasks", {"title": "Prioridade texto", "priority": "alta"}, 400),
    ("PUT", "/tasks/1", {"status": "in_progress", "priority": 2}, 200),
    ("POST", "/users", {"name": "Ana Teste", "email": "ana@email.com", "password": "senha123"}, 201),
    ("POST", "/users", {"name": "Dup", "email": "joao@email.com", "password": "senha123"}, 409),
    ("PUT", "/users/2", {"name": "Maria S."}, 200),
    ("POST", "/categories", {"name": "Docs", "color": "#ffffff"}, 201),
    ("PUT", "/categories/1", {"description": "Tarefas de backend (editado)"}, 200),
    ("DELETE", "/tasks/11", None, 200),
    ("DELETE", "/categories/5", None, 200),
    ("DELETE", "/users/4", None, 200),
]

# Paths whose JSON body must never carry the password hash
NO_PASSWORD_PATHS = {"/users", "/users/1", "/login", "/users/2"}


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def call(base, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def wait_until_up(base, server, attempts=75):
    for _ in range(attempts):
        if server.poll() is not None:
            raise RuntimeError("server exited before answering")
        try:
            urllib.request.urlopen(base + "/", timeout=1)
            return
        except urllib.error.HTTPError:
            return  # any HTTP answer means the server is up
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("server did not start")


def contains_password(raw):
    def walk(value):
        if isinstance(value, dict):
            return "password" in value or any(walk(v) for v in value.values())
        if isinstance(value, list):
            return any(walk(v) for v in value)
        return False
    return walk(json.loads(raw))


def main():
    port = free_port()
    workdir = tempfile.mkdtemp()
    env = {**os.environ, "PORT": str(port), "HOST": "127.0.0.1",
           "DATABASE_PATH": os.path.join(workdir, "smoke.db"), "SECRET_KEY": "smoke-secret"}
    subprocess.run([sys.executable, "seed.py"], cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)
    server = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    try:
        wait_until_up(base, server)
        failures = []
        for method, path, body, expected in CHECKS:
            status, raw = call(base, method, path, body)
            ok = status == expected
            if ok and status < 400 and path in NO_PASSWORD_PATHS and contains_password(raw):
                ok = False
                status = f"{status} with password in body"
            print(f"{'✓' if ok else '✗'} {method} {path} -> {status} (expected {expected})")
            if not ok:
                failures.append(f"{method} {path}")
        print(f"{len(CHECKS) - len(failures)}/{len(CHECKS)} checks passed")
        return 1 if failures else 0
    finally:
        server.terminate()
        server.wait(timeout=10)
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
