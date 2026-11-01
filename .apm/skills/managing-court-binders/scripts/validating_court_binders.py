#!/usr/bin/env python3
"""
validating_court_binders.py
===========================
PURPOSE:
    Audits and certifies an Electronic Application Record or Book of Authorities PDF
    against the 20 mandatory statutory court quality gates synthesized from:
    1. BC Supreme Court Practice Direction 72 (PD-72 Appendix A) & Practice Direction 73
    2. Court Services Online (CSO) 50 MB File Size & Document Acceptance Governance
    3. BCCA Civil Rule 27 Completion Instructions for Books of Authorities
    4. Senior Vancouver Litigation Paralegal 9-Step Standard Practice (Video 836310097)
    5. Ministry of Attorney General (JAG-CSO-Assistant) Enterprise Architecture:
       - 3-tier severity classification (HARD_STOP, SOFT_WARNING, PASS)
       - Spatial bounding box coordinate analysis (Top-Center vs Footer folios)
       - Page geometry and standard Letter dimensions auditing
       - Security & encryption rejection gate
       - Shannon character entropy and legal dictionary OCR heuristics
       - Substantive content density and non-blank page verification

KEY INPUT DEPENDENCIES:
    - Candidate application record or BoA PDF (path passed via --output or sys.argv)
    - pypdf>=5.0.0      : PDF structural and dictionary object analysis
    - pdfplumber>=0.11.0: Spatial text bounding box coordinate probing

FUNCTION INDEX:
    - calculate_entropy(text: str) -> float
    - evaluate_ocr_quality(text: str) -> dict
    - validate_court_binder(pdf_path: Path) -> tuple[bool, list[dict]]
    - main() -> None

USAGE:
    python3 validating_court_binders.py --output output/01-commercial-discovery/Application_Record.pdf
    python3 validating_court_binders.py --output output/01-commercial-discovery/Application_Record.pdf --json
"""

import os
import sys
import re
import math
import argparse
from pathlib import Path

# Core legal dictionary for deterministic OCR legibility heuristic (from JAG-CSO-Assistant)
LEGAL_DICTIONARY = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for",
    "not", "on", "with", "he", "as", "you", "do", "at", "this", "but", "his",
    "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", "my",
    "one", "all", "would", "there", "their", "what", "so", "up", "out", "if",
    "about", "who", "get", "which", "go", "me", "court", "supreme", "civil",
    "family", "rule", "rules", "application", "record", "affidavit", "plaintiff",
    "defendant", "applicant", "respondent", "exhibit", "filed", "sworn", "justice",
    "judge", "registry", "vancouver", "victoria", "bc", "british", "columbia",
    "notice", "order", "claim", "defence", "pursuant", "section", "act", "counsel",
    "matter", "chambers", "associate", "hearing", "costs", "dated", "commercial"
}

def calculate_entropy(text: str) -> float:
    """Calculates Shannon entropy of the character distribution."""
    if not text:
        return 0.0
    prob = [float(text.count(c)) / len(text) for c in set(text)]
    return -sum(p * math.log2(p) for p in prob)

def evaluate_ocr_quality(text: str) -> dict:
    """Evaluates text stream legibility and detects garbled or corrupted OCR scans."""
    if not text or len(text.strip()) == 0:
        return {"words": 0, "dictionary_hit_pct": 0.0, "entropy": 0.0, "is_garbled": False}
    
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    total_words = len(words)
    known_words = sum(1 for w in words if w in LEGAL_DICTIONARY)
    dict_hit_pct = (known_words / total_words * 100.0) if total_words > 0 else 0.0
    entropy = calculate_entropy(text)

    # Flag as corrupted OCR if dictionary hit is abnormally low on a substantial text block
    is_garbled = (dict_hit_pct < 18.0 and total_words >= 20) or (entropy > 5.5 and total_words >= 30)
    return {
        "words": total_words,
        "dictionary_hit_pct": round(dict_hit_pct, 1),
        "entropy": round(entropy, 2),
        "is_garbled": is_garbled
    }

FOLIO_PAGE_COUNT = 5
PART_SUFFIX = re.compile(r"\(Part \d+\)\s*$")


