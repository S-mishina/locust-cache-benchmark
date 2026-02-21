def add_common_arguments(parser):
    """
    common arguments for loadtest
    """
    group = parser.add_argument_group("Common Arguments")
    group.add_argument(
        "--config", "-C",
        type=str,
        required=False,
        default=None,
        help="Path to YAML configuration file. Cannot be used with other CLI parameters.",
    )
    group.add_argument(
        "--fqdn", "-f",
        type=str,
        required=False,
        default="localhost",
        help="Specify the hostname of the Redis server (default: localhost)."
    )
    group.add_argument(
        "--port", "-p",
        type=int,
        required=False,
        default=6379,
        help="Specify the port of the Redis server (default: 6379)."
    )
    group.add_argument(
        "--ssl", "-x",
        type=str,
        required=False,
        default="false",
        help="Use SSL for the connection."
    )
    group.add_argument(
        "--query-timeout", "-q",
        type=int,
        required=False,
        default=1,
        help="Specify the query timeout in seconds (default: 1)."
    )
    group.add_argument(
        "--hit-rate", "-r",
        type=float,
        required=False,
        default=0.5,
        help="Specify the cache hit rate as a float between 0 and 1 (default: 0.5)."
    )
    group.add_argument(
        "--duration", "-d",
        type=int,
        required=False,
        default=60,
        help="Specify the duration of the test in seconds (default: 60)."
    )
    group.add_argument(
        "--connections", "-c",
        type=int,
        required=False,
        default=1,
        help="Specify the number of concurrent connections (default: 1)."
    )
    group.add_argument(
        "--spawn_rate", "-n",
        type=int,
        required=False,
        default=1,
        help="Specify the number of requests to send (default: 1)."
    )
    group.add_argument(
        "--value-size", "-k",
        type=int,
        required=False,
        default=1,
        help="Specify the size of the keys in KB (default: 1)."
    )
    group.add_argument(
        "--ttl", "-t",
        type=int,
        required=False,
        default=60,
        help="Specify the time-to-live for the keys in seconds (default: 60)."
    )
    group.add_argument(
        "--connections-pool", "-l",
        type=int,
        required=False,
        default=10,
        help="Specify the number of connections in the pool per user (default: 10)."
    )
    group.add_argument(
        "--retry-count", "-rc",
        type=int,
        required=False,
        default=3,
        help="Specify the number of retry attempts for cache operations (default: 3)."
    )
    group.add_argument(
        "--retry-wait", "-rw",
        type=int,
        required=False,
        default=2,
        help="Specify the maximum wait time (cap) for exponential backoff between retries in seconds (default: 2)."
    )
    group.add_argument(
        "--set-keys", "-s",
        type=int,
        required=False,
        default=1000,
        help="Specify the number of keys to set in the cache (default: 1000). ※init redis only parameter"
    )
    group.add_argument(
        "--cluster-mode", "-cm",
        type=str,
        required=False,
        default=None,
        help="Run the test in cluster mode. master or worker"
    )
    group.add_argument(
        "--master-bind-host", "-mbh",
        type=str,
        required=False,
        default="127.0.0.1",
        help="Specify the hostname of the master node (default: localhost)."
    )
    group.add_argument(
        "--master-bind-port", "-mbp",
        type=int,
        required=False,
        default=5557,
        help="Specify the port of the master node (default: 5557)."
    )
    group.add_argument(
        "--num-workers", "-nw",
        type=int,
        required=False,
        default=1,
        help="Specify the number of workers to connect to the master node (default: 1)."
    )
    group.add_argument(
        "--request-rate", "-rr",
        type=float,
        required=False,
        default=1.0,
        help="Specify the request rate per user per second (default: 1.0). Uses constant_throughput for precise rate control."
    )
    group.add_argument(
        "--otel-tracing-enabled",
        type=str,
        required=False,
        default="false",
        help="Enable OpenTelemetry tracing (default: false)."
    )
    group.add_argument(
        "--otel-metrics-enabled",
        type=str,
        required=False,
        default="false",
        help="Enable redis-py native OpenTelemetry metrics (default: false). Only supported for Redis backends.",
    )
    group.add_argument(
        "--otel-exporter-endpoint",
        type=str,
        required=False,
        default="http://localhost:4317",
        help="Specify the OTLP exporter endpoint (default: http://localhost:4317)."
    )
    group.add_argument(
        "--otel-service-name",
        type=str,
        required=False,
        default="locust-cache-benchmark",
        help="Specify the OpenTelemetry service name (default: locust-cache-benchmark)."
    )
    group.add_argument(
        "--cache-username",
        type=str,
        required=False,
        default=None,
        help="Username for cache authentication (ACL)."
    )
    group.add_argument(
        "--cache-password",
        type=str,
        required=False,
        default=None,
        help="Password for cache authentication."
    )
    group.add_argument(
        "--ssl-cert-reqs",
        type=str,
        required=False,
        default=None,
        choices=["none", "optional", "required"],
        help="SSL certificate verification mode (none/optional/required)."
    )
    group.add_argument(
        "--ssl-ca-certs",
        type=str,
        required=False,
        default=None,
        help="Path to CA certificate file for SSL verification."
    )
