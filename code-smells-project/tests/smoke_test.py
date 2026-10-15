"""Smoke test: boots the app on a free port with a temporary database and calls every endpoint.

Run with: python tests/smoke_test.py   (standard library only)
"""
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
ADMIN_TOKEN = "smoke-test-token"

PRODUTO = {"nome": "Produto Teste", "descricao": "Criado no smoke test", "preco": 10.5,
           "estoque": 5, "categoria": "geral"}
PRODUTO_ATUALIZADO = {**PRODUTO, "nome": "Produto Teste 2", "preco": 12.0}
ADMIN = {"X-Admin-Token": ADMIN_TOKEN}

# (method, path, body, headers, expected status) — same requests as the baseline;
# read-only first, destructive last.
CHECKS = [
    ("GET", "/", None, None, 200),
    ("GET", "/produtos", None, None, 200),
    ("GET", "/produtos/busca?q=Mouse", None, None, 200),
    ("GET", "/produtos/1", None, None, 200),
    ("GET", "/usuarios", None, None, 200),
    ("GET", "/usuarios/1", None, None, 200),
    ("GET", "/pedidos", None, None, 200),
    ("GET", "/pedidos/usuario/2", None, None, 200),
    ("GET", "/relatorios/vendas", None, None, 200),
    ("GET", "/health", None, None, 200),
    ("POST", "/produtos", PRODUTO, None, 201),
    ("PUT", "/produtos/11", PRODUTO_ATUALIZADO, None, 200),
    ("POST", "/usuarios", {"nome": "Ana Teste", "email": "ana@teste.com", "senha": "segredo1"}, None, 201),
    ("POST", "/login", {"email": "joao@email.com", "senha": "123456"}, None, 200),
    ("POST", "/login", {"email": "ana@teste.com", "senha": "segredo1"}, None, 200),
    ("POST", "/login", {"email": "joao@email.com", "senha": "errada"}, None, 401),
    ("POST", "/login", {"email": "' OR '1'='1", "senha": "' OR '1'='1"}, None, 401),
    ("POST", "/pedidos", {"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": 1}]}, None, 201),
    ("POST", "/pedidos", {"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": -5}]}, None, 400),
    ("GET", "/pedidos/usuario/2", None, None, 200),
    ("PUT", "/pedidos/1/status", {"status": "aprovado"}, None, 200),
    ("DELETE", "/produtos/11", None, None, 200),
    ("GET", "/produtos/11", None, None, 404),
    ("POST", "/admin/query", {"sql": "SELECT id, nome FROM produtos"}, None, 401),
    ("POST", "/admin/query", {"sql": "SELECT id, nome FROM produtos"}, {"X-Admin-Token": "wrong"}, 403),
    ("POST", "/admin/query", {"sql": "SELECT id, nome FROM produtos"}, ADMIN, 200),
    ("POST", "/admin/query", {"sql": "DELETE FROM produtos"}, ADMIN, 400),
    ("POST", "/admin/reset-db", None, None, 401),
    ("POST", "/admin/reset-db", None, ADMIN, 200),
]

FORBIDDEN_FIELDS = {
    "/usuarios": ("senha",),
    "/usuarios/1": ("senha",),
    "/health": ("secret_key", "db_path", "debug"),
}


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def call(base, method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def wait_until_up(base, server, attempts=75):
    for _ in range(attempts):
        if server.poll() is not None:
            raise RuntimeError("server exited during startup")
        try:
            urllib.request.urlopen(base + "/", timeout=1)
            return
        except urllib.error.HTTPError:
            return                      # any HTTP answer means the server is up
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("server did not start")


def leaked_fields(path, raw):
    forbidden = FORBIDDEN_FIELDS.get(path)
    if not forbidden:
        return []
    payload = json.loads(raw)
    records = payload.get("dados", payload)
    records = records if isinstance(records, list) else [records]
    return [field for record in records for field in forbidden if field in record]


def main():
    port = free_port()
    workdir = tempfile.mkdtemp()
    env = {**os.environ, "PORT": str(port), "HOST": "127.0.0.1",
           "DATABASE_PATH": os.path.join(workdir, "smoke.db"),
           "ADMIN_TOKEN": ADMIN_TOKEN, "SECRET_KEY": "smoke-secret", "FLASK_DEBUG": "0"}
    server = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    failures = []
    try:
        wait_until_up(base, server)
        for method, path, body, headers, expected in CHECKS:
            status, raw = call(base, method, path, body, headers)
            leaks = leaked_fields(path, raw) if status == 200 else []
            ok = status == expected and not leaks
            note = f" leaked {leaks}" if leaks else ""
            print(f"{'✓' if ok else '✗'} {method} {path} -> {status} (expected {expected}){note}")
            if not ok:
                failures.append(f"{method} {path}")
        print(f"{len(CHECKS) - len(failures)}/{len(CHECKS)} checks passed")
        return 1 if failures else 0
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
