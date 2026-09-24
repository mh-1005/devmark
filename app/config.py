"""Where settings come from: the .env file at the project root. Import this module to load it."""

from pathlib import Path

from dotenv import load_dotenv, set_key

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"

load_dotenv(ENV_PATH)


def save_env(values: dict[str, str]) -> None:
    """Write keys into .env (creating it if needed) and reload them into the running process."""
    ENV_PATH.touch(exist_ok=True)
    for key, value in values.items():
        set_key(str(ENV_PATH), key, value)
    load_dotenv(ENV_PATH, override=True)
