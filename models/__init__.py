"""
Mina Models package registry
(Import everything that actually exists; ignore optional files gracefully.)
"""

# Some projects also keep a "Base"; if absent we ignore it.
try:
    from .base import Base  # noqa: F401
except Exception:
    Base = None  # noqa: N816

from .meeting import Meeting  # noqa: F401
from .session import Session  # noqa: F401
from .segment import Segment  # noqa: F401
from .shared_link import SharedLink  # noqa: F401
from .workspace import Workspace 
# metrics
try:
    from .metrics import ChunkMetric, SessionMetric  # noqa: F401
except Exception:
    ChunkMetric = SessionMetric = None  # noqa: N816

# summaries
try:
    from .summary import Summary  # noqa: F401
except Exception:
    Summary = None  # noqa: N816

# tasks (new)
try:
    from .task import Task  # noqa: F401
except Exception:
    Task = None  # noqa: N816

# optional models referenced by some routes (avoid breaking CLI if missing)
for _opt in ("workspace", "page", "user"):
    try:
        globals()[_opt.capitalize()] = __import__(f"models.{_opt}", fromlist=[_opt.capitalize()]).__dict__[
            _opt.capitalize()
        ]
    except Exception:
        pass

__all__ = [name for name in list(globals()) if name[0].isupper()]