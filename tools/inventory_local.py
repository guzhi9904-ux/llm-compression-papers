"""扫描本地 PDF，提取去重和分类需要的基本信息。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader


EXCLUDED_PARTS = {"project", "researchMap", "llm-ptq-papers"}


def clean_text(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def inspect_pdf(path: Path, source_root: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)

    error = ""
    title = ""
    author = ""
    pages = 0
    first_page_lines: list[str] = []
    try:
        reader = PdfReader(path)
        pages = len(reader.pages)
        metadata = reader.metadata or {}
        title = clean_text(metadata.get("/Title"))
        author = clean_text(metadata.get("/Author"))
        if pages:
            page_text = reader.pages[0].extract_text() or ""
            first_page_lines = [
                clean_text(line)
                for line in page_text.splitlines()
                if clean_text(line)
            ][:35]
    except Exception as exc:  # 坏文件也进入清单，后续手工处理。
        error = f"{type(exc).__name__}: {exc}"

    return {
        "source_path": str(path),
        "relative_path": path.relative_to(source_root).as_posix(),
        "filename": path.name,
        "sha256": digest.hexdigest(),
        "size_bytes": path.stat().st_size,
        "pages": pages,
        "metadata_title": title,
        "metadata_author": author,
        "first_page_lines": first_page_lines,
        "error": error,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="扫描 LLM Compress 下的本地论文")
    parser.add_argument("source_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    paths = sorted(
        path
        for path in source_root.rglob("*")
        if path.is_file()
        and path.suffix.lower() == ".pdf"
        and not (EXCLUDED_PARTS & set(path.relative_to(source_root).parts))
    )
    records = [inspect_pdf(path, source_root) for path in paths]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"已扫描 {len(records)} 个 PDF：{args.output}")


if __name__ == "__main__":
    main()
