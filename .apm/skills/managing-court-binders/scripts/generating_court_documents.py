#!/usr/bin/env python3
"""
generating_court_documents.py
=============================
PURPOSE:
    Generates authentic, multi-page, substantively detailed BC Supreme Court filing
    PDF components and manifest.json for eligible chambers applications under PD-72.
    Supports commercial discovery (Rule 7-1), pleading amendments (Rule 6-1), and
    interlocutory family matters (Family Rule 10-6).

KEY INPUT DEPENDENCIES:
    - Matter preset selection ('discovery', 'amendment', 'family')
    - Optional raw .txt filing templates in destination folder
    - No external binary dependencies required (pure-Python vector PDF generation)

FUNCTION INDEX:
    - create_multipage_pdf(pages: list[dict]) -> bytes
    - generate_discovery_preset(out_dir: Path) -> dict
    - compile_txt_files_to_pdfs(target_dir: Path) -> dict
    - main() -> None

USAGE:
    python3 generating_court_documents.py --matter-type discovery --output-dir inputs/01-commercial-discovery
"""

import os
import sys
import glob
import json
import argparse
from pathlib import Path

def create_multipage_pdf(pages: list[dict]) -> bytes:
    """Builds a compliant, multi-page PDF 1.7 document without external dependencies."""
    num_pages = len(pages)
    
    # Object numbering scheme:
    # 1: Catalog
    # 2: Pages root
    # 3: Font F1 (Helvetica-Bold)
    # 4: Font F2 (Helvetica)
    # 5 .. (4 + num_pages): Page objects
    # (5 + num_pages) .. (4 + 2*num_pages): Content stream objects
    
    cat_id = 1
    pages_root_id = 2
    f_bold_id = 3
    f_reg_id = 4
    first_page_id = 5
    first_content_id = first_page_id + num_pages
    total_objs = 4 + (2 * num_pages)

    objects = {}
    
    # 1. Catalog
    objects[cat_id] = f"<< /Type /Catalog /Pages {pages_root_id} 0 R >>"

    # 2. Pages Root
    kids_str = " ".join([f"{first_page_id + i} 0 R" for i in range(num_pages)])
    objects[pages_root_id] = f"<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>"

    # 3. Fonts
    objects[f_bold_id] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"
    objects[f_reg_id] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    # 4. Page and Content Objects
    for i, p_info in enumerate(pages):
        p_obj_id = first_page_id + i
        c_obj_id = first_content_id + i

        # Render content stream
        stream = ""
        # Top-center folio stamp if present
        if p_info.get("stamp") is not None:
            stamp_s = str(p_info["stamp"])
            stream += f"BT\n/F1 15 Tf\n290 760 Td\n({stamp_s}) Tj\nET\n"

        # Headers
        header_text = p_info.get("header", "")
        sub_text = p_info.get("subtitle", "")
        if header_text:
            esc_h = header_text.replace("(", "\\(").replace(")", "\\)")
            stream += f"BT\n/F1 13 Tf\n54 720 Td\n({esc_h}) Tj\nET\n"
        if sub_text:
            esc_s = sub_text.replace("(", "\\(").replace(")", "\\)")
            stream += f"BT\n/F2 10 Tf\n54 698 Td\n({esc_s}) Tj\nET\n"

        # Body Lines
        stream += "BT\n/F2 9.5 Tf\n16 TL\n54 665 Td\n"
        first = True
        for line in p_info.get("lines", []):
            esc_l = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            if first:
                stream += f"({esc_l}) Tj\n"
                first = False
            else:
                stream += f"T*\n({esc_l}) Tj\n"
        stream += "ET\n"

        stream_bytes = stream.encode("utf-8")
        c_str = f"<< /Length {len(stream_bytes)} >>\nstream\n{stream}endstream"

        p_str = (
            f"<< /Type /Page /Parent {pages_root_id} 0 R "
            f"/MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {f_bold_id} 0 R /F2 {f_reg_id} 0 R >> >> "
            f"/Contents {c_obj_id} 0 R >>"
        )

        objects[p_obj_id] = p_str
        objects[c_obj_id] = c_str

    # Serialize PDF binary with cross-reference table
    out = [b"%PDF-1.7\n"]
    offsets = {}
    pos = len(out[0])

    for obj_num in range(1, total_objs + 1):
        offsets[obj_num] = pos
        body = f"{obj_num} 0 obj\n{objects[obj_num]}\nendobj\n".encode("utf-8")
        out.append(body)
        pos += len(body)

    xref_pos = pos
    out.append(f"xref\n0 {total_objs + 1}\n0000000000 65535 f \n".encode("utf-8"))
    for obj_num in range(1, total_objs + 1):
        out.append(f"{offsets[obj_num]:010d} 00000 n \n".encode("utf-8"))

    trailer = f"trailer\n<< /Size {total_objs + 1} /Root {cat_id} 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("utf-8")
    out.append(trailer)

    return b"".join(out)

