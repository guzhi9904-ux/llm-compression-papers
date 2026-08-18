"""检查清单、PDF 路径、哈希和重复文件。"""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path

from pypdf import PdfReader


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    manifest = repo_root / "manifests" / "papers.csv"
    with manifest.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))

    errors: list[str] = []
    hashes: list[str] = []
    manifest_paths: set[str] = set()
    total_pages = 0
    for row in rows:
        relative = row["pdf_path"]
        manifest_paths.add(relative)
        path = repo_root / relative
        if not path.exists():
            errors.append(f"清单文件不存在：{relative}")
            continue
        digest = file_sha256(path)
        hashes.append(digest)
        if digest != row["sha256"]:
            errors.append(f"SHA256 不一致：{relative}")
        try:
            reader = PdfReader(path)
            total_pages += len(reader.pages)
            if not reader.pages:
                errors.append(f"PDF 没有页面：{relative}")
            elif not (reader.pages[0].extract_text() or "").strip():
                errors.append(f"PDF 首页没有可提取文本：{relative}")
        except Exception as exc:
            errors.append(f"PDF 无法读取：{relative}：{exc}")

    disk_paths = {
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "papers").rglob("*.pdf")
    }
    for extra in sorted(disk_paths - manifest_paths):
        errors.append(f"PDF 没有写入清单：{extra}")
    duplicates = [digest for digest, count in Counter(hashes).items() if count > 1]
    if duplicates:
        errors.append(f"发现 {len(duplicates)} 组重复 SHA256")

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print(f"检查通过：{len(rows)} 篇论文，{total_pages} 页，无重复文件")


if __name__ == "__main__":
    main()
