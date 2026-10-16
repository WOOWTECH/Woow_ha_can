"""Make custom_components importable, with Home Assistant's validation library set up first."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import homeassistant  # noqa: F401  (installs probatio as `voluptuous`, as Home Assistant itself does)
except ImportError:  # the cantools comparison runs without Home Assistant
    pass