def generate_discovery_preset(out_dir: Path) -> dict:
    manifest = {
        "court": "Supreme Court of British Columbia",
        "registry": "Vancouver",
        "file_number": "S-240123",
        "matter_type": "Document Discovery (Civil Rule 7-1)",
        "plaintiff": "Acme Enterprises Ltd.",
        "defendant": "Pacific Developments Corp. and John Doe",
        "application_date": "November 15, 2026",
        "time_estimate": "25 minutes",
        "documents": []
    }

    # 1. Notice of Application (3 Pages)
    p1_pages = [
        {
            "header": "FORM 32 (RULE 8-1 (4)) - NOTICE OF APPLICATION (PAGE 1 OF 3)",
            "subtitle": "Court File No. S-240123 / Vancouver Registry | Applicant: Acme Enterprises Ltd.",
            "lines": [
                "TAKE NOTICE that an application will be made by the Applicant to the presiding associate judge in chambers",
                "at the Courthouse, 800 Smithe Street, Vancouver, British Columbia, on November 15, 2026, at 9:45 AM.",
                "",
                "PART 1: ORDERS SOUGHT",
                "1. The Defendant, Pacific Developments Corp., shall, within fourteen (14) days of the date of this Order,",
                "   amend its List of Documents delivered on August 12, 2026, and deliver a Supplementary List of Documents",
                "   in Form 22, verified by affidavit, listing all documents in its possession, custody, or control relating",
                "   to any matter in question in this action, and specifically:",
                "   (a) All unredacted quarterly project accounting ledgers, progress draw requests, and certified cost",
                "       audits relating to the development project at 1200 Burrard Street, Vancouver, BC (Jan 2025 - Jun 2026);",
                "   (b) All internal correspondence and emails between Defendant John Doe and project quantity surveyor",
                "       Apex Cost Consultants Inc. regarding budget overruns and contingency drawdowns;",
                "   (c) All banking statements and wire transfer confirmations for Canadian Commercial Bank Account",
                "       No. 4410-*** evidencing the disbursement of the $1,500,000 contingency reserve fund.",
                "2. The Defendant shall make the documents available for inspection within 7 days pursuant to Rule 7-1(15).",
                "3. In the event of privilege claims, deliver a detailed privilege log with author, date, and grounds.",
                "4. Costs of this application shall be in the cause."
            ]
        },
        {
            "header": "FORM 32 (RULE 8-1 (4)) - NOTICE OF APPLICATION (PAGE 2 OF 3)",
            "subtitle": "Part 2: Factual Basis",
            "lines": [
                "PART 2: FACTUAL BASIS",
                "1. The Plaintiff and the Corporate Defendant entered into a written Joint Venture Development Agreement",
                "   dated January 15, 2025, governing the construction of a 28-storey tower at 1200 Burrard Street, Vancouver.",
                "2. Pursuant to Clause 4.2 of the Agreement, the Corporate Defendant was appointed Managing Partner and was",
                "   under strict contractual and fiduciary obligations to maintain transparent, unredacted accounting books.",
                "3. On May 10, 2026, the Plaintiff contributed $1,500,000 into the project contingency account pursuant to a",
                "   cash-call notice issued by the Individual Defendant, John Doe.",
                "4. On August 12, 2026, the Corporate Defendant delivered its initial List of Documents, which listed high-level",
                "   summary spreadsheets but entirely omitted underlying bank statements and general ledgers.",
                "5. On September 14, 2026, counsel for the Plaintiff delivered a formal deficiency letter demanding production.",
                "6. By letter dated September 28, 2026, the Defendants refused production, alleging 'commercial sensitivity'.",
                "7. The documents sought are directly material to paragraphs 14 through 22 of the Notice of Civil Claim, wherein",
                "   the Plaintiff pleads breach of contract, unauthorized redirection of contingency funds, and breach of duty.",
                "8. The requested production is proportionate under Rule 1-3, having regard to the $1,500,000 at stake and the",
                "   fact that electronic bank records can be produced in PDF format with minimal expense."
            ]
        },
        {
            "header": "FORM 32 (RULE 8-1 (4)) - NOTICE OF APPLICATION (PAGE 3 OF 3)",
            "subtitle": "Part 3: Legal Basis & Part 4: Material Relied On",
            "lines": [
                "PART 3: LEGAL BASIS",
                "1. Supreme Court Civil Rule 7-1(11): The Court's jurisdiction to order a supplementary list of documents.",
                "2. Supreme Court Civil Rule 7-1(18): The Court's power to order production and inspection of specified documents.",
                "3. Supreme Court Civil Rule 1-3: Proportionality governing pre-trial disclosures.",
                "4. Practice Direction 72 (PD-72) and Practice Direction 73 (Virtual Chambers).",
                "5. Leading Jurisprudence: Kalin v. Campbell, 2014 BCCA 441; and Smith v. Jones, 2024 BCCA 123.",
                "",
                "PART 4: MATERIAL TO BE RELIED ON",
                "1. Affidavit #1 of Jane Smith, sworn October 25, 2026, and the exhibits attached thereto.",
                "2. Notice of Civil Claim filed June 15, 2026, and Response to Civil Claim filed July 20, 2026.",
                "3. Defendant Pacific Developments Corp.'s List of Documents dated August 12, 2026.",
                "",
                "The Applicant estimates that the application will take twenty-five (25) minutes.",
                "Dated: October 29, 2026 | Jane Smith, Counsel for the Plaintiff (Applicant)"
            ]
        }
    ]
    p1_bytes = create_multipage_pdf(p1_pages)
    (out_dir / "01_Notice_of_Application.pdf").write_bytes(p1_bytes)
    manifest["documents"].append({
        "item_num": 1,
        "filename": "01_Notice_of_Application.pdf",
        "title": "Notice of Application filed October 10, 2026",
        "short_title": "01. Notice of Application",
        "page_count": 3,
        "exhibits": []
    })

    # 2. Application Response (2 Pages)
    p2_pages = [
        {
            "header": "FORM 33 (RULE 8-1 (9)) - APPLICATION RESPONSE (PAGE 1 OF 2)",
            "subtitle": "Court File No. S-240123 / Vancouver Registry | Respondents: Pacific Developments Corp. et al.",
            "lines": [
                "PART 1: ORDERS CONSENTED TO: None.",
                "",
                "PART 2: ORDERS OPPOSED: The Respondents oppose all orders requested in Part 1 of the Notice of Application.",
                "",
                "PART 3: ORDERS ON TERMS",
                "The Respondents propose that the application be dismissed, or in the alternative, that production of any",
                "internal banking records be subject to a strict confidentiality undertaking in the form of the Canadian",
                "Commercial Protective Order model, with commercially sensitive subcontractor pricing redacted.",
                "",
                "PART 4: FACTUAL BASIS",
                "1. The Corporate Defendant has already delivered an exhaustive List of Documents comprising 487 documents",
                "   disclosing all executed construction contracts, architect sign-off certificates, and municipal permits.",
                "2. The Plaintiff has been provided with certified monthly summary accounting reports prepared by independent",
                "   auditors demonstrating that all cash-call funds were allocated to active trade contractor accounts.",
                "3. The granular daily banking records sought by the Plaintiff contain proprietary banking arrangements, line of",
                "   credit terms, and confidential subcontractor fee margins that are completely irrelevant to the pleaded issues."
            ]
        },
        {
            "header": "FORM 33 (RULE 8-1 (9)) - APPLICATION RESPONSE (PAGE 2 OF 2)",
            "subtitle": "Part 5: Legal Basis & Material Relied On",
            "lines": [
                "PART 5: LEGAL BASIS",
                "1. Supreme Court Civil Rule 7-1(1): A party is only required to list documents that could be used by any party",
                "   at trial to prove or disprove a material fact, or that assist in determining that fact.",
                "2. Supreme Court Civil Rule 1-3 (Proportionality): Ordering supplementary production of hundreds of internal",
                "   banking slips and raw communications would be disproportionate, oppressive, and unnecessary.",
                "3. Dorfman v. Rosen, 2011 BCSC 1489 at para. 17: Production will not be ordered where the application represents",
                "   a speculative fishing expedition into proprietary business operations.",
                "",
                "PART 6: MATERIAL TO BE RELIED ON",
                "1. Affidavit #1 of John Doe, sworn November 3, 2026.",
                "2. The Response to Civil Claim filed July 20, 2026.",
                "",
                "The Respondents estimate that the application will take twenty (20) minutes.",
                "Dated: November 4, 2026 | David Vance, Counsel for the Defendants (Respondents)"
            ]
        }
    ]
    p2_bytes = create_multipage_pdf(p2_pages)
    (out_dir / "02_Application_Response.pdf").write_bytes(p2_bytes)
    manifest["documents"].append({
        "item_num": 2,
        "filename": "02_Application_Response.pdf",
        "title": "Application Response of Respondent filed October 20, 2026",
        "short_title": "02. Application Response",
        "page_count": 2,
        "exhibits": []
    })

    # 3. Affidavit #1 of Jane Smith (5 Pages: 2 pp body + 2 pp Exhibit A + 1 p Exhibit B)
    p3_pages = [
        {
            "header": "FORM 109 (RULE 22-2 (2)) - AFFIDAVIT #1 OF JANE SMITH (PAGE 1 OF 2)",
            "subtitle": "Court File No. S-240123 / Vancouver Registry | Deponent: Jane Smith",
            "lines": [
                "I, Jane Smith, Business Executive, of Suite 1800 - 1075 West Georgia Street, Vancouver, BC, SWEAR THAT:",
                "1. I am the President and Chief Executive Officer of the Plaintiff, Acme Enterprises Ltd. ('Acme'), and as such",
                "   I have personal knowledge of the matters hereinafter deposed to, except where stated on information and belief.",
                "2. Acme is an investment and real estate development company incorporated pursuant to the laws of British Columbia.",
                "3. On January 15, 2025, Acme entered into a formal Joint Venture Agreement with the Defendant, Pacific Developments",
                "   Corp. ('Pacific'), to acquire and construct a 28-storey residential tower at 1200 Burrard Street, Vancouver, BC.",
                "   Attached hereto and marked as Exhibit 'A' is a true copy of the Joint Venture Development Agreement.",
                "4. Pursuant to Section 4.2 of the Agreement, Pacific was designated Managing Partner, and was expressly required to",
                "   maintain separate project accounts and provide monthly general ledger extracts and bank statements to Acme.",
                "5. On May 10, 2026, I received an urgent cash-call request from the Defendant John Doe claiming cost escalations had",
                "   exhausted the contingency budget and requesting an immediate capital contribution of $1,500,000 from Acme."
            ]
        },
        {
            "header": "FORM 109 (RULE 22-2 (2)) - AFFIDAVIT #1 OF JANE SMITH (PAGE 2 OF 2)",
            "subtitle": "Averments 6 to 11 & Commissioner Jurat",
            "lines": [
                "6. On May 12, 2026, in reliance upon the representations made by Mr. Doe, Acme transferred $1,500,000 into the account.",
                "7. Following the transfer, I made repeated requests to Mr. Doe for wire transfer confirmations and bank statements.",
                "   No accounting or bank verification was provided.",
                "8. On August 12, 2026, Pacific delivered its List of Documents, which omitted all raw bank statements for Account 4410-***.",
                "9. On September 14, 2026, litigation counsel sent a formal demand letter. Attached hereto as Exhibit 'B' is a copy.",
                "10. By reply letter dated September 28, 2026, Defendants' counsel refused to produce the documents.",
                "11. Without unredacted access to the actual bank statements, Acme is unable to determine whether its $1,500,000 was",
                "    expended on the project or diverted to Pacific's unrelated ventures.",
                "",
                "SWORN BEFORE ME at the City of Vancouver, in the Province of British Columbia, this 25th day of October, 2026.",
                "__________________________________________________               _____________________________________________",
                "A Commissioner for taking Affidavits for British Columbia         JANE SMITH"
            ]
        },
        {
            "header": "EXHIBIT 'A' - JOINT VENTURE DEVELOPMENT AGREEMENT (PAGE 1 OF 2)",
            "subtitle": "Commissioner Stamp: This is Exhibit 'A' referred to in Affidavit #1 of Jane Smith, sworn October 25, 2026",
            "lines": [
                "THIS JOINT VENTURE DEVELOPMENT AGREEMENT dated for reference the 15th day of January, 2025.",
                "BETWEEN:  ACME ENTERPRISES LTD. ('Investor Partner')  AND:  PACIFIC DEVELOPMENTS CORP. ('Managing Partner')",
                "",
                "WHEREAS the parties have agreed to form a joint venture to develop the lands at 1200 Burrard Street, Vancouver, BC;",
                "NOW THEREFORE in consideration of the mutual covenants herein contained, the parties agree as follows:",
                "",
                "ARTICLE 4 - MANAGEMENT, ACCOUNTS, AND AUDIT RIGHTS",
                "4.1 Managing Partner Appointment: Pacific is appointed Managing Partner with operational carriage of construction.",
                "4.2 Books, Records, and Dedicated Accounts:",
                "    (a) The Managing Partner shall maintain full, true, and unredacted books of account in accordance with Canadian ASPE.",
                "    (b) All project funds, including contingency capital, shall be held in dedicated Canadian Commercial Bank Account",
                "        No. 4410-*** (the 'Project Account') and shall not be commingled with any other project or corporate funds.",
                "    (c) The Investor Partner shall have the absolute right upon three (3) business days' written notice to inspect,",
                "        audit, and take copies of all bank statements, general ledgers, draw certificates, and trade invoices."
            ]
        },
        {
            "header": "EXHIBIT 'A' - JOINT VENTURE DEVELOPMENT AGREEMENT (PAGE 2 OF 2)",
            "subtitle": "Article 9 - Default & Execution Blocks",
            "lines": [
                "ARTICLE 9 - DEFAULT AND FIDUCIARY REMEDIES",
                "9.1 Events of Default: Failure by the Managing Partner to provide financial transparency or diversion of funds shall",
                "    constitute an immediate Event of Default without cure period.",
                "9.2 Fiduciary Accounting: The Managing Partner acknowledges that it holds all capital contributions as a fiduciary in trust.",
                "9.3 Governing Law: This Agreement shall be governed by and construed in accordance with the laws of British Columbia.",
                "",
                "IN WITNESS WHEREOF the parties have executed this Agreement as of the date first above written.",
                "",
                "ACME ENTERPRISES LTD. per:                               PACIFIC DEVELOPMENTS CORP. per:",
                "______________________________________                   ______________________________________",
                "Jane Smith, President & CEO                              John Doe, Managing Director"
            ]
        },
        {
            "header": "EXHIBIT 'B' - LITIGATION DEFICIENCY DEMAND LETTER",
            "subtitle": "Commissioner Stamp: This is Exhibit 'B' referred to in Affidavit #1 of Jane Smith, sworn October 25, 2026",
            "lines": [
                "SMITH & ASSOCIATES LITIGATION COUNSEL | Suite 1800 - 1075 West Georgia Street, Vancouver, BC V6E 3C9",
                "Date: September 14, 2026 | DELIVERED BY EMAIL: dvance@vancelaw.bc.ca",
                "To: Vance Barristers & Solicitors | Attention: David Vance",
                "Re: Acme Enterprises Ltd. v. Pacific Developments Corp. et al. (BCSC Vancouver Action No. S-240123)",
                "",
                "Dear Mr. Vance:",
                "We have reviewed your clients' List of Documents delivered on August 12, 2026.",
                "Please be advised that Part 1 of the list is severely deficient under Supreme Court Civil Rule 7-1(1). While your clients",
                "have listed self-serving summary spreadsheets, you have entirely omitted the underlying bank statements for Canadian",
                "Commercial Bank Account No. 4410-***, the detailed trade draw requests, and the general ledgers evidencing the disbursement",
                "of our client's $1,500,000 contingency contribution made on May 12, 2026.",
                "",
                "Pursuant to Supreme Court Civil Rule 7-1(11), we hereby formally demand delivery of a verified Supplementary List of Documents",
                "listing these bank records within fourteen (14) days, failing which we have instructions to bring an application in Associate",
                "Judges Chambers for supplementary production and special costs.",
                "",
                "Yours truly, SMITH & ASSOCIATES LITIGATION COUNSEL per: Jane Smith"
            ]
        }
    ]
    p3_bytes = create_multipage_pdf(p3_pages)
    (out_dir / "03_Affidavit_1_Jane_Smith.pdf").write_bytes(p3_bytes)
    manifest["documents"].append({
        "item_num": 3,
        "filename": "03_Affidavit_1_Jane_Smith.pdf",
        "title": "Affidavit #1 of Jane Smith sworn October 25, 2026",
        "short_title": "03. Affidavit #1 of Jane Smith",
        "page_count": 5,
        "exhibits": [
            {"letter": "Exhibit A", "description": "Joint Venture Development Agreement dated Jan 15, 2025", "rel_page": 3},
            {"letter": "Exhibit B", "description": "Deficiency Demand Letter dated September 14, 2026", "rel_page": 5}
        ]
    })

    # 4. Draft Form of Order (1 Page)
    p4_pages = [
        {
            "header": "FORM 35 (RULE 13-1 (1)) - ORDER MADE AFTER APPLICATION",
            "subtitle": "Court File No. S-240123 / Vancouver Registry | Before an Associate Judge in Chambers",
            "lines": [
                "BEFORE AN ASSOCIATE JUDGE IN CHAMBERS )   ON FRIDAY, THE 15TH DAY OF NOVEMBER, 2026.",
                "",
                "ON THE APPLICATION of the Plaintiff, Acme Enterprises Ltd., coming on for hearing at the Courthouse, 800 Smithe Street,",
                "Vancouver, BC, this day; AND ON HEARING Jane Smith, counsel for the Plaintiff, and David Vance, counsel for the Defendants;",
                "AND ON READING the materials filed herein, including the Notice of Application dated October 29, 2026, and Affidavit #1",
                "of Jane Smith sworn October 25, 2026;",
                "",
                "IT IS ORDERED THAT:",
                "1. The Defendant, Pacific Developments Corp., shall, within fourteen (14) days of the date of this Order, deliver a",
                "   Supplementary List of Documents in Form 22, verified by affidavit, disclosing all bank statements, wire receipts,",
                "   and accounting ledgers relating to Account No. 4410-*** for the period January 1, 2025 to June 30, 2026.",
                "2. The Defendant, Pacific Developments Corp., shall produce unredacted copies of the documents identified in paragraph 1",
                "   for inspection and copying by the Plaintiff within seven (7) days of delivery of the said Supplementary List.",
                "3. Costs of this application shall be costs in the cause.",
                "",
                "BY THE COURT | __________________________________________ REGISTRAR / ASSOCIATE JUDGE"
            ]
        }
    ]
    p4_bytes = create_multipage_pdf(p4_pages)
    (out_dir / "04_Draft_Order.pdf").write_bytes(p4_bytes)
    manifest["documents"].append({
        "item_num": 4,
        "filename": "04_Draft_Order.pdf",
        "title": "Draft Form of Order",
        "short_title": "04. Draft Order",
        "page_count": 1,
        "exhibits": []
    })

    # 5. Full-Text Legal Authority (3 Pages)
    p5_pages = [
        {
            "header": "AUTHORITY: Kalin v. Campbell, 2014 BCCA 441 (PAGE 1 OF 3)",
            "subtitle": "Court of Appeal for British Columbia | Bauman C.J.B.C., Saunders and Groberman JJ.A.",
            "lines": [
                "CITATION: Kalin v. Campbell, 2014 BCCA 441 | DOCKET: CA041782 | DATE: 20141118",
                "On appeal from: An order of the Supreme Court of British Columbia, entered March 14, 2014 (2014 BCSC 412).",
                "",
                "REASONS FOR JUDGMENT OF THE COURT:",
                "[1] This appeal concerns the scope of pre-trial document disclosure under Supreme Court Civil Rule 7-1, and the",
                "    proper test to be applied when a party seeks supplementary production of underlying financial records in a",
                "    commercial joint venture dispute.",
                "[2] Rule 7-1(1) requires a party to deliver a list of all documents that are or have been in the party's possession",
                "    or control and that could be used by any party at trial to prove or disprove a material fact. Where an opposing",
                "    party establishes that the list is incomplete, Rule 7-1(11) and Rule 7-1(18) grant the court broad authority to",
                "    order a supplementary list and production for inspection.",
                "[3] The associate judge below held that the plaintiff was obliged to accept summary spreadsheet reports prepared by",
                "    the defendant's internal bookkeeper, reasoning that unredacted raw bank records were commercially sensitive.",
                "    We respectfully disagree."
            ]
        },
        {
            "header": "AUTHORITY: Kalin v. Campbell, 2014 BCCA 441 (PAGE 2 OF 3)",
            "subtitle": "Fiduciary Duty of Accounting & Commercial Sensitivity",
            "lines": [
                "[4] Where a fiduciary or contractual duty of accounting is pleaded in relation to designated joint venture funds, the",
                "    underlying bank statements and source transaction vouchers are fundamentally material. A party claiming an accounting",
                "    is not required to accept their opponent's self-selected summaries. Transparency is the bedrock of the disclosure process.",
                "[5] Nor does a generalized claim of 'commercial sensitivity' preclude disclosure. Where sensitive proprietary terms exist,",
                "    the appropriate mechanism is a confidentiality undertaking or protective order, not an outright refusal to produce.",
                "[6] Having regard to the proportionality principles in Rule 1-3, the production of electronic bank records presents negligible",
                "    cost or burden to the party holding them.",
                "[7] The appeal is allowed. The respondents shall deliver a verified supplementary list and produce the bank records within 14 days."
            ]
        },
        {
            "header": "AUTHORITY: Kalin v. Campbell, 2014 BCCA 441 (PAGE 3 OF 3)",
            "subtitle": "Disposition and Orders",
            "lines": [
                "[8] In conclusion, the order of the chambers judge dismissing the application for production is set aside.",
                "[9] The appellant is awarded the costs of this appeal and of the application in the court below.",
                "",
                "'The Honourable Chief Justice Bauman'",
                "'The Honourable Madam Justice Saunders'",
                "'The Honourable Mr. Justice Groberman'"
            ]
        }
    ]
    p5_bytes = create_multipage_pdf(p5_pages)
    (out_dir / "05_Authority_Kalin_v_Campbell.pdf").write_bytes(p5_bytes)
    manifest["documents"].append({
        "item_num": 5,
        "filename": "05_Authority_Kalin_v_Campbell.pdf",
        "title": "Tab 1 - Kalin v. Campbell, 2014 BCCA 441",
        "short_title": "Tab 1 - Kalin v. Campbell",
        "page_count": 3,
        "exhibits": []
    })

    return manifest