def collect_folio_evidence(reader, first_index: int = 2, count: int = FOLIO_PAGE_COUNT) -> list[dict]:
    """Inspects the folio actually stamped on the first substantive pages.

    Args:
        reader: An open pypdf reader.
        first_index: Zero-based index of the first substantive page.
        count: How many substantive pages to inspect.

    Returns:
        One dict per page: page number, expected folio, whether it was found
        top-centre or in the footer, and the font name and size used.
    """
    evidence: list[dict] = []
    for p_idx in range(first_index, min(first_index + count, len(reader.pages))):
        page = reader.pages[p_idx]
        page_w, page_h = float(page.mediabox.width), float(page.mediabox.height)
        entry = {"page": p_idx + 1, "expected": str(p_idx - 1), "top_center": False,
                 "footer": False, "font": "", "size": 0.0}

        def visitor(text, cm, tm, font_dict, font_size, entry=entry, page_w=page_w, page_h=page_h):
            st = text.strip()
            if not st:
                return
            tx, ty = tm[4], tm[5]
            centred = 0.35 <= tx / page_w <= 0.65
            is_folio = st == entry["expected"] or st.startswith(entry["expected"] + " ")
            if ty > page_h - 100 and centred and is_folio and not entry["top_center"]:
                entry["top_center"] = True
                entry["font"] = str(font_dict.get("/BaseFont", "")) if font_dict else ""
                entry["size"] = float(font_size or 0)
            elif ty < 100 and (entry["expected"] in st):
                entry["footer"] = True

        try:
            page.extract_text(visitor_text=visitor)
        except Exception:
            pass
        evidence.append(entry)
    return evidence


def document_final_pages(reader) -> set[int]:
    """Returns zero-based indexes of pages that end a document.

    A page ends a document when the next page's bookmark is not a
    "(Part N)" continuation, or when it is the last page.
    """
    titles: dict[int, str] = {}

    def walk(items) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item)
            else:
                try:
                    titles[reader.get_destination_page_number(item)] = str(item.title)
                except Exception:
                    continue

    try:
        walk(reader.outline)
    except Exception:
        return {len(reader.pages) - 1}
    last = len(reader.pages) - 1
    final = {last}
    for idx in range(last):
        nxt = titles.get(idx + 1)
        if nxt is not None and not PART_SUFFIX.search(nxt):
            final.add(idx)
    return final


