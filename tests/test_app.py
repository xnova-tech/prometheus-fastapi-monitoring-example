"""HTTP and Prometheus regression tests for the FastAPI example."""

import asyncio
from collections.abc import Iterable, Mapping

import httpx
import pytest
from prometheus_client import CONTENT_TYPE_LATEST
from prometheus_client.metrics_core import Metric
from prometheus_client.samples import Sample

from prometheus_demo import create_app
from prometheus_demo.config import Settings


def test_http_responses_and_bounded_labels() -> None:
    asyncio.run(check_http_responses_and_bounded_labels())


async def check_http_responses_and_bounded_labels() -> None:
    async with app_client() as client:
        await assert_response(client, "/", 200, "demo: ok\n")
        await assert_response(client, "/error", 500, "demo: controlled error\n")
        await assert_response(client, "/missing?user=sample", 404, "demo: not found\n")

        samples = await scrape_samples(client)
        assert sample_value(samples, "demo_http_requests_total", {"route": "/", "status": "200"}) == 1
        assert sample_value(samples, "demo_http_requests_total", {"route": "/error", "status": "500"}) == 1
        assert sample_value(samples, "demo_http_requests_total", {"route": "other", "status": "404"}) == 1
        assert sample_value(samples, "demo_http_request_duration_seconds_count", {"route": "/"}) == 1
        assert sample_value(samples, "demo_http_request_duration_seconds_count", {"route": "/error"}) == 1
        assert sample_value(samples, "demo_http_request_duration_seconds_count", {"route": "other"}) == 1


def test_metrics_scrape_is_not_counted_as_user_traffic() -> None:
    asyncio.run(check_metrics_scrape_is_not_counted_as_user_traffic())


async def check_metrics_scrape_is_not_counted_as_user_traffic() -> None:
    async with app_client() as client:
        first = await scrape_samples(client)
        second = await scrape_samples(client)

        assert sample_value(first, "demo_http_requests_total", {"route": "/", "status": "200"}) == 0
        assert sample_value(second, "demo_http_requests_total", {"route": "/", "status": "200"}) == 0
        assert not any(sample.labels.get("route") == "/metrics" for sample in second)


def test_settings_use_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEMO_HOST", raising=False)
    monkeypatch.delenv("DEMO_PORT", raising=False)

    assert Settings.from_env() == Settings(host="0.0.0.0", port=8000)


@pytest.mark.parametrize("raw_port", ["zero", "0", "65536"])
def test_settings_reject_invalid_port(monkeypatch: pytest.MonkeyPatch, raw_port: str) -> None:
    monkeypatch.setenv("DEMO_PORT", raw_port)

    with pytest.raises(ValueError, match="DEMO_PORT"):
        Settings.from_env()


def app_client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=create_app())
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


async def assert_response(client: httpx.AsyncClient, path: str, status: int, body: str) -> None:
    response = await client.get(path)
    assert response.status_code == status
    assert response.text == body
    assert response.headers["content-type"] == "text/plain; charset=utf-8"


async def scrape_samples(client: httpx.AsyncClient) -> list[Sample]:
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == CONTENT_TYPE_LATEST
    return [sample for family in _families(response.text) for sample in family.samples]


def _families(payload: str) -> Iterable[Metric]:
    from prometheus_client.parser import text_string_to_metric_families

    return text_string_to_metric_families(payload)


def sample_value(samples: Iterable[Sample], name: str, labels: Mapping[str, str]) -> float:
    for sample in samples:
        if sample.name == name and all(sample.labels.get(key) == value for key, value in labels.items()):
            return sample.value
    raise AssertionError(f"sample not found: {name}{dict(labels)}")
