#!/usr/bin/env python3
"""Generate compiled PDF exports for books from compiled.json files.

Expected layout:
  data/books/<slug>/compiled.json
  data/books/<slug>/compiled.pdf
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional
from xml.sax.saxutils import escape as xml_escape

try:
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
    )
except ImportError as exc:  # pragma: no cover - handled at runtime
    print(
        "ERROR: reportlab is required. Install it with `python3 -m pip install -r requirements.txt`.",
        file=sys.stderr,
    )
    raise


ROOT = Path(__file__).resolve().parents[1]
BOOKS_DIR = ROOT / "data" / "books"


class BuildError(Exception):
    """Raised when a PDF cannot be generated due to invalid source data."""


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BuildError(f"Invalid JSON in {path}: {exc}") from exc


def write_bytes(path: Path, data: bytes):
    path.write_bytes(data)


def iter_book_dirs(selected_slug: Optional[str]):
    if selected_slug:
        book_dir = BOOKS_DIR / selected_slug
        if not book_dir.is_dir():
            raise BuildError(f"Book directory not found: {book_dir}")
        return [book_dir]

    return sorted(path for path in BOOKS_DIR.iterdir() if path.is_dir())


def split_blocks(text: str) -> List[str]:
    parts = re.split(r"\n\s*\n", text.strip())
    return [part.strip() for part in parts if part and part.strip()]


def format_block(block: str) -> str:
    return xml_escape(block).replace("\n", "<br/>")


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="BookTitle",
            parent=styles["Title"],
            fontName="Times-Bold",
            fontSize=26,
            leading=30,
            alignment=TA_CENTER,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BookMeta",
            parent=styles["Normal"],
            fontName="Times-Roman",
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor="#444444",
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverNote",
            parent=styles["Normal"],
            fontName="Times-Italic",
            fontSize=10,
            leading=13,
            alignment=TA_CENTER,
            textColor="#666666",
        )
    )
    styles.add(
        ParagraphStyle(
            name="ChapterTitle",
            parent=styles["Heading1"],
            fontName="Times-Bold",
            fontSize=18,
            leading=22,
            spaceBefore=6,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionLabel",
            parent=styles["Heading2"],
            fontName="Times-Bold",
            fontSize=11,
            leading=13,
            spaceBefore=8,
            spaceAfter=4,
            textColor="#333333",
        )
    )
    styles.add(
        ParagraphStyle(
            name="ChapterBody",
            parent=styles["BodyText"],
            fontName="Times-Roman",
            fontSize=11,
            leading=14,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ChapterBodyCompact",
            parent=styles["BodyText"],
            fontName="Times-Roman",
            fontSize=10,
            leading=13,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FooterRight",
            parent=styles["Normal"],
            fontName="Times-Roman",
            fontSize=8.5,
            leading=10,
            alignment=TA_RIGHT,
            textColor="#666666",
        )
    )
    return styles


def build_story(book):
    styles = build_styles()
    story = []

    title = book.get("title") or book.get("slug") or "Livro"
    author = book.get("author") or ""
    year = book.get("year") or ""
    description = book.get("description") or ""
    tags = book.get("tags") or []
    chapters = book.get("chapters") or []

    story.extend(
        [
            Spacer(1, 28 * mm),
            Paragraph(xml_escape(title), styles["BookTitle"]),
        ]
    )

    if author:
        subtitle = author
        if year:
            subtitle += f" • {year}"
        story.append(Paragraph(xml_escape(subtitle), styles["BookMeta"]))

    if description:
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(xml_escape(description), styles["BookMeta"]))

    if tags:
        story.append(Spacer(1, 4 * mm))
        tag_text = "Tags: " + ", ".join(str(tag) for tag in tags)
        story.append(Paragraph(xml_escape(tag_text), styles["CoverNote"]))

    story.append(Spacer(1, 18 * mm))
    story.append(Paragraph("Edição compilada para leitura e arquivo.", styles["CoverNote"]))
    story.append(PageBreak())

    for chapter_index, chapter in enumerate(chapters):
        if chapter_index > 0:
            story.append(PageBreak())

        chapter_title = chapter.get("title") or f"Capítulo {chapter_index + 1}"
        story.append(Paragraph(xml_escape(chapter_title), styles["ChapterTitle"]))

        context = chapter.get("context") or ""
        if context:
            story.append(Paragraph("Contexto", styles["SectionLabel"]))
            for block in split_blocks(str(context)):
                story.append(Paragraph(format_block(block), styles["ChapterBody"]))

        content = chapter.get("content") or ""
        if content:
            for block in split_blocks(str(content)):
                story.append(Paragraph(format_block(block), styles["ChapterBody"]))

        annotations = chapter.get("annotations") or []
        if annotations:
            story.append(Paragraph("Notas", styles["SectionLabel"]))
            for note in annotations:
                target = str(note.get("target") or "").strip()
                text = str(note.get("text") or "").strip()
                if not target or not text:
                    continue
                note_html = f"<b>{xml_escape(target)}</b> - {xml_escape(text)}"
                story.append(Paragraph(note_html, styles["ChapterBodyCompact"]))

    return story


def page_decor(canvas, doc, book_title, author):
    canvas.saveState()
    width, height = A4

    canvas.setFont("Times-Roman", 8)
    canvas.setFillColorRGB(0.4, 0.4, 0.4)
    canvas.drawRightString(width - 15 * mm, 12 * mm, f"{canvas.getPageNumber()}")

    header_text = book_title
    if author:
        header_text = f"{book_title} • {author}"
    canvas.drawString(15 * mm, height - 12 * mm, header_text[:110])

    canvas.restoreState()


def generate_pdf(book_dir: Path):
    compiled_path = book_dir / "compiled.json"
    output_path = book_dir / "compiled.pdf"

    if not compiled_path.exists():
        raise BuildError(f"Missing compiled book file: {compiled_path}")

    book = load_json(compiled_path)
    story = build_story(book)

    title = book.get("title") or book_dir.name
    author = book.get("author") or ""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title=title,
        author=author,
        subject=book.get("description") or "",
        creator="Livros de Portugal PDF Builder",
        producer="ReportLab",
    )

    doc.build(
        story,
        onFirstPage=lambda canvas, doc: page_decor(canvas, doc, title, author),
        onLaterPages=lambda canvas, doc: page_decor(canvas, doc, title, author),
    )

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Build compiled PDF files for books.")
    parser.add_argument("--book", help="Only build one book by slug (folder name).")
    parser.add_argument("--quiet", action="store_true", help="Only print errors.")
    args = parser.parse_args()

    try:
        book_dirs = iter_book_dirs(args.book)
        if not book_dirs:
            raise BuildError(f"No book directories found in {BOOKS_DIR}")

        for book_dir in book_dirs:
            output_path = generate_pdf(book_dir)
            if not args.quiet:
                print(f"Built {output_path}")
    except BuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
