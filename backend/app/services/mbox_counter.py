from __future__ import annotations

from pathlib import Path


def quick_count_mbox(file_path: str | Path) -> tuple[int, int]:
    path = Path(file_path)
    total_size = path.stat().st_size if path.exists() else 0
    count = 0
    with path.open("rb") as handle:
        for line in handle:
            if line.startswith(b"From "):
                count += 1
    return count, total_size
