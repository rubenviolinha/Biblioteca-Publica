#!/usr/bin/env python3
"""Build compiled book files from folder-based book sources.

Expected layout:
  data/books/<slug>/book.json
  data/books/<slug>/chapters/<chapter-slug>.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
BOOKS_DIR = ROOT / "data" / "books"


class BuildError(Exception):
    """Raised when a book cannot be compiled due to data validation failures."""


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BuildError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def validate_chapter_order(chapter_order, book_path: Path):
    if not isinstance(chapter_order, list) or not chapter_order:
        raise BuildError(f"{book_path} must contain a non-empty chapterOrder list.")
    if not all(isinstance(slug, str) and slug.strip() for slug in chapter_order):
        raise BuildError(f"{book_path} chapterOrder must contain only non-empty strings.")

    seen = set()
    duplicates = []
    for slug in chapter_order:
        if slug in seen:
            duplicates.append(slug)
        seen.add(slug)
    if duplicates:
        unique_dupes = sorted(set(duplicates))
        raise BuildError(f"{book_path} chapterOrder has duplicate slugs: {', '.join(unique_dupes)}")


def build_book(book_dir: Path):
    book_path = book_dir / "book.json"
    chapters_dir = book_dir / "chapters"
    output_path = book_dir / "compiled.json"

    if not book_path.exists():
        raise BuildError(f"Missing {book_path}")
    if not chapters_dir.is_dir():
        raise BuildError(f"Missing chapters directory: {chapters_dir}")

    book_data = load_json(book_path)
    chapter_order = book_data.get("chapterOrder")
    validate_chapter_order(chapter_order, book_path)

    chapter_files = sorted(chapters_dir.glob("*.json"))
    chapter_map = {}
    for chapter_file in chapter_files:
        chapter = load_json(chapter_file)
        chapter_slug = chapter.get("slug") or chapter_file.stem
        if not isinstance(chapter_slug, str) or not chapter_slug.strip():
            raise BuildError(f"Invalid chapter slug in {chapter_file}")
        chapter_slug = chapter_slug.strip()
        chapter["slug"] = chapter_slug
        if chapter_slug in chapter_map:
            raise BuildError(f"Duplicate chapter slug '{chapter_slug}' in {chapters_dir}")
        chapter_map[chapter_slug] = chapter

    missing = [slug for slug in chapter_order if slug not in chapter_map]
    if missing:
        raise BuildError(f"{book_path} chapterOrder references missing chapters: {', '.join(missing)}")

    orphans = [slug for slug in chapter_map if slug not in chapter_order]
    if orphans:
        raise BuildError(
            f"{book_path} has chapter files not listed in chapterOrder: {', '.join(sorted(orphans))}"
        )

    compiled = {key: value for key, value in book_data.items() if key != "chapterOrder"}
    compiled["chapters"] = [chapter_map[slug] for slug in chapter_order]

    write_json(output_path, compiled)


def iter_book_dirs(selected_slug: Optional[str]):
    if selected_slug:
        book_dir = BOOKS_DIR / selected_slug
        if not book_dir.is_dir():
            raise BuildError(f"Book directory not found: {book_dir}")
        return [book_dir]

    return sorted(path for path in BOOKS_DIR.iterdir() if path.is_dir())


def main():
    parser = argparse.ArgumentParser(description="Build compiled.json files for books.")
    parser.add_argument("--book", help="Only build one book by slug (folder name).")
    args = parser.parse_args()

    try:
        book_dirs = iter_book_dirs(args.book)
        if not book_dirs:
            raise BuildError(f"No book directories found in {BOOKS_DIR}")
        for book_dir in book_dirs:
            build_book(book_dir)
            print(f"Built {book_dir / 'compiled.json'}")
    except BuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
