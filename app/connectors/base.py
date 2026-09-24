"""The connector contract. Every source implements this small interface."""

import os
from abc import ABC, abstractmethod

from app.database.models import Activity


def mock_mode_enabled() -> bool:
    return os.getenv("USE_MOCK_DATA", "false").lower() == "true"


class BaseConnector(ABC):
    source: str      # "github", "spotify", ...
    category: str    # one of Category values

    @abstractmethod
    def is_configured(self) -> bool:
        """True when the credentials this connector needs are present in .env."""

    @abstractmethod
    def fetch(self) -> list[dict]:
        """Call the external API. Returns raw records, exactly as the API gave them."""

    @abstractmethod
    def normalize(self, raw: list[dict]) -> list[Activity]:
        """Turn raw records into Activity objects. No I/O here."""

    @abstractmethod
    def mock(self) -> list[Activity]:
        """Realistic fake activities, used when mock mode is on or credentials are missing."""

    def run(self) -> tuple[list[Activity], str]:
        """Fetch + normalize, or mock. Returns (activities, mode) so callers can report it."""
        if mock_mode_enabled() or not self.is_configured():
            return self.mock(), "mock"
        return self.normalize(self.fetch()), "real"
