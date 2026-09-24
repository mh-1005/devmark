"""`uv run devmark` — start the dashboard. Same as `uv run streamlit run app/dashboard.py`."""

import sys
from pathlib import Path

from streamlit.web import cli as stcli


def main() -> None:
    dashboard = Path(__file__).with_name("dashboard.py")
    sys.argv = ["streamlit", "run", str(dashboard), *sys.argv[1:]]
    sys.exit(stcli.main())
