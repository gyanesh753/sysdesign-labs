#!/usr/bin/env python3
"""
Environment check for sysdesign-labs. Prints one line per check and tells you how to fix failures.

    python verify_setup.py             # everything
    python verify_setup.py python      # Python version, packages, smoke tests
    python verify_setup.py tools       # git, docker, docker compose
    python verify_setup.py services    # Postgres, Redpanda, S3 store, Toxiproxy (after: docker compose up -d)
    python verify_setup.py ollama      # local models

Exit code is 1 if any required check fails.
"""
import importlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECTIONS = set(sys.argv[1:]) or {"python", "tools", "services", "ollama"}
RESULTS = []
OLLAMA_MODELS = ["qwen3.5:9b", "nomic-embed-text"]


def load_env():
    env = {}
    for name in (".env.example", ".env"):  # .env overrides the example
        path = ROOT / name
        if path.exists():
            for line in path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env[key.strip()] = value.strip()
    env.update({k: v for k, v in os.environ.items() if k in env})  # real env vars win
    return env


ENV = load_env()


def run(section, name, fn, hint="", optional=False):
    if section not in SECTIONS:
        return
    try:
        detail, status = (fn() or ""), "ok"
    except Exception as exc:  # noqa: BLE001 - we want to report any failure
        detail, status = f"{type(exc).__name__}: {str(exc).strip()[:220]}", ("warn" if optional else "fail")
    RESULTS.append(status)
    tag = {"ok": "[ ok ]", "warn": "[warn]", "fail": "[FAIL]"}[status]
    print(f"{tag} {name}" + (f" - {detail}" if detail else ""))
    if status != "ok" and hint:
        print(f"       fix: {hint}")


def sh(cmd, timeout=20):
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    text = (out.stdout or "").strip()
    if out.returncode != 0:
        err = (out.stderr or out.stdout or "").strip().splitlines()
        raise RuntimeError(err[-1] if err else f"exit code {out.returncode}")
    return text


def need_port(port, host="127.0.0.1"):
    try:
        socket.create_connection((host, port), timeout=2).close()
    except OSError:
        raise RuntimeError(f"nothing is listening on {host}:{port}")


def http(url, body=None, timeout=5):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode()


# ---------------------------------------------------------------- python
def check_python_version():
    if sys.version_info < (3, 11):
        raise RuntimeError(f"found {sys.version.split()[0]}, need 3.11 or newer")
    return sys.version.split()[0]


def check_venv():
    if sys.prefix == sys.base_prefix:
        raise RuntimeError("no virtual environment is active")
    return sys.prefix


def import_check(module):
    def check():
        mod = importlib.import_module(module)
        version = getattr(mod, "__version__", "")
        return str(version) if isinstance(version, str) else ""
    return check


def smoke_duckdb():
    import duckdb
    assert duckdb.connect().execute("SELECT 6 * 7").fetchone()[0] == 42
    return "SQL works"


def smoke_parquet():
    import duckdb
    import pandas as pd
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "t.parquet").replace("\\", "/")
        duckdb.sql(f"COPY (SELECT 1 AS a, 'x' AS b) TO '{path}' (FORMAT parquet)")
        assert pd.read_parquet(path).shape == (1, 2)
    return "Parquet write and read work"


def smoke_hnsw():
    import hnswlib
    import numpy as np
    data = np.random.default_rng(0).random((200, 16), dtype="float32")
    index = hnswlib.Index(space="cosine", dim=16)
    index.init_index(max_elements=200, ef_construction=100, M=16)
    index.add_items(data, np.arange(200))
    labels, _ = index.knn_query(data[:1], k=3)
    assert labels[0][0] == 0
    return "HNSW index build and query work"


run("python", "Python 3.11 or newer", check_python_version, "uv venv --python 3.12 .venv")
run("python", "virtual environment active", check_venv, "source .venv/bin/activate", optional=True)
PACKAGES = [
    ("duckdb", "duckdb"), ("pandas", "pandas"), ("numpy", "numpy"), ("pyarrow", "pyarrow"),
    ("matplotlib", "matplotlib"), ("networkx", "networkx"), ("hnswlib", "hnswlib"),
    ("rank_bm25", "rank-bm25"), ("psycopg", "psycopg[binary]"), ("confluent_kafka", "confluent-kafka"),
    ("boto3", "boto3"), ("requests", "requests"), ("ollama", "ollama"), ("pytest", "pytest"),
]
for module, pip_name in PACKAGES:
    run("python", f"import {module}", import_check(module), f"uv pip install -r requirements.txt  (missing: {pip_name})")
