#!/usr/bin/env python3
"""Local admin API for writing book files and running compilation."""

import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BOOKS_INDEX = DATA_DIR / "books.json"
BOOKS_DIR = DATA_DIR / "books"
BUILD_SCRIPT = ROOT / "scripts" / "build_books.py"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def list_books():
    if BOOKS_INDEX.exists():
        data = read_json(BOOKS_INDEX)
        return data if isinstance(data, list) else []
    return []


def next_book_id(existing_books):
    ids = [b.get("id") for b in existing_books if isinstance(b.get("id"), int)]
    return (max(ids) + 1) if ids else 1


def normalize_book_metadata(book, existing_books):
    fields = ["id", "slug", "title", "author", "authorId", "authorBio", "description", "year", "language", "tags"]
    meta = {k: book.get(k) for k in fields if book.get(k) not in (None, "")}
    if "slug" not in meta:
        raise ValueError("book.slug is required")

    current = next((b for b in existing_books if b.get("slug") == meta["slug"]), None)
    if "id" not in meta:
        if current and isinstance(current.get("id"), int):
            meta["id"] = current["id"]
        else:
            meta["id"] = next_book_id(existing_books)
    return meta


def save_book_payload(payload):
    book = payload.get("book")
    chapters_map = payload.get("chapters")
    if not isinstance(book, dict) or not isinstance(chapters_map, dict):
        raise ValueError("Payload must include 'book' object and 'chapters' object")

    slug = book.get("slug")
    if not isinstance(slug, str) or not slug.strip():
        raise ValueError("book.slug is required")
    slug = slug.strip()

    chapter_order = book.get("chapterOrder") or list(chapters_map.keys())
    if not isinstance(chapter_order, list) or not chapter_order:
        raise ValueError("book.chapterOrder must be a non-empty list")
    if len(set(chapter_order)) != len(chapter_order):
        raise ValueError("book.chapterOrder contains duplicates")

    missing = [c for c in chapter_order if c not in chapters_map]
    if missing:
        raise ValueError(f"Missing chapter content for slugs: {', '.join(missing)}")

    book_dir = BOOKS_DIR / slug
    chapters_dir = book_dir / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    # Write chapter files (create/update)
    for chapter_slug in chapter_order:
        chapter = chapters_map[chapter_slug]
        if not isinstance(chapter, dict):
            raise ValueError(f"Chapter '{chapter_slug}' must be an object")
        chapter_obj = dict(chapter)
        chapter_obj["slug"] = chapter_slug
        write_json(chapters_dir / f"{chapter_slug}.json", chapter_obj)

    # Delete chapter files no longer present
    expected_files = {f"{slug_name}.json" for slug_name in chapter_order}
    for path in chapters_dir.glob("*.json"):
        if path.name not in expected_files:
            path.unlink()

    # Save book.json
    book_obj = dict(book)
    book_obj["slug"] = slug
    book_obj["chapterOrder"] = chapter_order
    write_json(book_dir / "book.json", book_obj)

    # Keep books.json metadata in sync
    books = list_books()
    meta = normalize_book_metadata(book_obj, books)
    replaced = False
    for idx, existing in enumerate(books):
        if existing.get("slug") == slug:
            books[idx] = meta
            replaced = True
            break
    if not replaced:
        books.append(meta)
    books.sort(key=lambda item: item.get("id", 999999))
    write_json(BOOKS_INDEX, books)

    # Build compiled file for this book
    run_compile(book_slug=slug)
    return {"slug": slug, "books": books}


def run_compile(book_slug=None):
    cmd = [sys.executable, str(BUILD_SCRIPT)]
    if book_slug:
        cmd.extend(["--book", book_slug])
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if proc.returncode != 0:
        error_message = (proc.stderr or proc.stdout or "Compilation failed").strip()
        raise RuntimeError(error_message)
    return {"stdout": proc.stdout.strip()}


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(200, {"ok": True})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json(200, {"ok": True})
            return
        if path == "/api/books":
            self._send_json(200, {"ok": True, "books": list_books()})
            return
        self._send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
            payload = json.loads(raw.decode("utf-8"))

            if path == "/api/books/save":
                result = save_book_payload(payload)
                self._send_json(200, {"ok": True, **result})
                return

            if path == "/api/compile":
                book_slug = payload.get("bookSlug")
                compile_result = run_compile(book_slug=book_slug)
                self._send_json(200, {"ok": True, **compile_result})
                return

            self._send_json(404, {"ok": False, "error": "Not found"})
        except Exception as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})


def main():
    host = "127.0.0.1"
    port = 8765
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Admin API running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
