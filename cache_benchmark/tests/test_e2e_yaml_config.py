"""E2E tests for YAML config file support.

These tests run the actual CLI (locust_cache_benchmark) via subprocess
against a real Redis container started by docker-compose.

Requires: Docker, docker-compose, poetry
Run:
    docker-compose -f docker-compose-redis-standalone.yml up -d
    poetry run pytest cache_benchmark/tests/test_e2e_yaml_config.py -v
    docker-compose -f docker-compose-redis-standalone.yml down
"""

import os
import shutil
import socket
import subprocess
import time

import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
COMPOSE_FILE = os.path.join(PROJECT_ROOT, "docker-compose-redis-standalone.yml")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


# ── Helpers ────────────────────────────────────────────────


def _fixture_path(name):
    """Return the absolute path to a fixture YAML file."""
    return os.path.join(FIXTURES_DIR, name)


def _run_cli(*args, env=None):
    """Run the CLI via poetry and return CompletedProcess."""
    cmd = ["poetry", "run", "locust_cache_benchmark", *args]
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env=run_env,
        timeout=120,
    )


def _wait_for_redis(host="127.0.0.1", port=6379, timeout=30):
    """Wait for Redis to respond to PING."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            sock = socket.create_connection((host, port), timeout=2)
            sock.sendall(b"*1\r\n$4\r\nPING\r\n")
            data = sock.recv(64)
            sock.close()
            if b"PONG" in data:
                return True
        except (ConnectionRefusedError, OSError, socket.timeout):
            pass
        time.sleep(1)
    return False


# ── Docker fixture (module scope) ──────────────────────────


@pytest.fixture(scope="module")
def redis_container():
    """Start Redis via docker-compose, wait for readiness, then tear down."""
    if not shutil.which("docker"):
        pytest.skip("docker command not found")

    probe = subprocess.run(
        ["docker", "info"], capture_output=True, timeout=10,
    )
    if probe.returncode != 0:
        pytest.skip("Docker daemon is not running")

    subprocess.run(
        ["docker-compose", "-f", COMPOSE_FILE, "up", "-d"],
        capture_output=True,
        cwd=PROJECT_ROOT,
        timeout=60,
    )

    if not _wait_for_redis():
        subprocess.run(
            ["docker-compose", "-f", COMPOSE_FILE, "down"],
            capture_output=True,
            cwd=PROJECT_ROOT,
        )
        pytest.fail("Redis did not become ready in time")

    yield

    subprocess.run(
        ["docker-compose", "-f", COMPOSE_FILE, "down"],
        capture_output=True,
        cwd=PROJECT_ROOT,
        timeout=60,
    )


# ── Tests requiring Docker ─────────────────────────────────


@pytest.mark.e2e
class TestYamlConfigWithRedis:
    """E2E tests that require a running Redis container."""

    def test_yaml_init(self, redis_container):
        """YAML config for init redis-standalone should succeed."""
        result = _run_cli(
            "init", "redis-standalone",
            "--config", _fixture_path("e2e_init.yaml"),
        )
        assert result.returncode == 0, (
            f"init failed (rc={result.returncode}):\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )

    def test_yaml_loadtest(self, redis_container):
        """YAML config for loadtest local redis-standalone should succeed."""
        # First: seed keys via init
        init_result = _run_cli(
            "init", "redis-standalone",
            "--config", _fixture_path("e2e_init.yaml"),
        )
        assert init_result.returncode == 0, (
            f"init failed (rc={init_result.returncode}):\n"
            f"stdout={init_result.stdout}\nstderr={init_result.stderr}"
        )

        # Then: run loadtest
        result = _run_cli(
            "loadtest", "local", "redis-standalone",
            "--config", _fixture_path("e2e_loadtest.yaml"),
        )
        assert result.returncode == 0, (
            f"loadtest failed (rc={result.returncode}):\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )

    def test_env_overrides_yaml(self, redis_container):
        """ENV CACHE_HOST=127.0.0.1 should override yaml host=wrong-host."""
        result = _run_cli(
            "init", "redis-standalone",
            "--config", _fixture_path("e2e_env_override.yaml"),
            env={"CACHE_HOST": "127.0.0.1"},
        )
        assert result.returncode == 0, (
            f"init with env override failed (rc={result.returncode}):\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )


# ── Tests NOT requiring Docker ─────────────────────────────


@pytest.mark.e2e
class TestYamlConfigValidation:
    """E2E tests for YAML config error handling (no Docker needed)."""

    def test_config_with_cli_params_rejected(self):
        """--config with other CLI params should be rejected."""
        result = _run_cli(
            "init", "redis-standalone",
            "--config", _fixture_path("e2e_cli_conflict.yaml"),
            "--port", "7000",
        )
        assert result.returncode != 0
        assert "Cannot use --config" in result.stderr

    def test_config_file_not_found(self):
        """--config with non-existent file should fail."""
        result = _run_cli(
            "init", "redis-standalone",
            "--config", "/nonexistent.yaml",
        )
        assert result.returncode != 0
        assert "Config file not found" in result.stderr

    def test_config_invalid_schema(self):
        """YAML with unknown keys should fail validation."""
        result = _run_cli(
            "init", "redis-standalone",
            "--config", _fixture_path("e2e_invalid_schema.yaml"),
        )
        assert result.returncode != 0
        assert "validation error" in result.stderr.lower()