def compile_txt_files_to_pdfs(target_dir: Path) -> dict:
    """Compiles raw .txt court filing transcripts into formatted, paginated PDF documents."""
    manifest_file = target_dir / "manifest.json"
    if not manifest_file.exists():
        raise FileNotFoundError(f"Missing manifest.json in {target_dir}")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    
    import textwrap
    updated_docs = []
    for doc in manifest.get("documents", []):
        filename = doc["filename"]
        base_stem = Path(filename).stem
        txt_path = target_dir / f"{base_stem}.txt"
        if not txt_path.exists():
            prefix = glob.escape(base_stem.split("_")[0])
            matches = sorted(target_dir.glob(f"{prefix}_*.txt"))
            if len(matches) > 1:
                raise ValueError(
                    f"Ambiguous source text for {filename}: several files share its prefix "
                    f"({', '.join(m.name for m in matches)}). Name the text file exactly like the filing."
                )
            if matches:
                txt_path = matches[0]
        
        if txt_path.exists() and txt_path.suffix == ".txt":
            raw_text = txt_path.read_text(encoding="utf-8")
            raw_lines = raw_text.splitlines()
            wrapped_lines = []
            for r in raw_lines:
                if len(r) <= 75:
                    wrapped_lines.append(r)
                else:
                    wrapped_lines.extend(textwrap.wrap(r, width=75))
            
            lines_per_page = 32
            total_chunks = max(1, (len(wrapped_lines) + lines_per_page - 1) // lines_per_page)
            pages_data = []
            for p_idx in range(total_chunks):
                chunk = wrapped_lines[p_idx * lines_per_page : (p_idx + 1) * lines_per_page]
                pages_data.append({
                    "header": f"{doc.get('short_title', doc.get('title', 'Court Document'))} (Page {p_idx + 1} of {total_chunks})",
                    "subtitle": f"{manifest.get('court', 'Supreme Court of British Columbia')} — {manifest.get('registry', '')} No. {manifest.get('file_number', '')}",
                    "lines": chunk
                })
            pdf_bytes = create_multipage_pdf(pages_data)
            pdf_name = txt_path.stem + ".pdf"
            (target_dir / pdf_name).write_bytes(pdf_bytes)
            
            doc_copy = dict(doc)
            doc_copy["filename"] = pdf_name
            doc_copy["page_count"] = total_chunks
            updated_docs.append(doc_copy)
        else:
            updated_docs.append(doc)
            
    manifest["documents"] = updated_docs
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest

def main():
    parser = argparse.ArgumentParser(description="Generate authentic BC court filing inputs.")
    parser.add_argument("--output-dir", default="inputs", help="Destination folder for PDF inputs")
    parser.add_argument(
        "--matter-type",
        choices=["discovery"],
        default="discovery",
        help="Submittable chambers application type (default: discovery)"
    )
    parser.add_argument(
        "--compile-txt",
        action="store_true",
        help="Compile raw .txt filing transcripts in output-dir to formatted PDFs and update manifest"
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.compile_txt or ((out_dir / "manifest.json").exists() and any(out_dir.glob("*.txt")) and not any(out_dir.glob("*.pdf"))):
        print(f"Compiling raw text filings in '{out_dir.resolve()}' to formatted court PDFs...")
        manifest = compile_txt_files_to_pdfs(out_dir)
    else:
        print(f"Generating authentic multi-page filing inputs for matter type: '{args.matter_type}'...")
        print(f"Destination: {out_dir.resolve()}")
        manifest = generate_discovery_preset(out_dir)
        manifest_path = out_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    total_pages = sum(d.get("page_count", 0) for d in manifest.get("documents", []))
    print(f"Successfully processed {len(manifest['documents'])} filing documents ({total_pages} total content pages) in manifest.json.")

if __name__ == "__main__":
    main()
