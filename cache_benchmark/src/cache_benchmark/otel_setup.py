import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.redis import RedisInstrumentor
from cache_benchmark.config import get_config

logger = logging.getLogger(__name__)

_otel_initialized = False


def setup_otel_tracing():
    """
    Initialize OpenTelemetry tracing with RedisInstrumentor.

    Reads otel_tracing_enabled from AppConfig to determine
    whether to enable tracing. When enabled, configures a
    TracerProvider with BatchSpanProcessor and OTLPSpanExporter,
    then instruments redis-py via RedisInstrumentor.

    Returns:
        bool: True if tracing was successfully initialized, False otherwise.
    """
    global _otel_initialized

    if _otel_initialized:
        logger.debug("OpenTelemetry tracing already initialized, skipping.")
        return True

    cfg = get_config()
    if not cfg.otel_tracing_enabled:
        logger.debug("OpenTelemetry tracing is disabled.")
        return False

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

        _otel_initialized = True
        logger.info(
            "OpenTelemetry tracing initialized (service=%s, endpoint=%s).",
            service_name,
            endpoint,
        )
        return True
    except (ConnectionError, OSError, ValueError):
        logger.exception("Failed to initialize OpenTelemetry tracing.")
        return False


def shutdown_otel_tracing():
    """
    Flush and shut down the OpenTelemetry TracerProvider.

    Returns:
        bool: True if shutdown was successful, False otherwise.
    """
    global _otel_initialized

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