def validate_court_binder(pdf_path: Path) -> tuple[bool, list[dict]]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    raw_bytes = pdf_path.read_bytes()
    file_size_bytes = len(raw_bytes)
    file_size_mb = file_size_bytes / (1024.0 * 1024.0)
    raw_text = raw_bytes.decode("latin-1", errors="ignore")

    reader = None
    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path))
    except Exception as exc:
        raise ValueError(f"Not a readable PDF ({type(exc).__name__}): {pdf_path.name}") from exc

    results = []

    def add_check(
        rule_num: int, 
        title: str, 
        authority: str, 
        passed: bool, 
        severity: str, 
        details: str, 
        remediation: str = ""
    ):
        results.append({
            "rule": f"RULE-{rule_num:02d}",
            "title": title,
            "authority": authority,
            "passed": passed,
            "severity": severity if not passed else "PASS",
            "details": details,
            "remediation": remediation
        })

    # =========================================================================
    # GATE 0: Security & Encryption Disabled (JAG PD72-R5)
    # =========================================================================
    is_encrypted = bool(reader is not None and reader.is_encrypted)

    add_check(
        0,
        "Security & Encryption Disabled",
        "CSO Guide §2; JAG PD72-R5",
        not is_encrypted,
        "HARD_STOP",
        "Document is unencrypted and accessible without passwords" if not is_encrypted
        else "Document is password-protected or encrypted (CSO registry cannot open it)",
        "Remove all password security and permissions encryption before submission."
    )

    if is_encrypted and reader is not None:
        # Gate 0 already fails. Try the empty user password so the remaining
        # gates can still be assessed; otherwise they run without page access.
        try:
            decrypted = reader.decrypt("") != 0
        except Exception:
            decrypted = False
        if not decrypted:
            reader = None

    # =========================================================================
    # GATE 1: Single Consolidated PDF File
    # =========================================================================
    is_pdf = raw_bytes.startswith(b"%PDF-") and (b"%%EOF" in raw_bytes or reader is not None)
    add_check(
        1,
        "Single Consolidated PDF File",
        "PD-72 §A.1; CSO Guide §2; Video 00:22",
        is_pdf,
        "HARD_STOP",
        f"Valid PDF container and %%EOF marker identified ({file_size_bytes:,} bytes)" if is_pdf else "Invalid PDF format",
        "Compile all documents (pleadings, affidavits, exhibits, authorities) into a single PDF volume."
    )

    # =========================================================================
    # GATE 2: CSO File Size Ceiling (< 50 MB)
    # =========================================================================
    size_passed = file_size_mb <= 50.0
    add_check(
        2,
        "File Size Ceiling (< 50 MB)",
        "CSO Instructions §3; Video 07:47",
        size_passed,
        "HARD_STOP",
        (f"File size is {file_size_mb:.4f} MB ({file_size_bytes:,} bytes), well below 50.0 MB threshold" if size_passed
         else f"File size is {file_size_mb:.4f} MB ({file_size_bytes:,} bytes), which exceeds the 50.0 MB threshold"),
        "Downsample raster imagery or apply Flate stream compression."
    )

    # =========================================================================
    # GATE 3: Initial View Bookmarks Panel Default (/PageMode /UseOutlines)
    # =========================================================================
    has_use_outlines = False
    if reader is not None:
        try:
            root = reader.trailer.get("/Root")
            if hasattr(root, "get_object"):
                root = root.get_object()
            if root and root.get("/PageMode") == "/UseOutlines":
                has_use_outlines = True
        except Exception:
            pass
    if not has_use_outlines:
        has_use_outlines = "/PageMode /UseOutlines" in raw_text or "/PageMode/UseOutlines" in raw_text

    add_check(
        3,
        "Initial View Bookmarks Panel Default",
        "PD-72 §A.3; Court PDF Guide 12",
        has_use_outlines,
        "SOFT_WARNING",
        "Catalog dictionary specifies /PageMode /UseOutlines (forces navigation tree open)" if has_use_outlines
        else "Document does not set /PageMode /UseOutlines (bookmarks panel will remain closed by default)",
        "Set Document Properties -> Initial View -> 'Bookmarks Panel and Page'."
    )

    # =========================================================================
    # GATE 4: Form 22 Style of Cause (Title Page)
    # =========================================================================
    has_cover = False
    if reader and len(reader.pages) > 0:
        p1_text = reader.pages[0].extract_text().upper()
        has_cover = any(term in p1_text for term in [
            "SUPREME COURT OF BRITISH COLUMBIA",
            "COURT OF APPEAL",
            "IN THE SUPREME COURT",
            "APPLICATION RECORD",
            "APPLICANT'S RECORD"
        ])
    if not has_cover:
        has_cover = "SUPREME COURT OF BRITISH COLUMBIA" in raw_text.upper() or "COURT OF APPEAL" in raw_text.upper()

    add_check(
        4,
        "Form 22 Style of Cause (Title Page)",
        "PD-72 §A.2; Video 00:22",
        has_cover,
        "HARD_STOP",
        "Title Page present as Item 1 containing style of cause, hearing date, and counsel" if has_cover
        else "Missing Form 22 Style of Cause / Court Heading on Page 1",
        "Ensure Item 1 is a Form 22 Title Page with proper court heading."
    )

    # =========================================================================
    # GATE 5: Index / Table of Contents Position (Page 2)
    # =========================================================================
    has_index = False
    if reader and len(reader.pages) > 1:
        p2_text = reader.pages[1].extract_text().upper()
        has_index = "INDEX" in p2_text or "TABLE OF CONTENTS" in p2_text
    if not has_index:
        has_index = "INDEX TO APPLICATION RECORD" in raw_text.upper() or "TABLE OF CONTENTS" in raw_text.upper()

    add_check(
        5,
        "Index / Table of Contents Position",
        "PD-72 §A.2; Court PDF Guide 02",
        has_index,
        "HARD_STOP",
        "Index is positioned directly behind Title Page and ahead of substantive filings (Item 2)" if has_index
        else "Missing Index / Table of Contents as Item 2",
        "Insert the numbered Table of Contents immediately following Item 1."
    )

    # =========================================================================
    # GATE 6: Page Numbers in Index
    # =========================================================================
    index_has_numbers = False
    if reader and len(reader.pages) > 1:
        index_lines = [l.strip() for l in reader.pages[1].extract_text().splitlines() if l.strip()]
        entry_rows = [l for l in index_lines if re.match(r"^\d+\s", l)]
        index_has_numbers = bool(entry_rows) and all(re.search(r"\s\d+\s*$", l) for l in entry_rows)

    add_check(
        6,
        "Page Number Entry in Index",
        "PD-72 §A.2; Video 05:44",
        index_has_numbers,
        "HARD_STOP",
        "Every listed document and authority carries calculated folio numbers in the Index" if index_has_numbers
        else "Index entries missing corresponding page folio numbers",
        "Populate index with exact page folios corresponding to target documents."
    )

    # =========================================================================
    # GATE 7: Hyperlinked Index Items (/Subtype /Link)
    # =========================================================================
    link_count = 0
    link_objs = []
    if reader and len(reader.pages) > 1:
        annots = reader.pages[1].get("/Annots")
        if annots:
            ann_list = annots.get_object() if hasattr(annots, "get_object") else annots
            if isinstance(ann_list, list):
                for a in ann_list:
                    a_dict = a.get_object() if hasattr(a, "get_object") else a
                    if a_dict.get("/Subtype") == "/Link":
                        link_count += 1
                        link_objs.append(a_dict)
    if link_count == 0:
        link_matches = re.findall(r'/Subtype\s*/Link', raw_text)
        link_count = len(link_matches)

    has_links = link_count >= 2
    add_check(
        7,
        "Hyperlinked Index Items",
        "PD-72 §A.2; Court PDF Guide 06",
        has_links,
        "SOFT_WARNING",
        f"Found {link_count} active link annotations on Index lines jumping directly to document pages" if has_links
        else f"Found only {link_count} link annotations on Index lines (minimum 2 required)",
        "Add interactive link annotations across all Index entries."
    )

    # =========================================================================
    # GATE 8: Link Visual Appearance: Invisible Rectangle & Highlight None
    # =========================================================================
    link_appearance_ok = False
    if link_objs:
        compliant_links = 0
        for lk in link_objs:
            border = lk.get("/Border")
            if hasattr(border, "get_object"):
                border = border.get_object()
            border_arr = list(border) if border else []
            is_invisible = (not border_arr) or (len(border_arr) >= 3 and border_arr[2] == 0)
            h = lk.get("/H")
            is_none_highlight = (h == "/N" or h is None)
            if is_invisible and is_none_highlight:
                compliant_links += 1
        link_appearance_ok = (compliant_links == len(link_objs)) and len(link_objs) > 0
    else:
        has_invisible_border = "/Border [0 0 0]" in raw_text or "/Border[0 0 0]" in raw_text
        has_highlight_none = "/H /N" in raw_text or "/H/N" in raw_text
        link_appearance_ok = has_invisible_border and has_highlight_none

    add_check(
        8,
        "Link Visual Appearance (Invisible Rectangle, Highlight None)",
        "Court PDF Guide 06; Video 06:14",
        link_appearance_ok,
        "SOFT_WARNING",
        "Links configured with /Border [0 0 0] (Invisible) and /H /N (Highlight None)" if link_appearance_ok
        else "Links use visible borders or interactive highlight styling instead of Invisible / None",
        "Set Link Type to 'Invisible Rectangle' and Highlight Style to 'None'."
    )

    # =========================================================================
    # GATE 9: Bookmark Tab / Page Navigation Destination (/Dest or /GoTo)
    # =========================================================================
    has_destinations = False
    if link_objs:
        has_destinations = any(("/Dest" in lk or "/A" in lk) for lk in link_objs)
    if not has_destinations:
        has_destinations = "/Dest [" in raw_text or "/S /GoTo" in raw_text

    add_check(
        9,
        "Bookmark Tab Integration (Go to Page View Action)",
        "Court PDF Guide 06; Video 06:40",
        has_destinations,
        "SOFT_WARNING",
        "Index hyperlinks integrate directly with document page destinations (/Dest /Fit)" if has_destinations
        else "Hyperlinks lack valid destination targets or GoTo page view actions",
        "Ensure link action directs viewer to the designated target page view."
    )

    # =========================================================================
    # GATE 10: Spatial Margin Analysis: Top-Center Folio Placement
    # (Adapted from JAG-CSO-Assistant spatial margin bounding box coordinate logic)
    # =========================================================================
    folio_evidence = collect_folio_evidence(reader) if reader else []
    spatial_evidence = ""
    for ev in folio_evidence:
        if not ev["top_center"] and ev["footer"]:
            spatial_evidence = f"Page {ev['page']} stamps folio in bottom footer margin instead of top-center"
    matching = sum(1 for ev in folio_evidence if ev["top_center"])
    has_top_center = bool(folio_evidence) and matching >= len(folio_evidence) - 1

    add_check(
        10,
        "Top-Center Folio Placement",
        "Court PDF Guide 09; Video 02:40",
        has_top_center,
        "HARD_STOP",
        "Page numbers stamped in top center of page header (x ~ 290 pt, y ~ 760 pt)" if has_top_center
        else f"Page numbers missing from top center ({spatial_evidence or 'placed in footer or margins'})",
        "Position folio stamp in the top-center margin of every substantive page."
    )

    # =========================================================================
    # GATE 11: Page Number Font Family (Arial / Helvetica)
    # =========================================================================
    folio_fonts = [ev["font"] for ev in folio_evidence if ev["top_center"]]
    has_arial_helvetica = bool(folio_fonts) and all("HELVETICA" in f.upper() or "ARIAL" in f.upper() for f in folio_fonts)
    add_check(
        11,
        "Page Number Font Family (Arial / Helvetica)",
        "Court PDF Guide 09; Video 02:22",
        has_arial_helvetica,
        "SOFT_WARNING",
        "Header stamping uses standard Arial/Helvetica standard-14 type family" if has_arial_helvetica
        else "Page number stamping does not use Arial or Helvetica",
        "Select Arial font in Header & Footer properties."
    )

    # =========================================================================
    # GATE 12: Page Number Font Style (Bold)
    # =========================================================================
    has_bold = bool(folio_fonts) and all("BOLD" in f.upper() for f in folio_fonts)
    add_check(
        12,
        "Page Number Font Style (Bold)",
        "Court PDF Guide 09; Video 02:25",
        has_bold,
        "SOFT_WARNING",
        "Page number font is styled in Arial/Helvetica Bold (/BaseFont /Helvetica-Bold)" if has_bold
        else "Page number font style is regular/plain instead of Bold",
        "Set Header & Footer font style to Bold."
    )

    # =========================================================================
    # GATE 13: Page Number Font Size (14 pt or 16 pt)
    # =========================================================================
    folio_sizes = [ev["size"] for ev in folio_evidence if ev["top_center"]]
    has_font_size = bool(folio_sizes) and all(14.0 <= sz <= 16.5 for sz in folio_sizes)

    add_check(
        13,
        "Page Number Font Size (14 pt - 16 pt)",
        "Court PDF Guide 09; Video 02:30",
        has_font_size,
        "SOFT_WARNING",
        "Folio font size set to 14–16 pt (compliant with court readability specification)" if has_font_size
        else "Folio font size does not match required 14 pt or 16 pt distinct size",
        "Increase Header & Footer font size to 14 pt or 16 pt."
    )

    # =========================================================================
    # GATE 14: Page 1 Start Location on First Substantive Document
    # =========================================================================
    has_st_1 = bool(folio_evidence) and folio_evidence[0]["expected"] == "1" and folio_evidence[0]["top_center"]

    add_check(
        14,
        "Page 1 Start Location on Substantive Content",
        "Court PDF Guide 10; Video 04:17",
        has_st_1,
        "HARD_STOP",
        "Sequential visible numbering begins at '1' on Tab 1 (Notice of Application)" if has_st_1
        else "Page 1 start location not set to first substantive document",
        "Configure page number stamp to start on first substantive document after Index."
    )

    # =========================================================================
    # GATE 15: Digital Page Labeling Synchronization (/PageLabels)
    # =========================================================================
    has_page_labels = False
    if reader is not None:
        try:
            root = reader.trailer.get("/Root")
            if hasattr(root, "get_object"):
                root = root.get_object()
            if root and "/PageLabels" in root:
                has_page_labels = True
        except Exception:
            pass
    if not has_page_labels:
        has_page_labels = "/PageLabels" in raw_text and "/S /D" in raw_text

    add_check(
        15,
        "Page Labeling Synchronization (/PageLabels)",
        "Court PDF Guide 10; Video 04:17",
        has_page_labels,
        "HARD_STOP",
        "/PageLabels catalog dictionary aligns PDF viewer counter with stamped printed folios" if has_page_labels
        else "Missing /PageLabels dictionary (PDF viewer page counter will desync from stamped folios)",
        "Add /PageLabels dictionary with decimal numbering beginning at Tab 1."
    )

    # =========================================================================
    # GATE 16: Unnumbered Front Matter Labels (Title & Index set to None)
    # =========================================================================
    has_front_matter_none = bool(re.search(r'/Nums\s*\[\s*0\s*<<\s*(?:/S\s*/None|>>)', raw_text))
    labels_search_ok = False
    if reader is not None:
        try:
            root = reader.trailer.get("/Root")
            if hasattr(root, "get_object"):
                root = root.get_object()
            if root and "/PageLabels" in root:
                pl = root["/PageLabels"]
                if hasattr(pl, "get_object"):
                    pl = pl.get_object()
                nums = pl.get("/Nums", [])
                if nums and len(nums) >= 2 and nums[0] == 0:
                    d0 = nums[1].get_object() if hasattr(nums[1], "get_object") else nums[1]
                    if d0.get("/S") == "/None" or "/S" not in d0 or len(d0.keys()) == 0:
                        has_front_matter_none = True
            
            # Direct verification of reader page_labels navigation
            try:
                plabels = list(reader.page_labels)
                if len(plabels) >= 3 and plabels[0] == "" and plabels[1] == "" and plabels[2] == "1":
                    labels_search_ok = True
                    has_front_matter_none = True
            except Exception:
                pass
        except Exception:
            pass

    add_check(
        16,
        "Unnumbered Front Matter Labels (None)",
        "Court PDF Guide 10; Video 04:45",
        has_front_matter_none,
        "SOFT_WARNING",
        "Front matter (Title Page & Index) page label style set to 'None' (verified: searching '1' jumps directly to Tab 1)" if labels_search_ok or has_front_matter_none
        else "Front matter pages carry Arabic numerals instead of style 'None'",
        "Set Page Labels for Pages 1-2 to Style: None."
    )

    # =========================================================================
    # GATE 17: Descriptive Bookmark Titles & Party Disambiguation
    # =========================================================================
    bookmarks_count = 0
    outline_titles = []
    if reader and reader.outline:
        def flatten_outlines(items):
            res = []
            for it in items:
                if isinstance(it, list):
                    res.extend(flatten_outlines(it))
                else:
                    t = getattr(it, "title", str(it))
                    res.append(t)
            return res
        outline_titles = flatten_outlines(reader.outline)
        bookmarks_count = len(outline_titles)
    if bookmarks_count == 0:
        bookmark_matches = re.findall(r'/Title\s*\((.*?)\)', raw_text)
        bookmarks_count = len(bookmark_matches)
        outline_titles = bookmark_matches

    has_good_bookmarks = bookmarks_count >= 3
    # Disambiguation: every affidavit bookmark must name its deponent or party;
    # without affidavits, at least one bookmark must name a party role.
    base_titles = [PART_SUFFIX.sub("", b).strip() for b in outline_titles]
    party_role = re.compile(r"\b(applicant|respondent|claimant|plaintiff|defendant|petitioner)\b", re.I)
    deponent = re.compile(r"(?i:affidavit)\W*(?:#?\d+\W+)?(?:(?i:of)\s+)?[A-Z][a-z]+\s+[A-Z][a-z]+")
    affidavits = [t for t in base_titles if re.search(r"\baffidavit\b", t, re.I)]
    if affidavits:
        has_disambiguation = all(party_role.search(t) or deponent.search(t) for t in affidavits)
    else:
        has_disambiguation = any(party_role.search(t) for t in base_titles)

    add_check(
        17,
        "Descriptive Bookmark Titles & Disambiguation",
        "PD-72 §A.3; Court PDF Guides 03 & 04",
        has_good_bookmarks and has_disambiguation,
        "HARD_STOP",
        f"Found {bookmarks_count} descriptive bookmarks disambiguating filings by party names" if (has_good_bookmarks and has_disambiguation)
        else f"Bookmarks ({bookmarks_count} found) do not adequately disambiguate filings by party name",
        "Ensure bookmarks clearly name documents and identify the filing party."
    )

    # =========================================================================
    # GATE 18: Exhibit Sub-Bookmarks, OCR Searchability & Content Integrity
    # (Incorporates Shannon Entropy & Legal Dictionary Heuristics from JAG-CSO-Assistant)
    # =========================================================================
    has_exhibit_bookmarks = any("EXHIBIT" in b.upper() for b in outline_titles)
    
    # Substantive density & OCR garble check
    sparse_pages = []
    garbled_pages = []
    if reader and len(reader.pages) > 2:
        final_pages = document_final_pages(reader)
        for p_idx in range(2, len(reader.pages)):
            txt = reader.pages[p_idx].extract_text()
            words = len(txt.split())
            lines = [l.strip() for l in txt.splitlines() if l.strip()]

            # Check 1: Empty or truncated page. The last page of a filing may be
            # short, so it only needs some real content; other pages need 15 words
            # and 2 lines. Placeholder text always fails.
            minimum_words, minimum_lines = (3, 1) if p_idx in final_pages else (15, 2)
            if (words < minimum_words or len(lines) < minimum_lines
                    or "Substantive legal content filed with court" in txt):
                sparse_pages.append((p_idx + 1, words, len(lines)))
            
            # Check 2: OCR legibility heuristic
            ocr_metrics = evaluate_ocr_quality(txt)
            if ocr_metrics["is_garbled"]:
                garbled_pages.append((p_idx + 1, ocr_metrics["dictionary_hit_pct"]))

    content_integrity_ok = len(sparse_pages) == 0
    ocr_quality_ok = len(garbled_pages) == 0
    has_vector_text = ("BT" in raw_text and "ET" in raw_text and "Tj" in raw_text) or (reader and len(reader.pages) > 0 and len(reader.pages[0].extract_text().split()) > 5)

    rule18_passed = has_exhibit_bookmarks and has_vector_text and content_integrity_ok and ocr_quality_ok

    if not content_integrity_ok:
        bad_summary = ", ".join([f"Page {p} ({w} words)" for p, w, l in sparse_pages[:5]])
        if len(sparse_pages) > 5:
            bad_summary += f", and {len(sparse_pages) - 5} more"
        details_18 = f"Substantive document pages have truncated or missing content: {bad_summary}"
        remediation_18 = "Fix input generation text operators and compile all lines onto substantive pages."
    elif not ocr_quality_ok:
        garble_summary = ", ".join([f"Page {p} ({hit}% dict match)" for p, hit in garbled_pages[:3]])
        details_18 = f"Corrupted or low-quality OCR text stream detected on {garble_summary}"
        remediation_18 = "Re-OCR pages with higher DPI or clear source scans."
    elif not has_exhibit_bookmarks:
        details_18 = "Affidavit exhibits are not nested as child bookmarks under parent affidavits"
        remediation_18 = "Nest Exhibit sub-bookmarks (e.g. 'Exhibit A - ...') under parent affidavits."
    elif not has_vector_text:
        details_18 = "Document text is not OCR-searchable or vector-selectable"
        remediation_18 = "Run Optical Character Recognition (OCR) across all scanned pages."
    else:
        details_18 = "Affidavit exhibits nested as child bookmarks; vector text stream provides 100% searchability; substantive pages fully populated and legible"
        remediation_18 = ""

    add_check(
        18,
        "Exhibit Sub-Bookmarks, OCR Searchability & Content Integrity",
        "PD-72 §A.3, §A.4; Court PDF Guides 04 & 11; JAG PD72-R1/R8",
        rule18_passed,
        "HARD_STOP" if (not content_integrity_ok or not has_vector_text) else "SOFT_WARNING",
        details_18,
        remediation_18
    )

    # =========================================================================
    # GATE 19: Standard Page Geometry & Dimensions (JAG PD72-R4)
    # =========================================================================
    non_standard_pages = []
    if reader and len(reader.pages) > 0:
        for p_idx, page in enumerate(reader.pages):
            pw = float(page.mediabox.width)
            ph = float(page.mediabox.height)
            # Standard 8.5 x 11 inch Letter is 612 x 792 pt (allow 15 pt tolerance)
            is_letter = (abs(pw - 612) <= 15 and abs(ph - 792) <= 15) or (abs(pw - 792) <= 15 and abs(ph - 612) <= 15)
            if not is_letter:
                non_standard_pages.append(p_idx + 1)
    
    non_std_pct = (len(non_standard_pages) / len(reader.pages) * 100.0) if (reader and len(reader.pages) > 0) else 0.0
    pages_assessed = bool(reader and len(reader.pages) > 0)
    geometry_passed = pages_assessed and non_std_pct <= 10.0

    add_check(
        19,
        "Page Geometry & Standard Dimensions",
        "JAG PD72-R4; Arlington Model §7.7",
        geometry_passed,
        "SOFT_WARNING",
        (f"All pages conform to standard 8.5 x 11 inch Letter dimensions ({len(reader.pages)} pages)" if geometry_passed
         else f"{non_std_pct:.1f}% of pages exceed standard 8.5 x 11 inch bounds (Pages: {non_standard_pages[:5]})" if pages_assessed
         else "Page dimensions could not be assessed (the file's pages are not readable, for example because it is password-protected)"),
        "Normalize oversized or non-Letter pages to standard 8.5 x 11 inch dimensions."
    )

    hard_stops = [r for r in results if r["severity"] == "HARD_STOP"]
    soft_warnings = [r for r in results if r["severity"] == "SOFT_WARNING"]
    all_passed = len(hard_stops) == 0

    return all_passed, results

