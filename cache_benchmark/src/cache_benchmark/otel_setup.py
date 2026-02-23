import logging
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.redis import RedisInstrumentor
from redis.observability.providers import get_observability_instance
from redis.observability.config import OTelConfig, MetricGroup
from cache_benchmark.config import get_config

logger = logging.getLogger(__name__)

_otel_initialized = False
_metrics_initialized = False

_DEFAULT_OTEL_ENDPOINT = "http://localhost:4317"


def setup_otel_metrics():
    """
    Initialize redis-py native OpenTelemetry metrics.

    Uses redis.observability to collect command duration, connection pool,
    and error metrics. Only supported for Redis backends (not Valkey).

    Returns:
        bool: True if metrics were successfully initialized, False otherwise.
    """
    global _metrics_initialized

    if _metrics_initialized:
        return True

    cfg = get_config()
    if not cfg.otel_metrics_enabled:
        return False

    if cfg.cache_type in ("valkey", "valkey_cluster"):
        logger.warning(
            "OTel native metrics are only supported for Redis backends. Skipping."
        )
        return False

    if cfg.otel_exporter_endpoint == _DEFAULT_OTEL_ENDPOINT:
        logger.warning(
            "OTel metrics enabled but exporter endpoint is the default (%s). "
            "Ensure an OTel Collector is running at this address, "
            "or set --otel-exporter-endpoint to your collector's address.",
            _DEFAULT_OTEL_ENDPOINT,
        )

    try:
        resource = Resource.create({"service.name": cfg.otel_service_name})
        exporter = OTLPMetricExporter(
            endpoint=cfg.otel_exporter_endpoint, insecure=True
        )
        reader = PeriodicExportingMetricReader(exporter=exporter)
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(provider)

        otel = get_observability_instance()
        otel.init(
            OTelConfig(
                metric_groups=[
                    MetricGroup.COMMAND,
                    MetricGroup.CONNECTION_BASIC,
                    MetricGroup.RESILIENCY,
                ]
            )
        )

        _metrics_initialized = True
        logger.info(
            "redis-py native OTel metrics initialized (service=%s)",
            cfg.otel_service_name,
        )
        return True
    except Exception:
        logger.exception("Failed to initialize redis-py native OTel metrics.")
        return False


def shutdown_otel_metrics():
    """
    Shut down the redis-py native OpenTelemetry metrics.

    Returns:
        bool: True if shutdown was successful, False otherwise.
    """
    global _metrics_initialized

    if not _metrics_initialized:
        return False

    try:
        otel = get_observability_instance()
        otel.shutdown()

        provider = metrics.get_meter_provider()
        if hasattr(provider, "shutdown"):
            provider.shutdown()

        _metrics_initialized = False
        logger.info("redis-py native OTel metrics shut down.")
        return True
    except Exception:
        logger.exception("Failed to shut down redis-py native OTel metrics.")
        return False


_valkey_instrumented = False


def _instrument_valkey():
    """
    Instrument valkey-py to produce spans equivalent to RedisInstrumentor.

    Wraps execute_command on Valkey and ValkeyCluster so that each command
    (GET, SET, PING, etc.) generates a span with db.system=valkey.
    """
    global _valkey_instrumented
    if _valkey_instrumented:
        return

    from valkey import Valkey
    from valkey.cluster import ValkeyCluster

    _tracer = trace.get_tracer("locust-cache-benchmark")

    def _wrap(original):
        def wrapper(self, *args, **kwargs):
            command = args[0] if args else "UNKNOWN"
            with _tracer.start_as_current_span(command, kind=trace.SpanKind.CLIENT) as span:
                span.set_attribute("db.system", "valkey")
                span.set_attribute("db.statement", " ".join(str(a) for a in args))
                try:
                    return original(self, *args, **kwargs)
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        return wrapper

    Valkey.execute_command = _wrap(Valkey.execute_command)
    ValkeyCluster.execute_command = _wrap(ValkeyCluster.execute_command)
    _valkey_instrumented = True
    logger.info("Valkey command tracing instrumented.")


def setup_otel_tracing():
    """
    Initialize OpenTelemetry tracing with RedisInstrumentor.

    Reads otel_tracing_enabled from AppConfig to determine
    whether to enable tracing. When enabled, configures a
    TracerProvider with BatchSpanProcessor and OTLPSpanExporter,
    then instruments redis-py via RedisInstrumentor and
    valkey-py via _instrument_valkey().

    After tracing setup, also attempts to initialize native metrics
    via setup_otel_metrics().

    Returns:
        bool: True if tracing was successfully initialized, False otherwise.
    """
    global _otel_initialized

    if _otel_initialized:
        logger.debug("OpenTelemetry tracing already initialized, skipping.")
        setup_otel_metrics()
        return True

    cfg = get_config()
    if not cfg.otel_tracing_enabled:
        logger.debug("OpenTelemetry tracing is disabled.")
        setup_otel_metrics()
        return False

    if cfg.otel_exporter_endpoint == _DEFAULT_OTEL_ENDPOINT:
        logger.warning(
            "OTel tracing enabled but exporter endpoint is the default (%s). "
            "Ensure an OTel Collector is running at this address, "
            "or set --otel-exporter-endpoint to your collector's address.",
            _DEFAULT_OTEL_ENDPOINT,
        )

    try:
        service_name = cfg.otel_service_name
        endpoint = cfg.otel_exporter_endpoint

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        RedisInstrumentor().instrument()
        _instrument_valkey()

        _otel_initialized = True
        logger.info(
            "OpenTelemetry tracing initialized (service=%s, endpoint=%s).",
            service_name,
            endpoint,
        )

        setup_otel_metrics()

        return True
    except (ConnectionError, OSError, ValueError):
        logger.exception("Failed to initialize OpenTelemetry tracing.")
        return False


def shutdown_otel_tracing():
    """
    Flush and shut down the OpenTelemetry TracerProvider.

    Also shuts down native metrics via shutdown_otel_metrics() first.

    Returns:
        bool: True if shutdown was successful, False otherwise.
    """
    global _otel_initialized

    shutdown_otel_metrics()

    if not _otel_initialized:
        return False

    try:
        provider = trace.get_tracer_provider()
        if hasattr(provider, "force_flush"):
            provider.force_flush()
        if hasattr(provider, "shutdown"):
            provider.shutdown()

        _otel_initialized = False
        logger.info("OpenTelemetry tracing shut down successfully.")
        return True
    except (OSError, TimeoutError):
        logger.exception("Failed to shut down OpenTelemetry tracing.")
        return False
