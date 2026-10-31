# British Columbia Electronic Application Record & Book of Authorities Specification
### Complete Synthesis of BC Court Practice Directions, CSO User Guides, and Professional Paralegal Practice

This document synthesizes:
1. **BC Supreme Court Practice Direction 72 (PD-72):** *Electronic Application Records (Associate Judges Chambers Pilot Project)*
2. **BC Supreme Court Practice Direction 73 (PD-73):** *Virtual Chambers*
3. **Court Services Online (CSO) User Guide:** *Instructions for Users for Application Records*
4. **BC Court of Appeal:** *E-Completion Instructions for Books of Authorities (Civil Rule 27)*
5. **BC Supreme Court 13-Part PDF Instructions Library:** (Page numbering, bookmarking, initial view, hyperlinks, OCR, Bates numbering)
6. **Professional Litigation Practice:** 20-Year Vancouver Senior Paralegal Video Workflow (`https://vimeo.com/836310097/44b6e64b67`)

---

## 🏛️ 1. Legal & Regulatory Requirements Matrix

| Parameter | BC Court Requirement | Source Reference | SDK Automation Capability |
| :--- | :--- | :--- | :--- |
| **Document Ordering** | Mandatory order: (1) Title Page / Cover, (2) Index, (3) Notice of Application, (4) Application Response(s), (5) Affidavits with Exhibits, (6) Written Argument, (7) Draft Order, (8) Authorities. | PD-72 §A.1–A.2; Video `00:22` | `client.merge()` with zero-overhead streaming page assembly. |
| **Legal Authorities** | Unlike paper records, full legal authorities **must be included directly inside the electronic record**. | PD-72 §2; BCCA Rule 27 | Embedded into the single volume stream with exact citation labels. |
| **Top-Center Page Numbering** | Continuous page numbers placed in the **top-center** of each page, formatted in **14–16 pt bold** so they are visibly distinct from native document body text. | Video `01:52`–`02:55`; Court PDF Guide 09 | Top-center text run stamping with Arial/Helvetica Bold 14–16 pt. |
| **Digital Page Labels (`/PageLabels`)** | PDF viewer page counter must align with stamped page numbers: Title Page & Index set to `None`, Tab 1 (Notice of Application) set to start at `1`. | Video `04:17`–`05:44`; Court PDF Guide 10 | `/PageLabels` catalog dictionary with decimal style starting at Tab 1. |
| **Hierarchical Bookmarks** | Every document must be bookmarked. Affidavits must have nested sub-bookmarks for each Exhibit (e.g. *Exhibit A – Contract*). | PD-72 §A.3; Video `01:10`–`01:52`; Court PDF Guide 03 & 04 | `Bookmark` recursive outline tree with `children: Vec<Bookmark>`. |
| **Initial View (`/PageMode`)** | The bookmark navigation panel **must open automatically by default** when opened by the judge. | PD-72 §A.3; Court PDF Guide 12 (`Show_Bookmarks_Automatically_Final.pdf`) | Catalog `/PageMode /UseOutlines` via `InitialView { navigation: Bookmarks }`. |
| **Index Hyperlinks** | The Index (Item 2) must feature invisible rectangle hyperlinks on every entry, jumping directly to target pages/bookmarks. | PD-72 §A.2; Video `05:44`–`07:36`; Court PDF Guide 06 | `LinkAnnotation` with `GoToAction` destination targeting exact page coordinates. |
| **OCR Searchability** | All scanned paper filings, stamped pleadings, and exhibits must be text-searchable. | PD-72 §A.4; Video `03:56`; Court PDF Guide 11 | Integration with `pdfcraft-ocr` pipeline. |
| **CSO File Size Limit** | Strict **50 MB** ceiling per document for electronic submission via CSO portal. | CSO Instructions §3; Video `07:37`–`08:33` | Stream optimization, Flate compression, and `reduce_size(Some(50.0))`. |

---

## ⚡ 2. Manual Paralegal Workflow vs. `pdfcraft-sdk` Automated Pipeline

In standard law firm practice, preparing a compliant application record in Adobe Acrobat requires **9 manual steps taking 45–90 minutes of billable time per filing**:

```mermaid
flowchart TD
    subgraph Manual["Traditional Manual Workflow (45–90 mins)"]
        M1["1. Manually rename source files with numbers"] --> M2["2. Merge content files in Acrobat"]
        M2 --> M3["3. Manually edit/nest exhibit bookmarks"]
        M3 --> M4["4. Stamp top-center 14-16pt bold page numbers"]
        M4 --> M5["5. Note page numbers, manually type into Word Index, export to PDF"]
        M5 --> M6["6. Drag-and-drop Title & Index to front in Pages panel"]
        M6 --> M7["7. Right-click thumbnails, configure PageLabels (None, 1..N)"]
        M7 --> M8["8. Draw link rectangles on Index line by line, link to bookmarks"]
        M8 --> M9["9. Check file size in File Explorer, run Acrobat Compress if > 50MB"]
    end

    subgraph Auto["pdfcraft-sdk Automated Engine (< 200 milliseconds)"]
        A1["Input: Raw Document Files & Exhibit Metadata"] --> A2["Pass 1: Stream Page Counts & Auto-calculate Index Folios"]
        A2 --> A3["Pass 2: Generate Cover, Formatted Index, and Merge Streams"]
        A3 --> A4["Pass 3: Generate Multi-Level Bookmarks Tree & /PageLabels"]
        A4 --> A5["Pass 4: Inject InitialView /UseOutlines & Index Hyperlink Rectangles"]
        A5 --> A6["Pass 5: Top-Center Stamping & Size Pre-Flight (< 50 MB)"]
        A6 --> A7["Output: 100% Court-Compliant CSO Ready PDF Binder"]
    end
```

---

## 🛠️ 3. Automated Two-Pass Generation Algorithm

The primary obstacle in manual assembly is the circular dependency between **pagination** and the **Table of Contents**:
* The Index cannot be finalized until the starting page of every document is known.
* Stamping page numbers before inserting the Index shifts all subsequent page numbers forward by the size of the Index.

### The SDK Algorithm:
1. **Source Introspection:**
   Each document source is probed to determine its page count:
   $$\text{PageCount}(D_i) = \text{pages in } D_i$$
2. **Deterministic Offset Computation:**
   Given a 1-page Cover and a $K$-page Index:
   $$\text{StartPage}(\text{Cover}) = 1$$
   $$\text{StartPage}(\text{Index}) = 2$$
   $$\text{StartPage}(D_1) = 2 + K$$
   $$\text{StartPage}(D_i) = \text{StartPage}(D_{i-1}) + \text{PageCount}(D_{i-1})$$
3. **Automated Index Synthesizer:**
   The Index is rendered dynamically with exact page offsets pre-computed.
4. **Assembly & Atomic Linking:**
   The entire volume is merged, stamped with top-center headers, tagged with `/PageLabels` and `/PageMode /UseOutlines`, and hyperlinked in memory in a single pass.
