"""FastAPI monitoring example used by the Prometheus article."""

from prometheus_demo.app import create_app

__all__ = ["create_app"]
