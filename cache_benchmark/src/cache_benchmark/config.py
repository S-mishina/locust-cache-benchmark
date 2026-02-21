import json
import os
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _strtobool(val):
    val = str(val).strip().lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError(f"invalid truth value {val!r}")


# ── CLI arg name → field name mapping ─────────────────
_ARG_MAP: dict[str, str] = {
    "fqdn": "cache_host",
    "port": "cache_port",
    "ssl": "ssl",
    "query_timeout": "query_timeout",
    "connections_pool": "connections_pool",
    "hit_rate": "hit_rate",
    "value_size": "value_size",
    "ttl": "ttl",
    "request_rate": "request_rate",
    "set_keys": "set_keys",
    "retry_count": "retry_attempts",
    "retry_wait": "retry_wait",
    "otel_tracing_enabled": "otel_tracing_enabled",
    "otel_metrics_enabled": "otel_metrics_enabled",
    "otel_exporter_endpoint": "otel_exporter_endpoint",
    "otel_service_name": "otel_service_name",
    "duration": "duration",
    "connections": "connections",
    "spawn_rate": "spawn_rate",
    "cluster_mode": "cluster_mode",
    "master_bind_host": "master_bind_host",
    "master_bind_port": "master_bind_port",
    "num_workers": "num_workers",
    "cache_username": "cache_username",
    "cache_password": "cache_password",
    "ssl_cert_reqs": "ssl_cert_reqs",
    "ssl_ca_certs": "ssl_ca_certs",
}

# ── Field name → env var name (only where it differs from field.upper()) ──
_FIELD_ENV_OVERRIDE: dict[str, str] = {
    "otel_exporter_endpoint": "OTEL_EXPORTER_OTLP_ENDPOINT",
}


