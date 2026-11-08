"""Prometheus instruments and bounded label values."""

from dataclasses import dataclass

from prometheus_client import CollectorRegistry, Counter, Histogram

REQUEST_ROUTES = (("/", "200"), ("/error", "500"), ("other", "404"))
HISTOGRAM_BUCKETS = (0.005, 0.025, 0.1, 0.5, 1.0)


@dataclass(frozen=True, slots=True)
class Metrics:
    """All metrics owned by one application instance."""

    registry: CollectorRegistry
    requests: Counter
    duration: Histogram

    def observe(self, *, route: str, status: int, duration_seconds: float) -> None:
        """Record one completed user-facing request."""
        self.requests.labels(route=route, status=str(status)).inc()
        self.duration.labels(route=route).observe(duration_seconds)


def create_metrics() -> Metrics:
    """Create an isolated registry, convenient for tests and one process."""
    registry = CollectorRegistry()
    requests = Counter(
        "demo_http_requests",
        "Total HTTP requests handled by the demo app.",
        ("route", "status"),
        registry=registry,
    )
    duration = Histogram(
        "demo_http_request_duration_seconds",
        "Duration of demo HTTP requests in seconds.",
        ("route",),
        buckets=HISTOGRAM_BUCKETS,
        registry=registry,
    )
    for route, status in REQUEST_ROUTES:
        requests.labels(route=route, status=status)
        duration.labels(route=route)
    return Metrics(registry=registry, requests=requests, duration=duration)