run("python", "DuckDB smoke test", smoke_duckdb, "reinstall: uv pip install --force-reinstall duckdb")
run("python", "Parquet smoke test", smoke_parquet, "uv pip install pyarrow")
run("python", "HNSW smoke test", smoke_hnsw, "macOS: xcode-select --install, then uv pip install hnswlib")


# ---------------------------------------------------------------- tools
def check_git():
    if not shutil.which("git"):
        raise RuntimeError("git not found")
    return sh(["git", "--version"])


def check_git_identity():
    def get(key):
        return subprocess.run(["git", "config", key], capture_output=True, text=True).stdout.strip()
    name, email = get("user.name"), get("user.email")
    if not name or not email:
        raise RuntimeError("user.name and/or user.email not set")
    return f"{name} <{email}>"


def check_docker_cli():
    if not shutil.which("docker"):
        raise RuntimeError("docker command not found")
    return sh(["docker", "--version"])


def check_docker_daemon():
    return "daemon running, server " + sh(["docker", "info", "--format", "{{.ServerVersion}}"])


def check_compose():
    return "docker compose " + sh(["docker", "compose", "version", "--short"])


run("tools", "git installed", check_git, "macOS: xcode-select --install")
run("tools", "git identity set", check_git_identity,
    'git config --global user.name "Your Name" && git config --global user.email "you@example.com"')
run("tools", "docker installed", check_docker_cli, "install Docker Desktop (docker.com/products/docker-desktop)")
run("tools", "docker daemon running", check_docker_daemon, "open Docker Desktop and wait until it says Engine running")
run("tools", "docker compose available", check_compose, "update Docker Desktop")


# ---------------------------------------------------------------- services
FIX_UP = "docker compose up -d   (then: docker compose logs <service> if it still fails)"


def check_postgres():
    port = int(ENV.get("POSTGRES_PORT", "5432"))
    need_port(port)
    import psycopg
    with psycopg.connect(host="127.0.0.1", port=port, user=ENV.get("POSTGRES_USER", "lab"),
                         password=ENV.get("POSTGRES_PASSWORD", "lab"), dbname=ENV.get("POSTGRES_DB", "lab"),
                         connect_timeout=5) as conn:
        version = conn.execute("SHOW server_version").fetchone()[0]
        wal = conn.execute("SHOW wal_level").fetchone()[0]
    if wal != "logical":
        raise RuntimeError(f"connected to PostgreSQL {version} but wal_level={wal}; is another Postgres using this port?")
    return f"PostgreSQL {version}, wal_level=logical"


def check_redpanda():
    bootstrap = ENV.get("KAFKA_BOOTSTRAP", "localhost:19092")
    need_port(int(bootstrap.rsplit(":", 1)[1]))
    from confluent_kafka import Consumer, Producer
    from confluent_kafka.admin import AdminClient, NewTopic

    topic = "verify-setup"
    admin = AdminClient({"bootstrap.servers": bootstrap})
    if topic not in admin.list_topics(timeout=10).topics:
        for future in admin.create_topics([NewTopic(topic, num_partitions=1, replication_factor=1)]).values():
            try:
                future.result(timeout=15)
            except Exception as exc:  # noqa: BLE001
                if "exist" not in str(exc).lower():
                    raise
    payload = uuid.uuid4().hex.encode()
    outcome = []
    producer = Producer({"bootstrap.servers": bootstrap})
    producer.produce(topic, payload, callback=lambda err, msg: outcome.append(err))
    if producer.flush(15) > 0 or not outcome or outcome[0] is not None:
        raise RuntimeError(f"produce failed: {outcome}")
    consumer = Consumer({"bootstrap.servers": bootstrap, "group.id": "verify-" + uuid.uuid4().hex[:8],
                         "auto.offset.reset": "earliest", "enable.auto.commit": False})
    consumer.subscribe([topic])
    deadline, got = time.time() + 20, False
    while time.time() < deadline and not got:
        msg = consumer.poll(1.0)
        got = msg is not None and not msg.error() and msg.value() == payload
    consumer.close()
    if not got:
        raise RuntimeError("message was produced but not consumed within 20s")
    return "produce and consume round trip works"