def _env_key(field_name: str) -> str:
    """Return the environment variable name for a given field name."""
    return _FIELD_ENV_OVERRIDE.get(field_name, field_name.upper())


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AppConfig
#
#  1 field = default + type + validation + description
#  Env var names resolved via _env_key() (mostly FIELD_NAME.upper())
#  CLI arg names resolved via _ARG_MAP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AppConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    # ── Connection ──────────────────────────────────────────
    cache_host: str = Field(
        default="localhost",
        description="Cache server hostname",
    )
    cache_port: int = Field(
        default=6379,
        ge=1, le=65535,
        description="Cache server port",
    )
    ssl: bool = Field(
        default=False,
        description="Use SSL for connection",
    )
    ssl_cert_reqs: Optional[Literal["none", "optional", "required"]] = Field(
        default=None,
        description="SSL certificate verification mode (none/optional/required)",
    )
    ssl_ca_certs: Optional[str] = Field(
        default=None,
        description="Path to CA certificate file for SSL verification",
    )
    cache_username: Optional[str] = Field(
        default=None,
        description="Username for cache authentication (ACL)",
    )
    cache_password: Optional[str] = Field(
        default=None,
        description="Password for cache authentication",
    )
    query_timeout: int = Field(
        default=1,
        ge=0,
        description="Query timeout in seconds",
    )
    connections_pool: int = Field(
        default=10,
        ge=1,
        description="Connection pool size per user",
    )
    cache_type: Literal["redis_cluster", "valkey_cluster", "redis", "valkey"] = Field(
        default="redis_cluster",
        description="Cache backend type",
    )

    # ── Test parameters ─────────────────────────────────────
    hit_rate: float = Field(
        default=0.5,
        ge=0.0, le=1.0,
        description="Cache hit rate (0.0 - 1.0)",
    )
    value_size: int = Field(
        default=1,
        ge=1,
        description="Value size in KB",
    )
    ttl: int = Field(
        default=60,
        ge=1,
        description="Time-to-live for keys in seconds",
    )
    request_rate: float = Field(
        default=1.0,
        gt=0,
        description="Requests per user per second",
    )
    set_keys: int = Field(
        default=1000,
        ge=1,
        description="Number of keys to populate in cache",
    )

    # ── Retry ───────────────────────────────────────────────
    retry_attempts: int = Field(
        default=3,
        ge=0,
        description="Number of retry attempts on failure",
    )
    retry_wait: int = Field(
        default=2,
        ge=0,
        description="Wait time between retries in seconds",
    )

    # ── OpenTelemetry ───────────────────────────────────────
    otel_tracing_enabled: bool = Field(
        default=False,
        description="Enable OpenTelemetry tracing",
    )
    otel_exporter_endpoint: str = Field(
        default="http://localhost:4317",
        description="OTLP exporter endpoint URL (env: OTEL_EXPORTER_OTLP_ENDPOINT)",
    )
    otel_service_name: str = Field(
        default="locust-cache-benchmark",
        description="OpenTelemetry service name",
    )
    otel_metrics_enabled: bool = Field(
        default=False,
        description="Enable redis-py native OpenTelemetry metrics (Redis only, not Valkey)",
    )

    # ── Locust runner ───────────────────────────────────────
    duration: int = Field(
        default=60,
        ge=1,
        description="Test duration in seconds",
    )
    connections: int = Field(
        default=1,
        ge=1,
        description="Number of concurrent connections",
    )
    spawn_rate: int = Field(
        default=1,
        ge=1,
        description="Spawn rate (users per second)",
    )
    cluster_mode: Optional[Literal["master", "worker"]] = Field(
        default=None,
        description="Cluster mode: master or worker",
    )
    master_bind_host: str = Field(
        default="127.0.0.1",
        description="Master node bind hostname",
    )
    master_bind_port: int = Field(
        default=5557,
        ge=1, le=65535,
        description="Master node bind port",
    )
    num_workers: int = Field(
        default=1,
        ge=1,
        description="Number of workers",
    )

    # ── Validators ──────────────────────────────────────────

    @field_validator("ssl", "otel_tracing_enabled", "otel_metrics_enabled", mode="before")
    @classmethod
    def _coerce_bool(cls, v):
        if isinstance(v, str):
            return _strtobool(v)
        return v

    @model_validator(mode="after")
    def _check_cluster_deps(self):
        if self.cluster_mode in ("master", "worker") and not self.master_bind_host:
            raise ValueError(
                f"master_bind_host is required when cluster_mode is '{self.cluster_mode}'"
            )
        return self

    # ── Factory: CLI args + env vars ─────────────────────────

    @classmethod
    def from_args(cls, args, cache_type: str = "redis_cluster") -> "AppConfig":
        """Build config with priority: env var > CLI arg > default."""
        kwargs: dict = {}

        # cache_type (determined by subcommand, not CLI arg)
        env_cache = os.environ.get("CACHE_TYPE")
        kwargs["cache_type"] = env_cache if env_cache is not None else cache_type

        # Each field: use env var if set, otherwise CLI arg
        for arg_name, field_name in _ARG_MAP.items():
            env_val = os.environ.get(_env_key(field_name))
            if env_val is not None:
                kwargs[field_name] = env_val
            elif hasattr(args, arg_name):
                kwargs[field_name] = getattr(args, arg_name)

        return cls(**kwargs)

    # ── JSON ────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return self.model_dump()

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        return cls.model_validate(data)

    @classmethod
    def from_json(cls, json_str: str) -> "AppConfig":
        return cls.model_validate_json(json_str)

    # ── JSON Schema ─────────────────────────────────────────

    @classmethod
    def json_schema(cls) -> dict:
        return cls.model_json_schema()

    @classmethod
    def json_schema_string(cls, indent: int = 2) -> str:
        return json.dumps(cls.model_json_schema(), indent=indent, ensure_ascii=False)


# ── Singleton ────────────────────────────────────────────

_config: Optional[AppConfig] = None


def set_config(config: AppConfig) -> None:
    global _config
    _config = config


def get_config() -> AppConfig:
    if _config is None:
        raise RuntimeError("AppConfig has not been initialized. Call set_config() first.")
    return _config


def reset_config() -> None:
    global _config
    _config = None
