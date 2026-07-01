"""Shared path resolution for analysis scripts.

All analysis scripts live in ``backend_server/analysis/`` but read experiment
result folders that live one level up in ``backend_server/``.  Importing
``BACKEND`` here lets every script resolve result directories regardless of the
current working directory, so they can be run as either

    cd reverie/backend_server && python analysis/analyse_x.py
    python reverie/backend_server/analysis/analyse_x.py

Author: MRes validation study (WISE 2026).
"""
import os
import sys

# backend_server/  (parent of this analysis/ folder)
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Make backend_server importable (early_warning, measurement/, etc.).
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


def rpath(*parts):
    """Absolute path to a file/dir under backend_server/."""
    return os.path.join(BACKEND, *parts)
