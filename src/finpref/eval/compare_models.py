"""Compare summary metric files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("metric_files", nargs="+")
    args = parser.parse_args()
    for file in args.metric_files:
        data = json.loads(Path(file).read_text(encoding="utf-8"))
        print(Path(file).stem, data)


if __name__ == "__main__":
    main()

