"""Load and cache the JPL ephemeris used by every astronomy tool."""

import os
from functools import cache
from pathlib import Path

from skyfield.api import Loader
from skyfield.jpllib import SpiceKernel
from skyfield.timelib import Timescale

EPHEMERIS_FILE = "de421.bsp"


def cache_dir() -> Path:
    """Directory holding downloaded data, from SKY_TONIGHT_CACHE or ~/.cache/sky-tonight."""
    configured = os.environ.get("SKY_TONIGHT_CACHE")
    path = Path(configured) if configured else Path.home() / ".cache" / "sky-tonight"
    path.mkdir(parents=True, exist_ok=True)
    return path


@cache
def _loader() -> Loader:
    return Loader(str(cache_dir()), verbose=False)


@cache
def ephemeris() -> SpiceKernel:
    """The DE421 ephemeris, downloaded on first use and cached on disk."""
    return _loader()(EPHEMERIS_FILE)


@cache
def timescale() -> Timescale:
    # Use Skyfield's built-in leap-second table so no extra download is needed.
    return _loader().timescale(builtin=True)
