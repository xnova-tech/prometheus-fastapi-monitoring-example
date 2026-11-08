"""HTTP routes exposed by the example application."""

from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from prometheus_demo.metrics import Metrics


def create_router(metrics: Metrics) -> APIRouter:
    """Build routes around an explicitly supplied metrics registry."""
    router = APIRouter()

    @router.get("/", response_class=PlainTextResponse)
    def root() -> PlainTextResponse:
        return PlainTextResponse("demo: ok\n")

    @router.get("/error", response_class=PlainTextResponse)
    def controlled_error() -> PlainTextResponse:
        return PlainTextResponse("demo: controlled error\n", status_code=500)

    @router.get("/metrics", include_in_schema=False)
    def prometheus_metrics() -> Response:
        return Response(
            content=generate_latest(metrics.registry),
            headers={"Content-Type": CONTENT_TYPE_LATEST},
        )

    @router.get("/{path:path}", response_class=PlainTextResponse, include_in_schema=False)
    def not_found(path: str) -> PlainTextResponse:
        del path
        return PlainTextResponse("demo: not found\n", status_code=404)

    return router
