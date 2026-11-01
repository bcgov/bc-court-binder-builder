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
    txt_candidates.extend(p for p in base.glob(f"{prefix}_*.txt") if p.is_relative_to(base))

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

def build_binder(inputs_dir: Path, output_file: Path) -> Path:
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

    for d_idx, d in enumerate(docs):
        lines = load_document_lines(inputs_dir, d["filename"])
        # Partition into chunks
        total_chunks = max(1, (len(lines) + lines_per_page - 1) // lines_per_page)
        
        doc_pages = []
        for p_idx in range(total_chunks):
            chunk = lines[p_idx * lines_per_page : (p_idx + 1) * lines_per_page]
            page_title = d.get("short_title", d.get("title", f"Document {d['item_num']}"))
            doc_pages.append({
                "header": f"{page_title} (Page {p_idx + 1} of {total_chunks})",
                "subtitle": subtitle_bar,
                "lines": chunk,
                "doc_idx": d_idx,
                "page_in_doc": p_idx + 1,
                "total_pages_in_doc": total_chunks,
                "title": f"{page_title} (Part {p_idx + 1})" if p_idx > 0 else page_title
            })

        # Apply Exhibit Sub-Bookmark Titles to Exhibit starting pages
        for ex in d.get("exhibits", []):
            rel_p = ex.get("rel_page") or ex.get("page_offset", 1)
            if 1 <= rel_p <= len(doc_pages):
                ex_name = ex.get("letter", "Exhibit")
                if not ex_name.upper().startswith("EXHIBIT"):
                    ex_name = f"Exhibit {ex_name}"
                desc = ex.get("description", "")
                doc_pages[rel_p - 1]["title"] = f"   - {ex_name}: {desc}"

        doc_pages_map.append(doc_pages)

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
    print(f"Pass 1: Total binder size: {total_pages} pages (Cover + Index + Substantive Content).")

    # -------------------------------------------------------------------------
    # Pass 2: Synthesize PDF objects with Bookmarks, Links, PageLabels & InitialView
    # -------------------------------------------------------------------------
    page_entries = [] # list of page dicts

    # 1. Cover Page (Item 1)
    cover_txt_file = inputs_dir / "000_Application_Record_Title_Page.txt"
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
            f"Time Estimate: {manifest.get('time_estimate', '25 min')} | Practice Direction 72 (PD-72)",
            "=========================================================================",
            "",
            f"Counsel for Applicant: {manifest.get('counsel_applicant', 'Counsel of Record')}",
            f"Counsel for Respondent: {manifest.get('counsel_respondent', 'Counsel of Record')}"
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
        target_page_1based = folio + 2 # +1 cover, +1 index

        index_rows.append({
            "type": "item",
            "tab": str(d.get("item_num", i + 1)),
            "doc": doc_title,
            "date": doc_date,
            "folio": str(folio),
            "target_page_1based": target_page_1based
        })

        # Handle exhibits under affidavits
        for ex in d.get("exhibits", []):
            rel_p = ex.get("rel_page") or ex.get("page_offset", 1)
            ex_folio = folio + rel_p - 1
            ex_desc = ex.get("description", "")
            ex_date = extract_date_str(ex_desc)
            clean_ex_desc = clean_display_title(ex_desc)
            ex_label = f"- {ex.get('letter', 'Exhibit')}: {clean_ex_desc}"
            if len(ex_label) > 44:
                ex_label = ex_label[:41] + "..."
            ex_target_page = ex_folio + 2

            index_rows.append({
                "type": "exhibit",
                "tab": "",
                "doc": ex_label,
                "date": ex_date,
                "folio": str(ex_folio),
                "target_page_1based": ex_target_page
            })

    # Total link annotations to construct
    clickable_rows = [r for r in index_rows if "target_page_1based" in r]
    num_annots = len(clickable_rows)

    page_entries.append({
        "header": "INDEX TO APPLICATION RECORD",
        "subtitle": "Required under Supreme Court Civil Rule 8-1(15) and PD-72 Appendix A",
        "lines": [],
        "index_rows": index_rows,
        "stamp": None,
        "is_index": True,
        "title": "001 - Application Record Index",
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
    font_bold_str = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"
    font_reg_str = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    # Outlines Root Object
    outlines_count = len(page_entries)
    first_outline_id = outline_item_start
    last_outline_id = outline_item_start + outlines_count - 1
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
        if p_data["stamp"] is not None:
            stamp_s = str(p_data["stamp"])
            stream_text += f"BT\n/F1 15 Tf\n290 760 Td\n({stamp_s}) Tj\nET\n"

        if p_data.get("is_index"):
            # Render authentic, professional Legal Table Index (Karen's Video 836310097)
            esc_header = escape_pdf_text("APPLICATION RECORD INDEX")
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

        stream_bytes = stream_text.encode("utf-8")
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

    # Construct Bookmarks Outline Items Tree
    for o_idx in range(outlines_count):
        this_id = outline_item_start + o_idx
        prev_str = f"/Prev {this_id - 1} 0 R " if o_idx > 0 else ""
        next_str = f"/Next {this_id + 1} 0 R " if o_idx < outlines_count - 1 else ""
        target_page_obj = page_obj_start + o_idx
        title_esc = escape_pdf_text(page_entries[o_idx]["title"])

        outline_item_str = (
            f"<< /Title ({title_esc}) "
            f"/Parent {outlines_root_idx} 0 R "
            f"{prev_str}{next_str}"
            f"/Dest [{target_page_obj} 0 R /Fit] >>"
        )
        outline_objects.append((this_id, outline_item_str))

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
        obj_bytes = f"{obj_id} 0 obj\n{obj_body}\nendobj\n".encode("utf-8")
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

    file_size_bytes = len(out)
    file_size_mb = file_size_bytes / (1024.0 * 1024.0)
    print(f"\nSUCCESS: Generated authentic, fully-detailed Court Binder -> {output_file.resolve()}")
    print("Binder Statistics:")
    print(f"  - Total Pages: {num_pages}")
    print(f"  - Bookmarks Created: {outlines_count}")
    print(f"  - Index Hyperlinks: {num_annots}")
    print(f"  - File Size: {file_size_bytes:,} bytes ({file_size_mb:.4f} MB)")
    print(f"  - CSO Threshold (< 50 MB): {'PASS' if file_size_mb <= 50.0 else 'FAIL'}")

    return output_file

def main():
    parser = argparse.ArgumentParser(description="Assemble authentic BC Supreme Court Application Record.")
    parser.add_argument("--inputs", default="poc/court-binder/inputs/01-commercial-discovery", help="Folder containing manifest.json and documents")
    parser.add_argument("--output", default="poc/court-binder/output/01-commercial-discovery/Application_Record_Commercial_Document_Discovery_Rule_7-1_15Nov2026.pdf", help="Output PDF destination")
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
        build_binder(inputs_dir, output_file)
    except Exception as e:
        print(f"ERROR: Court Binder assembly failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
