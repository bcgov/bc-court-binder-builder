#!/usr/bin/env python3
"""
assembling_court_binders.py
===========================
PURPOSE:
    Assembles source court documents into a fully compliant BC Supreme Court PD-72
    Electronic Application Record or Court of Appeal Book of Authorities (BoA).
    Executes two-pass mathematical foliation, Form 22 Title Page generation, 4-column
    hyperlinked Index table, hierarchical bookmarks, top-center 15 pt bold folios,
    and synchronized catalog /PageLabels.

KEY INPUT DEPENDENCIES:
    - inputs/<matter>/manifest.json     : Document sequence and metadata (or auto-inferred from Tab filenames)
    - inputs/<matter>/*.pdf or *.txt    : Substantive court pleadings and exhibits
    - references/filename-conventions.md: Statutory naming schema contract

FUNCTION INDEX:
    - clean_display_title(text: str) -> str
    - extract_date_str(text: str, default: str = "") -> str
    - escape_pdf_text(text: str) -> str
    - load_document_lines(inputs_dir: Path, filename: str) -> list[str]
    - infer_manifest_from_files(inputs_dir: Path) -> dict
    - build_binder(inputs_dir: Path, output_file: Path) -> Path
    - main() -> None

USAGE:
    python3 assembling_court_binders.py --inputs inputs/01-commercial-discovery --output output/01-commercial-discovery/Application_Record.pdf
"""

import os
import sys
import re
import glob
import io
from datetime import datetime
import json
import textwrap
import argparse
from pathlib import Path

# Regular expression for parsing raw document folders lacking manifest.json
FILENAME_REGEX = re.compile(
    r"^(?:Tab_?|Item_?|)(\d{1,2})[-_.\s]+"
    r"(.+?)"
    r"(?:[-_.\s]+(\d{1,2}[A-Za-z]{3}\d{4}))?"
    r"\.pdf$",
    re.IGNORECASE
)

# -----------------------------------------------------------------------------
# Document metadata and text cleaning helpers
# -----------------------------------------------------------------------------

PLACEHOLDER_REGISTRY = "[Registry - complete before filing]"
PLACEHOLDER_FILE_NUMBER = "[Court file number - complete before filing]"


CASE_FIELDS = (
    "court", "registry", "file_number", "plaintiff", "defendant",
    "application_date", "time_estimate", "counsel_applicant", "counsel_respondent",
)
REQUIRED_CASE_FIELDS = {
    "court": "court",
    "registry": "registry",
    "file_number": "court file number",
    "plaintiff": "applicant or plaintiff",
    "defendant": "respondent or defendant",
    "application_date": "hearing date",
}
DEFAULT_COURT = "Supreme Court of British Columbia"
COVER_FILE_NAME = "000_Application_Record_Title_Page.txt"
COVER_CASE_FIELDS = ("court", "registry", "file_number")  # still used in page headers when a custom cover is supplied


def read_case_details(folder: Path) -> dict:
    """Returns the title-page case details for a folder of filings.

    Args:
        folder: Folder of filings.

    Returns:
        Every case field (empty text when unknown; the court is prefilled) plus
        has_manifest, which says whether manifest.json already existed.
    """
    details = {field: "" for field in CASE_FIELDS}
    details["court"] = DEFAULT_COURT
    manifest_path = folder / "manifest.json"
    has_manifest = manifest_path.is_file()
    if has_manifest:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for field in CASE_FIELDS:
            details[field] = str(manifest.get(field, details[field]))
    details["has_manifest"] = has_manifest
    details["has_cover_file"] = (folder / COVER_FILE_NAME).is_file()
    return details


def save_case_details(folder: Path, details: dict, require_all: bool = True) -> Path:
    """Validates case details and writes them into folder/manifest.json.

    Never invents values: a blank required field is refused. An existing
    manifest keeps its documents and exhibits; with none, the document list is
    inferred from the Tab filenames.

    Args:
        folder: Folder of filings.
        details: Case fields supplied by the user.
        require_all: When False, blank required fields are simply left out of the
            manifest (the title page then shows a marked placeholder) instead of
            being refused.

    Returns:
        The path of the written manifest.json.

    Raises:
        ValueError: If a required field is blank or the filenames cannot be read.
    """
    cleaned = {f: str(details.get(f, "")).strip() for f in CASE_FIELDS}
    # A custom cover page supplies the parties, hearing date and the rest;
    # only the details used in page headers are still needed.
    required = (
        {f: REQUIRED_CASE_FIELDS[f] for f in COVER_CASE_FIELDS}
        if (folder / COVER_FILE_NAME).is_file() else REQUIRED_CASE_FIELDS
    )
    missing = [label for field, label in required.items() if not cleaned[field]]
    if missing and require_all:
        raise ValueError("Enter the " + ", ".join(missing) + " before building.")
    manifest_path = folder / "manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = infer_manifest_from_files(folder)
        manifest.pop("inferred", None)
    for field, value in cleaned.items():
        if value or field in required:
            manifest[field] = value
        else:
            manifest.pop(field, None)
    temp = manifest_path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temp.replace(manifest_path)
    return manifest_path


def suggest_binder_name(folder: Path, application_date: str | None = None) -> str:
    """Suggests a binder file name: Application_Record_<folder>[_DDMmmYYYY].

    The folder name identifies the matter. The application date, from the
    argument or manifest.json, is appended as DDMmmYYYY (for example 15Nov2026).
    The court guides set no rule for this name; it is a project recommendation.

    Args:
        folder: Folder of filings.
        application_date: A date typed by the user; overrides the manifest's.

    Returns:
        A file name without the .pdf extension.
    """
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", folder.name).strip("_") or "Filings"
    name = f"Application_Record_{stem}"
    raw = application_date or ""
    if not raw:
        try:
            raw = str(json.loads((folder / "manifest.json").read_text(encoding="utf-8")).get("application_date", ""))
        except (OSError, ValueError):
            return name
    match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", raw)
    if match:
        try:
            return f"{name}_{datetime.strptime(' '.join(match.groups()), '%B %d %Y').strftime('%d%b%Y')}"
        except ValueError:
            pass
    return name


