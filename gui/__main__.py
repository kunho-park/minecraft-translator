"""Entry point for running GUI as module."""

from __future__ import annotations

import sys

try:
    from .main import main
except ImportError:
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from gui.main import main

if __name__ == "__main__":
    sys.exit(main())
