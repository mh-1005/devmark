"""The connector contract. Every source implements this small interface."""

import os
from abc import ABC, abstractmethod

from app.database.models import Activity


def mock_mode_enabled() -> bool:
    return os.getenv("USE_MOCK_DATA", "false").lower() == "true"


class BaseConnector(ABC):
    source: str          # "github", "leetcode", ...
    category: str        # one of Category values
    local: bool = False  # True = reads files on this machine; only works when the app runs locally

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

    def status(self) -> str:
        """One short line for the sidebar. Subclasses add the username or file count."""
        return "connected" if self.is_configured() else "not connected"

    def run(self) -> tuple[list[Activity], str]:
        """Returns (activities, mode). mode is "real", "mock", or "skipped".

        Mock data only appears when explicitly asked for (USE_MOCK_DATA=true).
        An unconfigured source contributes nothing rather than fake rows.
        """
        if mock_mode_enabled():
            return self.mock(), "mock"
        if not self.is_configured():
            return [], "skipped"
        return self.normalize(self.fetch()), "real"