def check_s3():
    need_port(9000)
    import boto3
    from botocore.config import Config
    s3 = boto3.client(
        "s3", endpoint_url="http://127.0.0.1:9000", region_name="us-east-1",
        aws_access_key_id=ENV.get("RUSTFS_ACCESS_KEY", "labaccesskey"),
        aws_secret_access_key=ENV.get("RUSTFS_SECRET_KEY", "labsecretkey123"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"},
                      retries={"max_attempts": 1}, connect_timeout=5, read_timeout=15,
                      request_checksum_calculation="when_required", response_checksum_validation="when_required"),
    )
    bucket = "lab-verify"
    if bucket not in [b["Name"] for b in s3.list_buckets().get("Buckets", [])]:
        s3.create_bucket(Bucket=bucket)
    s3.put_object(Bucket=bucket, Key="hello.txt", Body=b"hello")
    body = s3.get_object(Bucket=bucket, Key="hello.txt")["Body"].read()
    s3.delete_object(Bucket=bucket, Key="hello.txt")
    if body != b"hello":
        raise RuntimeError("read back different bytes than were written")
    return "S3 API works (create bucket, put, get, delete)"


def check_toxiproxy():
    need_port(8474)
    return "Toxiproxy " + http("http://127.0.0.1:8474/version").strip()


run("services", "Postgres (localhost:5432)", check_postgres, FIX_UP)
run("services", "Redpanda / Kafka API (localhost:19092)", check_redpanda, FIX_UP)
run("services", "S3-compatible store (localhost:9000)", check_s3, FIX_UP)
run("services", "Toxiproxy (localhost:8474)", check_toxiproxy, FIX_UP)


# ---------------------------------------------------------------- ollama
def ollama_host():
    return ENV.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def installed_models():
    return [m["name"] for m in json.loads(http(f"{ollama_host()}/api/tags")).get("models", [])]


def check_ollama_server():
    return f"running, {len(installed_models())} model(s) installed"


def check_ollama_models():
    have = installed_models()
    missing = [m for m in OLLAMA_MODELS if not any(h == m or h.startswith(m + ":") for h in have)]
    if missing:
        raise RuntimeError("missing: " + ", ".join(missing))
    return ", ".join(OLLAMA_MODELS)


def check_ollama_generate():
    reply = json.loads(http(f"{ollama_host()}/api/generate", {
        "model": OLLAMA_MODELS[0], "prompt": "Reply with the single word: ready", "stream": False,
        "options": {"num_predict": 12}}, timeout=180))
    return "model replied: " + reply.get("response", "").strip()[:40]


def check_ollama_embed():
    reply = json.loads(http(f"{ollama_host()}/api/embed", {"model": OLLAMA_MODELS[1], "input": "hello"}, timeout=60))
    return f"embedding vector has {len(reply['embeddings'][0])} dimensions"


run("ollama", "Ollama server", check_ollama_server, "open the Ollama app (menu bar icon), or run: ollama serve", optional=True)
run("ollama", "Ollama models pulled", check_ollama_models, "ollama pull llama3.2:3b && ollama pull nomic-embed-text", optional=True)
run("ollama", "Ollama chat works", check_ollama_generate, "if memory is tight, close other apps or pull a smaller model", optional=True)
run("ollama", "Ollama embeddings work", check_ollama_embed, "ollama pull nomic-embed-text", optional=True)

# ---------------------------------------------------------------- summary
fails, warns = RESULTS.count("fail"), RESULTS.count("warn")
print()
if fails:
    print(f"{fails} required check(s) failed. Fix the lines marked [FAIL], then run this again.")
    sys.exit(1)
print("All required checks passed" + (f" ({warns} optional warning(s) above)." if warns else "."))
