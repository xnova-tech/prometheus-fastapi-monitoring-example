"""Deterministic HTTP observation used by technical acceptance."""

import asyncio

import httpx

from prometheus_demo import create_app


async def check_app() -> None:
    """Exercise the ASGI application through HTTPX without opening a port."""
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        for label, path, expected in (
            ("ok", "/", 200),
            ("not_found", "/missing?user=sample", 404),
            ("controlled_error", "/error", 500),
        ):
            response = await client.get(path)
            if response.status_code != expected:
                raise AssertionError(f"{label}: expected {expected}, got {response.status_code}")
            print(f"{label}: status={response.status_code}")

        metrics = (await client.get("/metrics")).text
        expected_lines = (
            'demo_http_requests_total{route="/",status="200"} 1.0',
            'demo_http_requests_total{route="other",status="404"} 1.0',
            'demo_http_requests_total{route="/error",status="500"} 1.0',
            'demo_http_request_duration_seconds_count{route="/"} 1.0',
        )
        if not all(line in metrics for line in expected_lines):
            raise AssertionError("expected counter or histogram samples are missing")
        if 'route="/metrics"' in metrics:
            raise AssertionError("metrics scrape was counted as user traffic")
        print("metrics: counters=3 histogram=observed scrape_excluded=true")


def main() -> None:
    asyncio.run(check_app())


if __name__ == "__main__":
    main()