INDEX_START_Y = 632      # first row on every index page
INDEX_ROW_STEP = 22      # vertical space one index row uses
INDEX_BOTTOM_Y = 60      # rows stop above this


def paginate_index_rows(rows: list[dict]) -> list[list[dict]]:
    """Splits index rows into pages by the vertical space each row uses.

    A heading row (such as AUTHORITIES) uses a little more space than a normal row.
    There is always at least one page.

    Args:
        rows: Index rows in order.

    Returns:
        A list of pages, each a list of rows.
    """
    pages: list[list[dict]] = []
    current: list[dict] = []
    y = INDEX_START_Y
    for row in rows:
        cost = 4 + (INDEX_ROW_STEP - 2) if row["type"] == "heading" else INDEX_ROW_STEP
        if current and y - cost < INDEX_BOTTOM_Y:
            pages.append(current)
            current, y = [], INDEX_START_Y
        current.append(row)
        y -= cost
    pages.append(current)
    return pages


def open_original_pdf(inputs_dir: Path, filename: str):
    """Opens a filing's original PDF so its real pages can go in the binder.

    Args:
        inputs_dir: Folder of filings.
        filename: The filing's file name from the manifest.

    Returns:
        (path, reader) when the file is a readable PDF with at least one page
        inside inputs_dir, otherwise None (the caller then re-typesets the text).
    """
    try:
        path = resolve_inside(inputs_dir, filename)
    except ValueError:
        return None
    if path.suffix.lower() != ".pdf" or not path.is_file():
        return None
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        if reader.is_encrypted and not reader.decrypt(""):
            return None
        return (path, reader) if len(reader.pages) > 0 else None
    except Exception:
        return None


