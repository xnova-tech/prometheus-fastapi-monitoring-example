"""Run the example through Uvicorn."""

import uvicorn

from prometheus_demo.app import app
from prometheus_demo.config import Settings


def main() -> None:
    """Start the HTTP server with environment-backed settings."""
    settings = Settings.from_env()
    uvicorn.run(app, host=settings.host, port=settings.port, access_log=False)


if __name__ == "__main__":
    main()
