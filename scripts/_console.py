"""UTF-8 CLI streams on Windows even when encoding environment variables are absent."""

import sys


def configure_utf8():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
