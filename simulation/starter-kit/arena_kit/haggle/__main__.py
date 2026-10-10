"""arena-haggle: open the page that runs and inspects the haggling agent."""

import argparse
import os
import threading
import webbrowser
from pathlib import Path

import uvicorn

from arena_kit.cli import load_env
from arena_kit.data import DataPackage

from .server import create_app


def find_data():
    for candidate in (os.environ.get("ARENA_DATA"), "data/package", "../data"):
        if candidate:
            try:
                return DataPackage(Path(candidate))
            except (FileNotFoundError, OSError):
                continue
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(prog="arena-haggle", description=__doc__)
    ap.add_argument("--host", default="127.0.0.1", help="keep it on localhost: the server holds your keys")
    ap.add_argument("--port", type=int, default=8100)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args(argv)
    load_env()
    url = f"http://{a.host}:{a.port}"
    pkg = find_data()
    print(f"arena-haggle on {url} · data: {pkg.root if pkg else 'none found (set ARENA_DATA)'}", flush=True)
    if not a.no_browser:
        threading.Timer(1.0, webbrowser.open, [url]).start()
    uvicorn.run(create_app(pkg), host=a.host, port=a.port, log_level="warning")


if __name__ == "__main__":
    main()
