def add_common_arguments(parser):
    """
    common arguments for loadtest
    """
    group = parser.add_argument_group("Common Arguments")
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
        type=bool,
        required=False,
        default=False,
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
        default=1000000,
        help="Specify the number of connections in the pool (default: 1000000)."
    )
    group.add_argument(
        "--retry-count", "-rc",
        type=int,
        required=False,
        default=3,
        help="Specify the number of retries in case of failure (default: 3)."
    )
    group.add_argument(
        "--retry-wait", "-rw",
        type=int,
        required=False,
        default=2,
        help="Specify the wait time between retries in seconds (default: 2)."
    )
    group.add_argument(
        "--set-keys", "-s",
        type=int,
        required=False,
        default=1000,
        help="Specify the number of keys to set in the cache (default: 1000). ※init redis only parameter"
    )
