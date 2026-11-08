"""Runtime settings for the example application."""

import os
from dataclasses import dataclass

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000


@dataclass(frozen=True, slots=True)
class Settings:
    """Network settings accepted by the local Uvicorn process."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings without adding a configuration dependency."""
        host = os.getenv("DEMO_HOST", DEFAULT_HOST)
        raw_port = os.getenv("DEMO_PORT", str(DEFAULT_PORT))
        try:
            port = int(raw_port)
        except ValueError as error:
            raise ValueError("DEMO_PORT must be an integer") from error
        if not 1 <= port <= 65535:
            raise ValueError("DEMO_PORT must be between 1 and 65535")
        return cls(host=host, port=port)