def folio_overlay_pdf(content: str, font: str = "Helvetica-Bold") -> bytes:
    """Builds a one-page PDF carrying only the folio text, to be merged over a page.

    The font (Helvetica-Bold unless told otherwise) is named /BCFolio. The page size
    is irrelevant because the overlay is merged into a page whose size is already set.
    """
    body = content.encode("cp1252", errors="replace")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /BCFolio 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /" + font.encode("ascii") + b" /Encoding /WinAnsiEncoding >>",
        b"<< /Length %d >>\nstream\n" % len(body) + body + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.7\n")
    offsets = []
    for number, obj in enumerate(objs, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + obj + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


def folio_stream(folio: int, box, rotation: int) -> str:
    """Returns content-stream text that draws a folio at the top centre of the displayed page.

    The number is Helvetica-Bold 15 pt, 32 pt below the displayed top edge, and stays
    upright and top-centre on pages that are rotated 90, 180 or 270 degrees.

    Args:
        folio: The page number to print.
        box: The page's media box (left, bottom, width, height are read from it).
        rotation: The page's /Rotate value.
    """
    left, bottom = float(box.left), float(box.bottom)
    width, height = float(box.width), float(box.height)
    text = str(folio)
    text_width = len(text) * 15 * 0.556  # Helvetica-Bold digits are 556/1000 em wide
    rot = rotation % 360
    if rot == 90:
        matrix, x, y = (0, 1, -1, 0), left + 32, bottom + height / 2 - text_width / 2
    elif rot == 180:
        matrix, x, y = (-1, 0, 0, -1), left + width / 2 + text_width / 2, bottom + 32
    elif rot == 270:
        matrix, x, y = (0, -1, 1, 0), left + width - 32, bottom + height / 2 + text_width / 2
    else:
        matrix, x, y = (1, 0, 0, 1), left + width / 2 - text_width / 2, bottom + height - 32
    a, b, c, d = matrix
    return f"q\nBT\n/BCFolio 15 Tf\n{a} {b} {c} {d} {x:.2f} {y:.2f} Tm\n({escape_pdf_text(text)}) Tj\nET\nQ\n"


def splice_original_pages(output_file: Path, originals: list) -> None:
    """Replaces blank placeholder pages with the filings' real pages (true copies).

    The placeholders were written with the right page numbers, bookmarks, index
    links and page labels. This puts each original page's content, size, rotation
    and annotations into the same page object, then stamps the folio on top, so
    nothing that points at the page has to change.

    Args:
        output_file: The binder written by build_binder (modified in place).
        originals: Tuples of (page index in the binder, source PDF path,
            page index in the source, folio number).
    """
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter(clone_from=PdfReader(str(output_file)))
    sources: dict = {}
    for page_idx, src_path, src_idx, folio in originals:
        reader = sources.get(src_path)
        if reader is None:
            reader = PdfReader(str(src_path))
            if reader.is_encrypted:
                reader.decrypt("")
            sources[src_path] = reader
        source = reader.pages[src_idx]
        target = writer.pages[page_idx]
        target.mediabox = source.mediabox
        if "/CropBox" in source:
            target.cropbox = source.cropbox
        rotation = int(source.rotation or 0)
        if rotation:
            target.rotate(rotation)
        target.merge_page(source)
        overlay = PdfReader(io.BytesIO(folio_overlay_pdf(folio_stream(folio, source.mediabox, rotation)))).pages[0]
        target.merge_page(overlay)
    with open(output_file, "wb") as handle:
        writer.write(handle)


def clean_display_title(text: str) -> str:
    """Cleans up document title for the Index table."""
    m = re.match(r'^(.*?)\s+(?:sworn|filed|dated)\s+[A-Za-z]+\s+\d{1,2},?\s+\d{4}', text, re.IGNORECASE)
    if m:
        t = m.group(1).strip()
        if t:
            text = t
    # Strip Item / Tab prefix from title if present
    text = re.sub(r'^(?:Item\s+\d+\s*-\s*|Tab\s+\d+\s*-\s*)', '', text, flags=re.IGNORECASE)
    # Strip long parenthetical descriptions if too wide for the DOCUMENT column
    if len(text) > 44 and " (" in text:
        text = text.split(" (")[0].strip()
    return text.strip()

def extract_date_str(text: str, default: str = "") -> str:
    """Extracts filing, sworn, or dated timestamp from title/description."""
    m = re.search(r'(?:sworn|filed|dated)\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})', text, re.IGNORECASE)
    if m:
        return m.group(1)
    m_full = re.search(r'\b([A-Za-z]+\s+\d{1,2},?\s+\d{4})\b', text)
    if m_full:
        return m_full.group(1)
    m_year = re.search(r'\b(20\d{2})\b', text)
    if m_year:
        return m_year.group(1)
    return default

PDF_TEXT_ENCODING = "cp1252"  # Windows ANSI, matches /Encoding /WinAnsiEncoding on the fonts


def pdf_title_string(text: str) -> str:
    """Returns a PDF string for a bookmark title.

    Plain ASCII titles are written as escaped literals. Anything else is written
    as a UTF-16BE hex string with a byte-order mark, which every PDF viewer reads
    correctly (accents, dashes, curly quotes).
    """
    if text.isascii():
        return f"({escape_pdf_text(text)})"
    return "<FEFF" + text.encode("utf-16-be").hex().upper() + ">"


def unsupported_characters(texts: list[str]) -> list[str]:
    """Returns the distinct characters that the Windows ANSI (cp1252) text encoding cannot show.

    Helvetica as used here shows Western European text; anything else is replaced
    with '?', so callers warn the user.
    """
    bad: set[str] = set()
    for text in texts:
        for ch in text:
            try:
                ch.encode(PDF_TEXT_ENCODING)
            except UnicodeEncodeError:
                bad.add(ch)
    return sorted(bad)


# The quote marks around the exhibit letter may be straight, curly or garbled
# (older PDFs were written with the wrong text encoding), so allow any run of
# up to 8 non-alphanumeric characters around the letter.
_JUNK = r"[^A-Za-z0-9\n]{0,8}"
EXHIBIT_STAMP = re.compile(rf"this is exhibit{_JUNK}([A-Z0-9]{{1,3}}){_JUNK}referred to", re.IGNORECASE)
EXHIBIT_HEADER = re.compile(
    rf"^exhibit{_JUNK}([A-Z0-9]{{1,3}}){_JUNK}[-\u2013\u2014:]\s*(.+?)(?:\s*\(page \d+ of \d+\))?$",
    re.IGNORECASE)


def detect_exhibits(doc_pages: list[dict]) -> list[dict]:
    """Finds exhibits in a document from their exhibit stamps.

    A page carrying "This is Exhibit "A" referred to in ..." starts exhibit A. The
    description comes from an "EXHIBIT "A" - DESCRIPTION" heading on that page when
    one exists. Body text such as "marked as Exhibit A" is not a stamp and is ignored.

    Args:
        doc_pages: The paginated pages of one document (each has a "lines" list).

    Returns:
        Exhibit dictionaries (letter, description, rel_page), the same shape as a
        manifest exhibit list.
    """
    found: list[dict] = []
    seen: set[str] = set()
    for rel_page, page in enumerate(doc_pages, start=1):
        page_lines = page.get("detect_lines", page["lines"])
        stamp = EXHIBIT_STAMP.search(" ".join(line.strip() for line in page_lines))
        if not stamp or stamp.group(1).upper() in seen:
            continue
        letter = stamp.group(1).upper()
        seen.add(letter)
        description = ""
        for line in page_lines:
            header = EXHIBIT_HEADER.match(line.strip())
            if header and header.group(1).upper() == letter:
                description = header.group(2).strip()
                description = description.title() if description.isupper() else description
                break
        found.append({"letter": letter, "description": description, "rel_page": rel_page})
    return found


def escape_pdf_text(text: str) -> str:
    """Escapes backslashes and parentheses for PDF string literals."""
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

class SourceTextUnavailable(ValueError):
    """Raised when a filing's text cannot be recovered; never substitute placeholder text."""


def resolve_inside(inputs_dir: Path, filename: str) -> Path:
    """Resolves a manifest filename and refuses anything outside the input folder.

    Args:
        inputs_dir: The folder the user chose.
        filename: A filename taken from manifest.json.

    Returns:
        The resolved path, guaranteed to be inside inputs_dir.

    Raises:
        ValueError: If the filename is absolute or escapes inputs_dir.
    """
    base = inputs_dir.resolve()
    candidate = (base / filename).resolve()
    if Path(filename).is_absolute() or not candidate.is_relative_to(base):
        raise ValueError(f"Manifest filename escapes the input folder: {filename!r}")
    return candidate


def wrap_lines(raw_text: str) -> list[str]:
    """Wraps text into court-page lines of at most 75 characters."""
    wrapped: list[str] = []
    for line in raw_text.splitlines():
        stripped = line.rstrip()
        if not stripped:
            wrapped.append("")
        elif len(stripped) <= 75:
            wrapped.append(stripped)
        else:
            wrapped.extend(textwrap.wrap(stripped, width=75))
    return wrapped


def extract_pdf_text(pdf_path: Path) -> str:
    """Extracts text from a PDF with pdftotext when available, else pypdf."""
    import shutil
    import subprocess

    if shutil.which("pdftotext"):
        try:
            out = subprocess.check_output(["pdftotext", str(pdf_path), "-"])
            if out.strip():
                return out.decode("utf-8", errors="ignore")
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception:
        return ""


def load_document_lines(inputs_dir: Path, filename: str) -> list[str]:
    """Loads substantive text lines for one filing, preferring .txt over .pdf.

    Raises:
        SourceTextUnavailable: If no text can be recovered. A binder must never
            contain invented placeholder text in place of a real filing.
        ValueError: If the filename escapes the input folder.
    """
    base = inputs_dir.resolve()
    txt_candidates = [
        resolve_inside(inputs_dir, filename.replace(".pdf", ".txt")),
        resolve_inside(inputs_dir, filename),
    ]
    prefix = glob.escape(filename.split("_")[0])
    exact_exists = any(c.exists() and c.suffix == ".txt" for c in txt_candidates)
    prefix_matches = sorted(p for p in base.glob(f"{prefix}_*.txt") if p.is_relative_to(base))
    if not exact_exists and len(prefix_matches) > 1:
        names = ", ".join(m.name for m in prefix_matches)
        raise SourceTextUnavailable(
            f"Ambiguous source text for {filename}: several files share its prefix ({names}). "
            "Name the text file exactly like the filing."
        )
    txt_candidates.extend(prefix_matches)

    for cand in txt_candidates:
        if cand.exists() and cand.suffix == ".txt":
            wrapped = wrap_lines(cand.read_text(encoding="utf-8"))
            if wrapped:
                return wrapped

    pdf_path = resolve_inside(inputs_dir, filename)
    if pdf_path.exists() and pdf_path.suffix == ".pdf":
        wrapped = wrap_lines(extract_pdf_text(pdf_path))
        if any(line.strip() for line in wrapped):
            return wrapped
        raise SourceTextUnavailable(
            f"No extractable text in {filename}. If it is a scan, run OCR first, "
            "or provide a matching .txt file."
        )
    raise SourceTextUnavailable(f"Source file not found for {filename} in {inputs_dir}.")

def infer_manifest_from_files(inputs_dir: Path) -> dict:
    """Auto-synthesizes manifest data from conforming Tab filenames when manifest.json is absent."""
    pdf_files = sorted(list(inputs_dir.glob("*.pdf")))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF documents or manifest.json found in {inputs_dir}")

    documents = []
    non_conforming = []

    for f in pdf_files:
        if f.stat().st_size == 0:
            raise ValueError(f"Input file is 0 bytes (corrupt/empty): {f.name}")

        m = FILENAME_REGEX.match(f.name)
        if m:
            tab_num = int(m.group(1))
            raw_title = m.group(2).replace("_", " ").strip()
            date_str = m.group(3) or ""
            documents.append({
                "item_num": tab_num,
                "title": f"Tab {tab_num} - {raw_title}",
                "short_title": raw_title,
                "date": date_str,
                "filename": f.name,
                "exhibits": []
            })
        else:
            non_conforming.append(f.name)

    if non_conforming:
        examples = "\n  - ".join(non_conforming[:5])
        raise ValueError(
            f"Input folder contains files not conforming to court filename conventions:\n  - {examples}\n"
            f"Please rename files to 'Tab01_Document_Description_DDMmmYYYY.pdf' or supply manifest.json.\n"
            f"See references/filename-conventions.md for full specification."
        )

    documents.sort(key=lambda d: d["item_num"])
    return {
        "court": "SUPREME COURT OF BRITISH COLUMBIA",
        "registry": PLACEHOLDER_REGISTRY,
        "file_number": PLACEHOLDER_FILE_NUMBER,
        "style_of_cause": "IN THE SUPREME COURT OF BRITISH COLUMBIA",
        "hearing_date": "To be scheduled",
        "application_date": "Current Session",
        "inferred": True,
        "documents": documents
    }

def build_binder(inputs_dir: Path, output_file: Path, use_originals: bool = True) -> Path:
    """Assembles a court binder PDF from a folder of filings.

    Args:
        inputs_dir: Folder of filings (and optionally manifest.json).
        output_file: Where to write the binder.
        use_originals: When True (the default), a filing that is a readable PDF
            goes into the binder as its original pages (a true copy, as CSO
            requires). Filings that exist only as text are typeset from the text.

    Returns:
        The path of the written binder.
    """
    manifest_file = inputs_dir / "manifest.json"
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    else:
        print(f"No manifest.json found. Inferring document sequence from conforming filenames...")
        manifest = infer_manifest_from_files(inputs_dir)

    docs = manifest.get("documents", [])
    if not docs:
        raise ValueError("manifest contains no documents")

    # Defensive check: ensure no 0-byte or corrupt source files
    for d in docs:
        fname = d.get("filename", "")
        fpath = inputs_dir / fname
        if fpath.exists() and fpath.stat().st_size == 0:
            raise ValueError(f"Input document file is 0 bytes (corrupt/empty): {fname}")

    print(f"Loaded {len(docs)} document definitions for assembly.")

    court_name = manifest.get("court", "SUPREME COURT OF BRITISH COLUMBIA").upper()
    registry = manifest.get("registry", PLACEHOLDER_REGISTRY)
    file_no = manifest.get("file_number", PLACEHOLDER_FILE_NUMBER)
    subtitle_bar = f"{court_name} — {registry} Registry / No. {file_no}"

    # -------------------------------------------------------------------------
    # Ingest Documents and Partition into Paginated Page Blocks
    # -------------------------------------------------------------------------
    lines_per_page = 28
    doc_pages_map = [] # list of lists of page_dicts for each doc

    original_count = 0
    for d_idx, d in enumerate(docs):
        page_title = d.get("short_title", d.get("title", f"Document {d['item_num']}"))
        original = open_original_pdf(inputs_dir, d["filename"]) if use_originals else None
        doc_pages = []
        if original is not None:
            # True copy: one blank placeholder per original page; the real page is
            # spliced in after the binder skeleton is written.
            original_count += 1
            path, reader = original
            total_chunks = len(reader.pages)
            for p_idx, source_page in enumerate(reader.pages):
                try:
                    text = source_page.extract_text() or ""
                except Exception:
                    text = ""
                doc_pages.append({
                    "header": "", "subtitle": "", "lines": [],
                    "detect_lines": text.splitlines(),
                    "original": (str(path), p_idx),
                    "doc_idx": d_idx, "page_in_doc": p_idx + 1, "total_pages_in_doc": total_chunks,
                    "title": page_title if p_idx == 0 else None,
                })
        else:
            lines = load_document_lines(inputs_dir, d["filename"])
            print(f"WARNING: {d['filename']} has no source PDF, so its text was typeset again "
                  "(not a true copy of the original).")
            total_chunks = max(1, (len(lines) + lines_per_page - 1) // lines_per_page)
            for p_idx in range(total_chunks):
                chunk = lines[p_idx * lines_per_page : (p_idx + 1) * lines_per_page]
                doc_pages.append({
                    "header": f"{page_title} (Page {p_idx + 1} of {total_chunks})",
                    "subtitle": subtitle_bar,
                    "lines": chunk,
                    "doc_idx": d_idx,
                    "page_in_doc": p_idx + 1,
                    "total_pages_in_doc": total_chunks,
                    "title": page_title if p_idx == 0 else None,
                })

        # Without a manifest exhibit list, find exhibits from their stamps
        # ("This is Exhibit "A" referred to in ...") so they are still bookmarked.
        if not d.get("exhibits"):
            d["exhibits"] = detect_exhibits(doc_pages)

        # Exhibits become child bookmarks under their document's bookmark.
        for ex in d.get("exhibits", []):
            rel_p = ex.get("rel_page") or ex.get("page_offset", 1)
            if 1 <= rel_p <= len(doc_pages):
                ex_name = ex.get("letter", "Exhibit")
                if not ex_name.upper().startswith("EXHIBIT"):
                    ex_name = f"Exhibit {ex_name}"
                desc = ex.get("description", "")
                doc_pages[rel_p - 1].setdefault("exhibit_titles", []).append(
                    f"{ex_name}: {desc}" if desc else ex_name)

        doc_pages_map.append(doc_pages)

    if original_count:
        print(f"Using the original PDF pages for {original_count} of {len(docs)} filings (true copies).")

    bad_chars = unsupported_characters([line for pages in doc_pages_map for pg in pages for line in pg["lines"]])
    if bad_chars:
        print("WARNING: these characters cannot be shown in the binder font and were replaced with '?': "
              + " ".join(bad_chars))

    # -------------------------------------------------------------------------
    # Pass 1: Probing page counts and calculating folios across multi-page docs
    # -------------------------------------------------------------------------
    doc_folios = []
    current_folio = 1 # Folio 1 starts at first content document (Notice of Application)

    for doc_pages in doc_pages_map:
        doc_folios.append(current_folio)
        current_folio += len(doc_pages)

    total_content_pages = current_folio - 1
    total_pages = total_content_pages + 2 # +1 Cover, +1 Index

    print(f"Pass 1: Computed {total_content_pages} content folios across {len(docs)} substantive documents.")
    print(f"Pass 1: {total_content_pages} content pages plus the cover and the index.")

    # -------------------------------------------------------------------------
    # Pass 2: Synthesize PDF objects with Bookmarks, Links, PageLabels & InitialView
    # -------------------------------------------------------------------------
    page_entries = [] # list of page dicts

    # 1. Cover Page (Item 1)
    cover_txt_file = inputs_dir / COVER_FILE_NAME
    if cover_txt_file.exists():
        raw_lines = [l.rstrip() for l in cover_txt_file.read_text(encoding="utf-8").splitlines()]
        # wrap lines to <= 75
        cover_lines = []
        for l in raw_lines:
            if len(l) <= 75:
                cover_lines.append(l)
            else:
                cover_lines.extend(textwrap.wrap(l, width=75))
        cover_lines = cover_lines[:32]
    else:
        # Optional details are left off the title page when blank; nothing is invented.
        time_est = str(manifest.get("time_estimate", "")).strip()
        time_line = f"Time Estimate: {time_est} | Practice Direction 72 (PD-72)" if time_est else "Practice Direction 72 (PD-72)"
        counsel_lines = [
            f"{label}: {str(manifest.get(key, '')).strip()}"
            for label, key in (("Counsel for Applicant", "counsel_applicant"), ("Counsel for Respondent", "counsel_respondent"))
            if str(manifest.get(key, "")).strip()
        ]
        cover_lines = [
            f"No. {file_no}",
            f"{registry} Registry",
            "",
            f"IN THE {court_name}",
            "",
            "BETWEEN:",
            f"   {manifest.get('plaintiff', 'Plaintiff')}                  (Applicant / Plaintiff)",
            "AND:",
            f"   {manifest.get('defendant', 'Defendant')}                  (Respondent / Defendant)",
            "",
            "=========================================================================",
            "                 ELECTRONIC APPLICATION RECORD                           ",
            f"Hearing Date: {manifest.get('application_date', 'Chambers')} before an Associate Judge",
            time_line,
            "=========================================================================",
            "",
            *counsel_lines,
        ]

    page_entries.append({
        "header": f"IN THE {court_name}",
        "subtitle": f"{registry} Registry / Court File No. {file_no}",
        "lines": cover_lines,
        "stamp": None,
        "is_index": False,
        "title": "000 - Application Record Title Page",
        "parent": None
    })

    # 2. Index Page (Item 2) - Professional Legal Table Layout (Video 836310097)
    index_rows = []
    authorities_started = False
    app_date = manifest.get("application_date", "")

    for i, d in enumerate(docs):
        folio = doc_folios[i]
        title = d["title"]
        # Check if authority / case law
        is_auth = (d.get("item_num", 0) >= 5) or ("Authority" in title) or ("Tab 5" in title) or ("BCCA" in title) or ("BCSC" in title)
        if is_auth and not authorities_started:
            index_rows.append({
                "type": "heading",
                "text": "AUTHORITIES"
            })
            authorities_started = True

        doc_title = clean_display_title(title)
        doc_date = d.get("date") or extract_date_str(title, app_date)

        index_rows.append({
            "type": "item",
            "tab": str(d.get("item_num", i + 1)),
            "doc": doc_title,
            "date": doc_date,
            "folio": str(folio),
            "_folio": folio
        })

        # Handle exhibits under affidavits
        for ex in d.get("exhibits", []):
            rel_p = ex.get("rel_page") or ex.get("page_offset", 1)
            ex_folio = folio + rel_p - 1
            ex_desc = ex.get("description", "")
            ex_date = extract_date_str(ex_desc)
            clean_ex_desc = clean_display_title(ex_desc)
            ex_name = str(ex.get("letter", "Exhibit"))
            if not ex_name.upper().startswith("EXHIBIT"):
                ex_name = f"Exhibit {ex_name}"
            ex_label = f"- {ex_name}: {clean_ex_desc}" if clean_ex_desc else f"- {ex_name}"
            if len(ex_label) > 44:
                ex_label = ex_label[:41] + "..."

            index_rows.append({
                "type": "exhibit",
                "tab": "",
                "doc": ex_label,
                "date": ex_date,
                "folio": str(ex_folio),
                "_folio": ex_folio
            })

    # Split the index over as many pages as it needs, then point every row at its
    # page: cover (1) + index pages, then the content folio.
    index_pages = paginate_index_rows(index_rows)
    index_page_count = len(index_pages)
    for row in index_rows:
        if "_folio" in row:
            row["target_page_1based"] = row["_folio"] + 1 + index_page_count

    clickable_rows = [r for r in index_rows if "target_page_1based" in r]
    num_annots = len(clickable_rows)

    for part, page_rows in enumerate(index_pages, start=1):
        page_entries.append({
            "header": "INDEX TO APPLICATION RECORD",
            "subtitle": "Required under Supreme Court Civil Rule 8-1(15) and PD-72 Appendix A",
            "lines": [],
            "index_rows": page_rows,
            "index_part": part,
            "stamp": None,
            "is_index": True,
            "title": "001 - Application Record Index" if part == 1 else None,
            "parent": None
        })

    # Record actual front matter page count for dynamic /PageLabels synchronization
    front_matter_page_count = len(page_entries)

    # 3. Add Substantive Pages
    current_content_folio = 1
    for d_idx, doc_pages in enumerate(doc_pages_map):
        d_meta = docs[d_idx]
        for p_idx, p_data in enumerate(doc_pages):
            p_data["stamp"] = current_content_folio
            p_data["is_index"] = False
            current_content_folio += 1
            page_entries.append(p_data)

    # -------------------------------------------------------------------------
    # PDF Serialization Architecture (Fonts, Bookmarks, Annotations & Streams)
    # -------------------------------------------------------------------------
    num_pages = len(page_entries)
    
    # Precise Object ID Numbering:
    # 1: Catalog
    # 2: Pages Root
    # 3: Outlines Root
    # 4: Font Bold
    # 5: Font Regular
    # 6 .. 5 + num_pages: Page Objects (consecutive!)
    # 6 + num_pages .. 5 + 2*num_pages: Content Stream Objects (consecutive!)
    # 6 + 2*num_pages .. : Link Annotations
    # 6 + 2*num_pages + num_annots .. : Outline Bookmark Items
    
    catalog_idx = 1
    pages_root_idx = 2
    outlines_root_idx = 3
    font_bold_idx = 4
    font_reg_idx = 5

    page_obj_start = 6
    content_obj_start = page_obj_start + num_pages
    annot_obj_start = content_obj_start + num_pages
    outline_item_start = annot_obj_start + num_annots

    # 1. Catalog Object with /PageMode /UseOutlines and /PageLabels
    catalog_str = (
        f"<< /Type /Catalog /Pages {pages_root_idx} 0 R "
        f"/PageMode /UseOutlines "  # Initial View: open bookmarks navigation panel by default
        f"/Outlines {outlines_root_idx} 0 R "
        f"/PageLabels << /Nums [0 << >> {front_matter_page_count} << /S /D /St 1 >>] >> >>"
    )

    # 2. Pages Root Object
    kids_str = " ".join([f"{page_obj_start + p} 0 R" for p in range(num_pages)])
    pages_root_str = f"<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>"

    # Fonts
    font_bold_str = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
    font_reg_str = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"

    # Bookmark tree: the cover, index and each document are top-level items, and a
    # document's exhibits are its children.
    outline_nodes: list[dict] = []
    for p_idx, p_data in enumerate(page_entries):
        if p_data.get("title"):
            outline_nodes.append({"title": p_data["title"], "page_idx": p_idx, "children": []})
        for ex_title in p_data.get("exhibit_titles", []):
            outline_nodes[-1]["children"].append({"title": ex_title, "page_idx": p_idx, "children": []})

    next_outline_id = outline_item_start
    for node in outline_nodes:
        node["id"] = next_outline_id
        next_outline_id += 1
        for child in node["children"]:
            child["id"] = next_outline_id
            next_outline_id += 1
    outlines_count = next_outline_id - outline_item_start

    # Outlines Root Object
    first_outline_id = outline_nodes[0]["id"]
    last_outline_id = outline_nodes[-1]["id"]
    outlines_root_str = (
        f"<< /Type /Outlines /First {first_outline_id} 0 R /Last {last_outline_id} 0 R /Count {outlines_count} >>"
    )

    # Prepare Content Streams and Annotation Objects
    page_objects = []
    content_objects = []
    annot_objects = []
    outline_objects = []

    current_annot_id = annot_obj_start

    for p_idx, p_data in enumerate(page_entries):
        p_obj_id = page_obj_start + p_idx
        c_obj_id = content_obj_start + p_idx

        # Render Content Stream
        stream_text = ""

        # Top-center page number (14-16pt Arial/Helvetica Bold)
        if p_data["stamp"] is not None and not p_data.get("original"):
            stamp_s = str(p_data["stamp"])
            stream_text += f"BT\n/F1 15 Tf\n290 760 Td\n({stamp_s}) Tj\nET\n"

        if p_data.get("is_index"):
            # Render authentic, professional Legal Table Index (Karen's Video 836310097)
            esc_header = escape_pdf_text(
                "APPLICATION RECORD INDEX" + (" (continued)" if p_data.get("index_part", 1) > 1 else ""))
            esc_sub = escape_pdf_text("Required under Supreme Court Civil Rule 8-1(15) and PD-72 Appendix A")

            stream_text += (
                f"BT\n/F1 14 Tf\n54 720 Td\n({esc_header}) Tj\nET\n"
                f"BT\n/F2 10 Tf\n54 700 Td\n({esc_sub}) Tj\nET\n"
                # Table Headers
                f"BT\n/F1 10.5 Tf\n54 665 Td\n(TAB) Tj\nET\n"
                f"BT\n/F1 10.5 Tf\n94 665 Td\n(DOCUMENT) Tj\nET\n"
                f"BT\n/F1 10.5 Tf\n390 665 Td\n(DATE) Tj\nET\n"
                f"BT\n/F1 10.5 Tf\n525 665 Td\n(PAGE) Tj\nET\n"
                # Crisp 0.75pt horizontal rule under headers
                f"0.75 w\n54 655 m\n558 655 l\nS\n"
            )

            current_y = 632
            row_step = 22
            hyperlinks_with_coords = []

            for row in p_data["index_rows"]:
                if row["type"] == "heading":
                    # Authorities section divider
                    current_y -= 4
                    esc_hd = escape_pdf_text(row["text"])
                    stream_text += (
                        f"BT\n/F1 10.5 Tf\n54 {current_y} Td\n({esc_hd}) Tj\nET\n"
                        f"0.5 w\n54 {current_y - 2} m\n140 {current_y - 2} l\nS\n"
                    )
                    current_y -= (row_step - 2)
                    continue

                # Tab number
                if row["tab"]:
                    esc_tab = escape_pdf_text(row["tab"])
                    stream_text += f"BT\n/F1 10 Tf\n58 {current_y} Td\n({esc_tab}) Tj\nET\n"

                # Document description (indented for exhibits)
                x_doc = 114 if row["type"] == "exhibit" else 94
                font_name = "/F2"
                font_size = "9.5" if row["type"] == "exhibit" else "10"
                esc_doc = escape_pdf_text(row["doc"])
                stream_text += f"BT\n{font_name} {font_size} Tf\n{x_doc} {current_y} Td\n({esc_doc}) Tj\nET\n"

                # Date column
                if row.get("date"):
                    esc_date = escape_pdf_text(row["date"])
                    stream_text += f"BT\n/F2 9.5 Tf\n390 {current_y} Td\n({esc_date}) Tj\nET\n"

                # Page number right-aligned to X=554
                folio_str = row["folio"]
                x_page = 554 - (len(folio_str) * 6)
                stream_text += f"BT\n/F1 10 Tf\n{x_page} {current_y} Td\n({folio_str}) Tj\nET\n"

                # Record hyperlink geometry
                hyperlinks_with_coords.append((current_y, row["target_page_1based"]))
                current_y -= row_step

            # Check for annotations on Index page
            these_annot_ids = []
            for y_coord, target_page in hyperlinks_with_coords:
                these_annot_ids.append(f"{current_annot_id} 0 R")
                # Precise row bounding box: spans from X=50 to X=560, Y from y_coord - 4 to y_coord + 14
                rect_str = f"50 {y_coord - 4} 560 {y_coord + 14}"
                target_p_obj = page_obj_start + min(target_page - 1, num_pages - 1)

                link_obj_str = (
                    f"<< /Type /Annot /Subtype /Link "
                    f"/Rect [{rect_str}] "
                    f"/Border [0 0 0] " # Invisible rectangle (per Court PDF Guide 06 and Video 06:14)
                    f"/H /N "           # Highlight style: None (per Court PDF Guide 06 and Video 06:14)
                    f"/A << /S /GoTo /D [{target_p_obj} 0 R /FitH 792] >> " # Universal GoTo action
                    f"/Dest [{target_p_obj} 0 R /FitH 792] >>"             # Destination fallback
                )
                annot_objects.append((current_annot_id, link_obj_str))
                current_annot_id += 1

            annots_attr = f"/Annots [{' '.join(these_annot_ids)}] "
        elif p_data.get("original"):
            annots_attr = ""  # blank placeholder; the original page replaces it afterwards
        else:
            annots_attr = ""
            esc_header = escape_pdf_text(p_data["header"])
            esc_sub = escape_pdf_text(p_data["subtitle"])

            stream_text += (
                f"BT\n/F1 13 Tf\n54 720 Td\n({esc_header}) Tj\nET\n"
                f"BT\n/F2 10.5 Tf\n54 695 Td\n({esc_sub}) Tj\nET\n"
                f"BT\n/F2 9.5 Tf\n16 TL\n54 660 Td\n"
            )

            for l_idx, l in enumerate(p_data.get("lines", [])):
                esc_l = escape_pdf_text(l)
                if l_idx == 0:
                    stream_text += f"({esc_l}) Tj\n"
                else:
                    stream_text += f"T*\n({esc_l}) Tj\n"
            stream_text += "ET\n"

        stream_bytes = stream_text.encode(PDF_TEXT_ENCODING, errors="replace")
        c_str = f"<< /Length {len(stream_bytes)} >>\nstream\n{stream_text}endstream"
        content_objects.append((c_obj_id, c_str))

        page_str = (
            f"<< /Type /Page /Parent {pages_root_idx} 0 R "
            f"/MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_bold_idx} 0 R /F2 {font_reg_idx} 0 R >> >> "
            f"{annots_attr}"
            f"/Contents {c_obj_id} 0 R >>"
        )
        page_objects.append((p_obj_id, page_str))

    # Write the bookmark items (siblings are linked with /Prev and /Next)
    def write_outline_level(siblings: list[dict], parent_id: int) -> None:
        for pos, node in enumerate(siblings):
            prev_str = f"/Prev {siblings[pos - 1]['id']} 0 R " if pos > 0 else ""
            next_str = f"/Next {siblings[pos + 1]['id']} 0 R " if pos < len(siblings) - 1 else ""
            kids = node["children"]
            kids_str = (f"/First {kids[0]['id']} 0 R /Last {kids[-1]['id']} 0 R /Count {len(kids)} " if kids else "")
            target_page_obj = page_obj_start + node["page_idx"]
            outline_objects.append((node["id"], (
                f"<< /Title {pdf_title_string(node['title'])} "
                f"/Parent {parent_id} 0 R "
                f"{prev_str}{next_str}{kids_str}"
                f"/Dest [{target_page_obj} 0 R /Fit] >>"
            )))
            write_outline_level(kids, node["id"])

    write_outline_level(outline_nodes, outlines_root_idx)
    outline_objects.sort(key=lambda item: item[0])

    # Combine all parts in exact ascending object order
    ordered_objects = [
        (catalog_idx, catalog_str),
        (pages_root_idx, pages_root_str),
        (outlines_root_idx, outlines_root_str),
        (font_bold_idx, font_bold_str),
        (font_reg_idx, font_reg_str),
    ]
    ordered_objects.extend(page_objects)
    ordered_objects.extend(content_objects)
    ordered_objects.extend(annot_objects)
    ordered_objects.extend(outline_objects)

    # -------------------------------------------------------------------------
    # Serialize to Valid PDF 1.7 Stream with Byte Cross-Reference Offsets
    # -------------------------------------------------------------------------
    out = bytearray()
    out.extend(b"%PDF-1.7\n")

    offsets = {}

    for obj_id, obj_body in ordered_objects:
        offsets[obj_id] = len(out)
        obj_bytes = f"{obj_id} 0 obj\n{obj_body}\nendobj\n".encode(PDF_TEXT_ENCODING, errors="replace")
        out.extend(obj_bytes)

    total_objects = len(ordered_objects)
    xref_offset = len(out)

    # Write Cross-Reference (xref) Table
    xref_str = f"xref\n0 {total_objects + 1}\n0000000000 65535 f \n"
    for i in range(1, total_objects + 1):
        xref_str += f"{offsets[i]:010d} 00000 n \n"
    out.extend(xref_str.encode("utf-8"))

    # Trailer
    trailer_str = (
        f"trailer\n<< /Size {total_objects + 1} /Root {catalog_idx} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )
    out.extend(trailer_str.encode("utf-8"))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_bytes(bytes(out))

    originals = [
        (idx, Path(pd["original"][0]), pd["original"][1], pd["stamp"])
        for idx, pd in enumerate(page_entries) if pd.get("original")
    ]
    if originals:
        splice_original_pages(output_file, originals)

    file_size_bytes = output_file.stat().st_size
    file_size_mb = file_size_bytes / (1024.0 * 1024.0)
    print(f"\nSUCCESS: Generated authentic, fully-detailed Court Binder -> {output_file.resolve()}")
    print("Binder Statistics:")
    print(f"  - Total Pages: {num_pages} (cover, {index_page_count} index page{'s' if index_page_count != 1 else ''}, {total_content_pages} content)")
    print(f"  - Bookmarks Created: {outlines_count}")
    print(f"  - Index Hyperlinks: {num_annots}")
    print(f"  - File Size: {file_size_bytes:,} bytes ({file_size_mb:.4f} MB)")
    print(f"  - CSO Threshold (< 50 MB): {'PASS' if file_size_mb <= 50.0 else 'FAIL'}")

    return output_file

def main():
    parser = argparse.ArgumentParser(description="Assemble authentic BC Supreme Court Application Record.")
    parser.add_argument("--inputs", default="poc/court-binder/inputs/01-commercial-discovery", help="Folder containing manifest.json and documents")
    parser.add_argument("--output", default="poc/court-binder/output/01-commercial-discovery/Application_Record_Commercial_Document_Discovery_Rule_7-1_15Nov2026.pdf", help="Output PDF destination")
    parser.add_argument("--retypeset", action="store_true", help="Typeset filings from their text instead of using their original PDF pages")
    args = parser.parse_args()

    inputs_dir = Path(args.inputs)
    if not inputs_dir.exists():
        # Try finding relative to court-binder root
        poc_dir = Path(__file__).resolve().parents[4]
        candidate = poc_dir / args.inputs
        if candidate.exists():
            inputs_dir = candidate

    output_file = Path(args.output)
    if not output_file.is_absolute() and not output_file.parent.exists():
        poc_dir = Path(__file__).resolve().parents[4]
        output_file = poc_dir / args.output

    try:
        build_binder(inputs_dir, output_file, use_originals=not args.retypeset)
    except Exception as e:
        print(f"ERROR: Court Binder assembly failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