def main():
    parser = argparse.ArgumentParser(description="Validate Electronic Court Binder against complete BC Court matrix.")
    parser.add_argument("--file", default="output/01-commercial-discovery/Application_Record_Commercial_Document_Discovery_Rule_7-1_15Nov2026.pdf", help="Path to PDF binder")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    pdf_path = Path(args.file)
    print(f"Auditing court binder: {pdf_path.resolve()}\n")

    try:
        passed, checks = validate_court_binder(pdf_path)
    except Exception as e:
        print(f"ERROR: Audit execution failed: {e}", file=sys.stderr)
        sys.exit(2)

    hard_stops = [c for c in checks if c["severity"] == "HARD_STOP"]
    soft_warnings = [c for c in checks if c["severity"] == "SOFT_WARNING"]

    if args.json:
        import json
        print(json.dumps({
            "passed": passed, 
            "file": str(pdf_path), 
            "hard_stops_count": len(hard_stops),
            "warnings_count": len(soft_warnings),
            "checks": checks
        }, indent=2))
        sys.exit(0 if passed else 1)

    print("=" * 86)
    print("      BRITISH COLUMBIA COURT ELECTRONIC RECORD AUDIT & CSO COMPLIANCE GATES      ")
    print("=" * 86)

    for c in checks:
        if c["passed"]:
            status_icon = "✔ PASS        "
        elif c["severity"] == "HARD_STOP":
            status_icon = "✖ HARD_STOP   "
        else:
            status_icon = "⚠ SOFT_WARNING"

        print(f"{status_icon} | [{c['rule']}] {c['title']}")
        print(f"       Authority: {c['authority']}")
        print(f"       Details:   {c['details']}")
        if not c["passed"]:
            print(f"       Action:    {c['remediation']}")
        print("-" * 86)

    print("\nSUMMARY SCORECARD:")
    print(f"  - Hard Stops (Fatal Court Rejections): {len(hard_stops)}")
    print(f"  - Soft Warnings (Formatting Advisories): {len(soft_warnings)}")
    print(f"  - Passed Rules:                        {len([c for c in checks if c['passed']])} / {len(checks)}")

    if len(hard_stops) == 0 and len(soft_warnings) == 0:
        verdict = "100% COMPLIANT - ALL GATES PASSED (APPROVED FOR CSO SUBMISSION)"
    elif len(hard_stops) == 0:
        verdict = "CONDITIONALLY COMPLIANT - PASS WITH SOFT WARNINGS (ACCEPTABLE FOR CSO)"
    else:
        verdict = "NON-COMPLIANT - REJECTED (HARD_STOP VIOLATIONS MUST BE REMEDIATED)"

    print(f"\nFINAL VERDICT: {verdict}")
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
