"""FastAPI application factory and request instrumentation."""

from time import perf_counter

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from prometheus_demo.metrics import Metrics, create_metrics
from prometheus_demo.routes import create_router


def create_app(metrics: Metrics | None = None) -> FastAPI:
    """Create one app with an isolated metrics registry."""
    app_metrics = metrics or create_metrics()
    application = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @application.middleware("http")
    async def instrument_request(request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        started = perf_counter()
        response = await call_next(request)
        route = request.url.path if request.url.path in {"/", "/error"} else "other"
        app_metrics.observe(
            route=route,
            status=response.status_code,
            duration_seconds=perf_counter() - started,
        )
        return response

    application.include_router(create_router(app_metrics))
    return application


app = create_app()
