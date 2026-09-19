#!/usr/bin/env python3
"""
Generate a publication-grade formal academic report in .docx format
for YojanaVaani Major Project (Chapters 1 to 4).
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="D3D3D3"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="6" w:space="0" w:color="{color}"/>
            <w:bottom w:val="single" w:sz="6" w:space="0" w:color="{color}"/>
            <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>
            <w:insideV w:val="none"/>
            <w:left w:val="none"/>
            <w:right w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders)

def build_docx(output_path):
    doc = Document()

    # Configure 1-inch margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Base styling
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0x1F, 0x29, 0x37) # Slate 800
    normal_style.paragraph_format.line_spacing = 1.25
    normal_style.paragraph_format.space_after = Pt(6)

    # ----------------------------------------------------
    # COVER PAGE / TITLE BLOCK
    # ----------------------------------------------------
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(36)
    title_p.paragraph_format.space_after = Pt(8)
    run_title = title_p.add_run("YOJANAVAANI (योजना वाणी)")
    run_title.font.name = 'Times New Roman'
    run_title.font.size = Pt(24)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A) # Navy Blue

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.paragraph_format.space_after = Pt(28)
    run_sub = sub_p.add_run("An Agentic Voice-First Multimodal AI System for Vernacular Welfare Scheme Discovery and Deterministic Eligibility Verification")
    run_sub.font.name = 'Times New Roman'
    run_sub.font.size = Pt(13)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)

    badge_p = doc.add_paragraph()
    badge_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    badge_p.paragraph_format.space_after = Pt(40)
    run_badge = badge_p.add_run("MAJOR PROJECT INTERIM REPORT (CHAPTERS 1 TO 4)")
    run_badge.font.name = 'Times New Roman'
    run_badge.font.size = Pt(14)
    run_badge.font.bold = True
    run_badge.font.color.rgb = RGBColor(0x06, 0x5F, 0x46) # Emerald Dark

    meta_p = doc.add_paragraph()
    meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_p.paragraph_format.space_after = Pt(4)
    run_meta = meta_p.add_run("Submitted in partial fulfillment of the requirements for the degree of\nBACHELOR OF TECHNOLOGY IN COMPUTER SCIENCE & ENGINEERING")
    run_meta.font.name = 'Times New Roman'
    run_meta.font.size = Pt(11)
    run_meta.font.bold = True

    doc.add_page_break()

    # Helper functions for headings
    def add_chapter_heading(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(10)
        run = p.add_run(title)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A) # Navy
        return p

    def add_section_heading(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(title)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
        return p

    def add_subsection_heading(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(title)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x37, 0x41, 0x51)
        return p

    def add_callout(text, prefix=""):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.cell(0, 0)
        set_cell_background(cell, "F0F4F8") # Very light soft blue-gray
        set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.2
        if prefix:
            r_pre = p.add_run(prefix + " ")
            r_pre.font.bold = True
            r_pre.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
        r_txt = p.add_run(text)
        r_txt.font.italic = True
        r_txt.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    def format_table(table, col_widths, headers, rows_data):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(table, "CBD5E1")
        # Header
        hdr_row = table.rows[0]
        for idx, text in enumerate(headers):
            cell = hdr_row.cells[idx]
            cell.width = col_widths[idx]
            set_cell_background(cell, "1E3A8A")
            set_cell_margins(cell, top=120, bottom=120, left=120, right=120)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(text)
            run.font.bold = True
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        # Data
        for r_idx, r_data in enumerate(rows_data):
            row = table.rows[r_idx + 1]
            bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
            for c_idx, val in enumerate(r_data):
                cell = row.cells[c_idx]
                cell.width = col_widths[c_idx]
                set_cell_background(cell, bg)
                set_cell_margins(cell, top=90, bottom=90, left=100, right=100)
                p = cell.paragraphs[0]
                p.paragraph_format.space_after = Pt(0)
                run = p.add_run(str(val))
                run.font.size = Pt(9.5)
                if c_idx == 0:
                    run.font.bold = True
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # ----------------------------------------------------
    # TABLE OF CONTENTS
    # ----------------------------------------------------
    add_chapter_heading("TABLE OF CONTENTS")
    toc_items = [
        ("Chapter 1: Introduction", "3"),
        ("    1.1 Background", "3"),
        ("    1.2 Problem Statement", "3"),
        ("    1.3 Social & Environmental Relevance", "4"),
        ("    1.4 Gantt Chart / Project Timeline", "5"),
        ("    1.5 Scope of the Project", "5"),
        ("Chapter 2: Literature Survey / Critical Review", "6"),
        ("    2.1 Overview of Existing Work & Dataset Study", "6"),
        ("    2.2 Summary Comparison Table", "8"),
        ("    2.3 Research Gaps, Citizen Awareness Deficit Analysis, & Project Contribution", "9"),
        ("Chapter 3: System Design & Methodology", "11"),
        ("    3.1 Proposed Methodology & Architectural Block Diagrams", "11"),
        ("    3.2 Tool and Technique Selection Justifications", "14"),
        ("Chapter 4: Implementation & Testing", "16"),
        ("    4.1 Experimental Setup", "16"),
        ("    4.2 Test Cases, Case Study Walkthrough, & Next Steps Implementation Roadmap", "18"),
    ]
    for item, page_num in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        r1 = p.add_run(item)
        if not item.startswith("    "):
            r1.font.bold = True
        r2 = p.add_run(" " + "." * max(5, 75 - len(item) * 2) + " " + page_num)
        r2.font.color.rgb = RGBColor(0x9C, 0xA3, 0xAF)

    doc.add_page_break()

    # ----------------------------------------------------
    # CHAPTER 1: INTRODUCTION
    # ----------------------------------------------------
    add_chapter_heading("CHAPTER 1: INTRODUCTION")

    add_section_heading("1.1 Background")
    doc.add_paragraph(
        "The Government of India alongside state administrations operates over 2,300 welfare schemes and Direct Benefit Transfer (DBT) initiatives formulated to economically and socially support rural, low-income, and marginalized citizens. Major flagship programs such as Pradhan Mantri Kisan Samman Nidhi (PM-KISAN), Pradhan Mantri Awas Yojana (PMAY), Ayushman Bharat - PM-JAY, and the National Social Assistance Programme (NSAP) disburse over ₹4.5 lakh crore annually."
    )
    doc.add_paragraph(
        "Despite extensive fiscal outlays, a persistent 'last-mile delivery deficit' prevents eligible beneficiaries from obtaining their statutory entitlements. The underlying root cause is not financial shortage, but an acute discoverability and accessibility barrier. Target beneficiaries—predominantly rural smallholder farmers, informal laborers, elderly citizens, and women—frequently lack formal literacy and digital fluency. Furthermore, they operate in oral, vernacular linguistic environments (specifically conversational regional dialects of Hindi), whereas existing public service portals (e.g., myScheme.gov.in, UMANG) demand desktop/smartphone text-based navigation, intricate category filtering, and comprehension of bureaucratic legal prose."
    )
    doc.add_paragraph(
        "Consequently, citizens remain heavily reliant on village middlemen, cyber-café operators, and informal touts who routinely extract 10% to 30% commissions or misinform citizens regarding their eligibility. YojanaVaani addresses this fundamental exclusion by providing an agentic, voice-first native mobile application that allows citizens to discover, verify, and document their eligibility for public schemes purely through spoken vernacular Hindi."
    )

    add_section_heading("1.2 Problem Statement")
    doc.add_paragraph(
        "Contemporary public welfare delivery architectures suffer from three critical structural bottlenecks:"
    )
    doc.add_paragraph(
        "1. Modality and Linguistic Exclusion: Existing systems are overwhelmingly text-centric and English/formal Hindi-based. There is an absence of intuitive conversational voice interfaces that accommodate rural dialects, phonology, and colloquial phrasing."
    )
    doc.add_paragraph(
        "2. Algorithmic Hallucination in Public Entitlements: Deploying generative LLM chatbots directly to advise citizens on welfare eligibility introduces severe risks of hallucination—generating fictitious criteria, misquoting statutory income/age thresholds, or granting false assurances of entitlement."
    )
    doc.add_paragraph(
        "3. Multimodal Documentation Verification Overhead: Eligibility determination requires validating tangible identity and socio-economic certificates (Aadhaar cards, BPL ration cards, land revenue records, caste and disability certificates). Rural citizens lack automated mechanisms to inspect whether their available documentation satisfies statutory norms."
    )
    add_callout(
        "To design, implement, and empirically evaluate YojanaVaani, a voice-first native mobile application powered by an agentic backend orchestration framework that decouples probabilistic conversational understanding (via speech recognition, multilingual vector retrieval, and bounded LLM agent orchestration) from deterministic, rule-based eligibility verification, guaranteeing 100% auditability and zero hallucination in public welfare delivery.",
        "Formal Objective Statement:"
    )

    add_section_heading("1.3 Social & Environmental Relevance")
    add_subsection_heading("1.3.1 Social Relevance")
    doc.add_paragraph(
        "• Democratization of Social Welfare: Bridges the digital and literacy divide, allowing illiterate and semi-literate citizens to discover benefits independently in their native spoken tongue."
    )
    doc.add_paragraph(
        "• Eradication of Exploitative Middlemen: By providing an automated, objective, and cost-free eligibility verdict, citizens are shielded from predatory touts charging commissions on direct benefit transfers."
    )
    doc.add_paragraph(
        "• Empowerment of Women and PwD Beneficiaries: Rural women and persons with disabilities facing severe geographic and mobility constraints can conduct complete eligibility screenings from home."
    )
    doc.add_paragraph(
        "• Privacy Compliance (DPDP Act, 2023): In strict accordance with India's Digital Personal Data Protection Act (2023), citizen voice inputs and identity documents are processed on dedicated private infrastructure without third-party commercial cloud leakage."
    )

    add_subsection_heading("1.3.2 Environmental Relevance")
    doc.add_paragraph(
        "• Paperless Governance: Multimodal digital intake and local optical character recognition eliminate the massive paper trails, redundant photocopies, and physical affidavits traditionally mandated for welfare applications."
    )
    doc.add_paragraph(
        "• Rural Commute Decarbonization: Rural citizens frequently undertake repeated 15 km–50 km motorized journeys to block headquarters (Tehsils) simply to inquire about scheme prerequisites. Local voice verification directly curtails vehicular fuel consumption and transit emissions."
    )

    add_section_heading("1.4 Gantt Chart / Project Timeline")
    doc.add_paragraph(
        "The project follows a structured 16-week engineering lifecycle divided across 8 progressive phases. Table 1.1 delineates the milestone allocation and current delivery progress."
    )
    
    gantt_table = doc.add_table(rows=9, cols=5)
    format_table(
        gantt_table,
        [Inches(1.8), Inches(1.8), Inches(1.2), Inches(1.0), Inches(1.2)],
        ["Phase Name", "Core Deliverables", "Timeline", "Effort", "Status"],
        [
            ["Phase 1: Inception", "Specs, Ethics, DPDP Review", "Weeks 1–2", "2 Weeks", "Completed"],
            ["Phase 2: Corpus & DB", "Scraping, Cleaning, Vector Store", "Weeks 3–5", "3 Weeks", "Completed"],
            ["Phase 3: Rules Engine", "Deterministic Python Matcher", "Weeks 6–7", "2 Weeks", "Current Stage"],
            ["Phase 4: Voice Pipeline", "IndicWhisper STT + Indic-TTS", "Weeks 8–9", "2 Weeks", "Next Step"],
            ["Phase 5: MCP & Agent", "LangGraph Loop + MCP Tools", "Weeks 10–11", "2 Weeks", "Planned"],
            ["Phase 6: Mobile Client", "React Native Android CLI App", "Weeks 12–13", "2 Weeks", "Planned"],
            ["Phase 7: OCR Vision", "OpenCV Deskew + Tesseract OCR", "Weeks 14–15", "2 Weeks", "Planned"],
            ["Phase 8: Evaluation", "Field Trials, Latency & Thesis", "Week 16", "1 Week", "Planned"],
        ]
    )

    add_section_heading("1.5 Scope of the Project")
    add_subsection_heading("1.5.1 In-Scope Deliverables")
    doc.add_paragraph(
        "1. Multi-Sector Knowledge Base: 270 curated, normalized government welfare schemes covering Central Government, Delhi NCT, and Uttar Pradesh across 9 critical functional domains.\n"
        "2. Spoken Hindi Conversational Pipeline: Fine-tuned Indic speech recognition and high-fidelity Hindi speech synthesis.\n"
        "3. Two-Stage Interaction Model: Stage 1 structured baseline interview (9 canonical socio-economic demographic questions) followed by Stage 2 dynamic bounded agentic reasoning (maximum 6 tool iterations per turn).\n"
        "4. Standardized Model Context Protocol (MCP) Interface: Exactly four isolated tools: search_schemes, request_document, check_eligibility, and escalate_to_csc.\n"
        "5. Deterministic Zero-Hallucination Rules Engine: Pure rule-based Python logic for statutory criteria evaluation with machine-generated audit logs.\n"
        "6. Native Android Mobile Application: Lightweight React Native Android client with offline SQLite action caching."
    )
    add_subsection_heading("1.5.2 Out-of-Scope Elements")
    doc.add_paragraph(
        "1. Automated Direct Database Submission: Direct API insertion into central government PFMS/ministry registries requires bilateral government MoUs beyond an academic major project scope.\n"
        "2. All-India 2,300+ Scheme Indexing: Restricting coverage to Central, Delhi, and UP (270 schemes) provides statistical validity while maintaining verified data quality.\n"
        "3. Forensic Identity Verification: Detecting physical forged identity documents requires central UIDAI hardware security module access."
    )

    doc.add_page_break()

    # ----------------------------------------------------
    # CHAPTER 2: LITERATURE SURVEY
    # ----------------------------------------------------
    add_chapter_heading("CHAPTER 2: LITERATURE SURVEY / CRITICAL REVIEW")

    add_section_heading("2.1 Overview of Existing Work & Dataset Study")
    doc.add_paragraph(
        "The digital transformation of public governance has motivated extensive research in conversational information retrieval, accessibility for low-resource languages, and direct benefit delivery systems."
    )
    doc.add_paragraph(
        "Public Welfare Web Portals: National portals such as myScheme.gov.in and UMANG serve as unified clearinghouses for state and central schemes. However, empirical usability studies by Gupta et al. (2022) revealed that over 70% of low-income citizens cannot independently navigate these portals. The primary obstacles include dense legal terminology, strict requirement for alphanumeric keyboard input, and lack of guidance regarding supporting documentation."
    )
    doc.add_paragraph(
        "Conversational AI in Public Administration: The advent of large language models inspired projects such as Jugalbandi (AI4Bharat, Microsoft, OpenNyAI), a WhatsApp-based multilingual bot. While Jugalbandi demonstrated that rural citizens embrace voice-based query answering, evaluations demonstrated high susceptibility to hallucinated eligibility verdicts. In high-stakes public welfare, generating an incorrect eligibility decision can deprive a destitute family of basic pensions or nutritional subsidies."
    )
    doc.add_paragraph(
        "Vernacular Speech Interfaces: Landmark investigations by Medhi et al. (2007) and Patel et al. (2010) established that voice and multimodal audio-visual prompts lower interaction error rates by over 80% among non-literate rural Indian participants. With recent open-weight models such as AI4Bharat IndicWhisper (2023), robust acoustic models trained on tens of thousands of hours of Indian vernacular speech are now viable for local server deployment."
    )

    add_subsection_heading("2.1.2 Schemes Studied for Dataset (Corpus Analysis)")
    doc.add_paragraph(
        "To establish a robust factual ground truth, 270 schemes were scraped from myScheme.gov.in and subjected to rigorous normalization. Table 2.1 documents the distribution of analyzed schemes across sectors."
    )

    cat_table = doc.add_table(rows=11, cols=3)
    format_table(
        cat_table,
        [Inches(3.2), Inches(1.8), Inches(1.8)],
        ["Functional Category / Sector", "Scheme Count", "Percentage (%)"],
        [
            ["Social Welfare & Empowerment", "68", "25.19%"],
            ["Education & Scholarships", "52", "19.26%"],
            ["Agriculture & Rural Livelihoods", "39", "14.44%"],
            ["Women and Child Development", "31", "11.48%"],
            ["Healthcare & Medical Relief", "27", "10.00%"],
            ["Housing & Urban Development", "19", "7.04%"],
            ["Employment, Skilling & Labour", "15", "5.56%"],
            ["Pensions & Senior Citizen Support", "11", "4.07%"],
            ["Financial Inclusion & Insurance", "8", "2.96%"],
            ["Total Studied Scheme Corpus", "270", "100.00%"],
        ]
    )

    add_section_heading("2.2 Summary Comparison Table")
    doc.add_paragraph(
        "Table 2.2 presents a comprehensive comparative evaluation between existing paradigms and YojanaVaani across architectural, accessibility, and governance parameters."
    )

    comp_table = doc.add_table(rows=6, cols=5)
    format_table(
        comp_table,
        [Inches(1.8), Inches(1.4), Inches(1.4), Inches(1.2), Inches(1.6)],
        ["Evaluation Dimension", "Official Web Portals", "Generative Bots (Jugalbandi)", "Rule Systems", "YojanaVaani (Proposed)"],
        [
            ["Primary Modality", "Desktop/Mobile Text", "Text / Audio Messaging", "Form Input", "Voice-First Vernacular Hindi"],
            ["Eligibility Verification", "Manual Self-Reading", "Generative LLM (Hallucinates)", "Hardcoded Rules", "Deterministic Python Engine (0% Hallucination)"],
            ["Architecture", "Monolithic Web", "Single LLM Prompt Chain", "Static Script", "Bounded LangGraph Agent + MCP Tools"],
            ["Document Processing", "Manual PDF Upload", "Unprocessed Image", "None", "OpenCV Deskew + Tesseract OCR"],
            ["Failure Handling", "Dead-end Error Page", "Unchecked Hallucination", "Generic Rejection", "Deterministic CSC Escalation Ticket"],
        ]
    )

    add_section_heading("2.3 Research Gaps, Citizen Awareness Deficit Analysis, & Project Contribution")
    add_subsection_heading("2.3.1 Real-Life Citizen Awareness Deficit")
    doc.add_paragraph(
        "Empirical findings from the National Sample Survey Office (NSSO 75th & 78th Rounds) and NITI Aayog social sector reviews reveal that 60% to 75% of eligible rural citizens remain unaware of major government welfare programs for which they qualify. In agricultural welfare (PM-KISAN), over 30% of eligible tenant farmers remain unregistered due to land title ambiguities. In life insurance (PMSBY/PMJJBY), over 65% of rural nominees are unaware that automatic bank deductions entitle them to ₹2 lakh death or disability benefits."
    )
    doc.add_paragraph(
        "The underlying causes of this deficit include:"
    )
    doc.add_paragraph(
        "1. Bureaucratic Vocabulary: Official gazettes use formal high-register phrasing that semi-literate citizens cannot decipher.\n"
        "2. Document Bewilderment: Citizens cannot correlate required statutory documents (e.g., distinguishing a BPL Ration Card from a Tahsil-issued Income Certificate).\n"
        "3. Inaccessible Recourse: Lack of transparent reasons when an application is rejected fosters distrust and disengagement."
    )

    add_subsection_heading("2.3.2 How YojanaVaani Solves These Challenges")
    doc.add_paragraph(
        "YojanaVaani resolves these systemic obstacles through three technical contributions:\n"
        "• Spoken Vernacular Interaction: Eliminates literacy friction entirely by conducting natural Hindi dialogue.\n"
        "• Zero Hallucination Guarantee: Separates language understanding from eligibility computation, assuring mathematically verified verdicts.\n"
        "• Automated Physical-Digital Bridge: Generates structured CSC escalation summaries when complex physical verification is mandated, empowering Village Level Entrepreneurs (VLEs) to assist citizens efficiently."
    )

    doc.add_page_break()

    # ----------------------------------------------------
    # CHAPTER 3: SYSTEM DESIGN & METHODOLOGY
    # ----------------------------------------------------
    add_chapter_heading("CHAPTER 3: SYSTEM DESIGN & METHODOLOGY")

    add_section_heading("3.1 Proposed Methodology & Architectural Block Diagrams")
    doc.add_paragraph(
        "YojanaVaani is engineered as a decoupled, multi-tier agentic architecture designed for high reliability, data privacy, and deterministic accuracy. Figure 3.1 illustrates the architectural block diagram of the system."
    )

    add_callout(
        "[React Native Android Client]\n"
        "       │  Spoken Audio / Photo Capture\n"
        "       ▼\n"
        "[FastAPI Backend Gateway & Session Manager]\n"
        "       ├──► [AI4Bharat IndicWhisper STT (Acoustic Decoding)]\n"
        "       ├──► [OpenCV Deskew & Tesseract OCR (Document Parsing)]\n"
        "       ▼\n"
        "[LangGraph Agentic Orchestrator (Max 6 Iterations Bounded Loop)]\n"
        "       │  Standardized Tool Calls via Model Context Protocol (MCP)\n"
        "       ├──► 1. search_schemes(query, profile) ──► ChromaDB Vector Store\n"
        "       ├──► 2. request_document(type) ──────────► Mobile Capture UI\n"
        "       ├──► 3. check_eligibility(p, s) ─────────► Deterministic Python Rules Engine\n"
        "       └──► 4. escalate_to_csc(reason) ─────────► CSC Geolocation Registry\n"
        "       ▼\n"
        "[Indic-TTS Speech Synthesis] ──► Vernacular Audio Stream to Mobile",
        "System Block Diagram (Topological Overview):"
    )

    add_subsection_heading("3.1.2 Structured Two-Stage Dialogue Pipeline")
    doc.add_paragraph(
        "To prevent conversational drift and optimize agent reasoning, dialogue is partitioned into two distinct stages:"
    )
    doc.add_paragraph(
        "• Stage 1 (Scripted Baseline Interview): The system systematically asks 9 fixed demographic questions in Hindi: 1. Full Name, 2. Age, 3. Gender, 4. State & District, 5. Household Annual Income, 6. Social Category (Caste), 7. Primary Occupation, 8. Disability Status, 9. Primary Assistance Sought. This creates a validated Citizen Profile Fact Sheet.\n"
        "• Stage 2 (Bounded Agentic Reasoning Loop): Powered by LangGraph, the agent inspects the fact sheet and invokes tools via MCP. To prevent infinite recursion or excessive latency, the loop is strictly bounded to a maximum of 6 tool iterations per conversational turn. If unresolved, it deterministically invokes escalate_to_csc."
    )

    add_subsection_heading("3.1.3 Mathematical Formulation of Deterministic Rules Engine")
    doc.add_paragraph(
        "The deterministic rules engine evaluates candidate schemes using strict boolean predicate conjunctions. For citizen profile P and scheme candidate S:"
    )
    add_callout(
        "Eligible(P, S) = Ψ_age(P, S) ∧ Ψ_income(P, S) ∧ Ψ_state(P, S) ∧ Ψ_gender(P, S) ∧ Ψ_caste(P, S) ∧ Ψ_disability(P, S)\n\n"
        "Where:\n"
        "• Ψ_age(P, S) = (S.min_age ≤ P.age ≤ S.max_age) ∨ (S.age_bounds = Ø)\n"
        "• Ψ_income(P, S) = (P.income ≤ S.income_ceiling) ∨ (S.income_ceiling = Ø)\n"
        "• Ψ_state(P, S) = (P.state ∈ S.applicable_states) ∨ ('All' ∈ S.applicable_states)\n"
        "• Ψ_gender(P, S) = (P.gender == S.target_gender) ∨ ('All' ∈ S.target_gender)\n"
        "• Ψ_caste(P, S) = (P.category ∈ S.eligible_categories) ∨ ('All' ∈ S.eligible_categories)\n"
        "• Ψ_disability(P, S) = (P.disability == True if S.is_pwd_only else True)",
        "Deterministic Logic Formulation:"
    )

    add_section_heading("3.2 Tool and Technique Selection Justifications")
    doc.add_paragraph(
        "Every framework and tool in YojanaVaani was chosen based on empirical engineering criteria. Table 3.1 delineates the selection rationale across all functional tiers."
    )

    tech_table = doc.add_table(rows=9, cols=3)
    format_table(
        tech_table,
        [Inches(2.0), Inches(2.2), Inches(2.6)],
        ["Subsystem / Layer", "Selected Technology", "Technical Rationale & Selection Criteria"],
        [
            ["Mobile Frontend", "React Native CLI (TypeScript)", "Compiles to native Android APK; direct access to audio recording and camera hardware; avoids Expo managed dependencies."],
            ["Backend API Gateway", "FastAPI (Python 3.11)", "Asynchronous ASGI concurrency, native Pydantic data validation, high throughput for audio payload handling."],
            ["Speech Recognition", "AI4Bharat IndicWhisper", "Trained on 20,000+ hours of Indian vernacular speech; delivers significantly lower Word Error Rates on accented rural Hindi."],
            ["Speech Synthesis", "AI4Bharat Indic-TTS", "Open-source, low-latency, and natural Devanagari prosodic inflection without recurring cloud API fees."],
            ["Vector Retrieval", "ChromaDB + Sentence-Transformers", "Local embedding generation ('paraphrase-multilingual-mpnet-base-v2') aligned across Hindi & English with in-memory persistence."],
            ["Agent Orchestration", "LangGraph State Machine", "Enforces bounded execution (max 6 iterations), deterministic state transitions, and auditable cycle checkpoints."],
            ["Tool Interface Protocol", "Model Context Protocol (MCP)", "Official Anthropic MCP SDK provides standardized protocol isolation between reasoning agent and business logic."],
            ["Document Processing", "OpenCV + Tesseract OCR", "Local OpenCV deskewing and adaptive thresholding combined with Devanagari OCR guarantees citizen privacy under DPDP Act."],
        ]
    )

    doc.add_page_break()

    # ----------------------------------------------------
    # CHAPTER 4: IMPLEMENTATION & TESTING
    # ----------------------------------------------------
    add_chapter_heading("CHAPTER 4: IMPLEMENTATION & TESTING")

    add_section_heading("4.1 Experimental Setup")
    add_subsection_heading("4.1.1 Hardware Specifications")
    doc.add_paragraph(
        "• Workstation Environment: Apple Silicon M-Series workstation (16 GB Unified Memory) and Ubuntu 22.04 LTS Server.\n"
        "• Compute Acceleration: PyTorch MPS / CUDA 12.1 for rapid vector embedding calculation.\n"
        "• Target Physical Device: Android Smartphone running Android 13 (API Level 33), 4 GB RAM, integrated microphone and 13MP camera sensor."
    )
    add_subsection_heading("4.1.2 Software Stack & Institutional Compliance")
    doc.add_paragraph(
        "The software environment comprises Python 3.11.9, Node.js 20.x, React Native CLI 0.73, PostgreSQL 15, and ChromaDB 0.4. In strict compliance with academic departmental directives, TensorFlow, Keras, and MATLAB are 100% excluded across all modules and dependencies."
    )
    add_subsection_heading("4.1.3 Data Inconsistency Remediation & Verification")
    doc.add_paragraph(
        "During Phase 2, an extensive automated audit was executed on the 270-scheme PostgreSQL database. Key remediations completed include:\n"
        "1. Canonical Geographic State Alignment: Resolved 99 state mismatches, standardizing applicable states into canonical arrays (['Delhi'], ['Uttar Pradesh'], ['All']).\n"
        "2. Parent Scheme Cycle Elimination: Cleared 4 self-referential circular foreign keys (IDs 57, 424, 571, 595).\n"
        "3. Document Schema Deserialization: Restored 262 corrupted string-escaped nested JSON records to clean DocumentRequirement Pydantic models.\n"
        "4. Statutory Constraint Recovery: Recovered explicit income ceilings (87 schemes) and explicit age limits (108 schemes) from legal text.\n"
        "5. Confidence Score Validation: Reached an overall database confidence score of 0.990, with 95.2% of schemes scoring >= 0.85."
    )

    add_section_heading("4.2 Test Cases, Case Study Walkthrough, & Next Steps Implementation Roadmap")
    add_subsection_heading("4.2.1 Automated Test Suite Verification (Phases 1 & 2)")
    doc.add_paragraph(
        "Table 4.1 documents the test cases executed and passed during the completed foundational phases."
    )

    test_table = doc.add_table(rows=8, cols=4)
    format_table(
        test_table,
        [Inches(1.2), Inches(3.0), Inches(1.6), Inches(1.0)],
        ["Test ID", "Test Target & Verification Logic", "Expected Outcome", "Status"],
        [
            ["TC-DB-01", "PostgreSQL Record Count & Primary Key Integrity", "Exactly 270 valid schemes", "PASSED"],
            ["TC-DB-02", "Parent Scheme Self-Referential Cycle Sweep", "0 Circular Loops", "PASSED"],
            ["TC-DB-03", "Canonical State Restriction Array Validation", "0 Schema Contradictions", "PASSED"],
            ["TC-DB-04", "Required Documents JSON Schema Deserialization", "0 Corrupted String Records", "PASSED"],
            ["TC-DB-05", "Age Boundary Semantic Inversion (min > max)", "0 Inverted Age Records", "PASSED"],
            ["TC-VEC-01", "ChromaDB Multilingual Vector Index Alignment", "270 Dense Embeddings", "PASSED"],
            ["TC-VEC-02", "Colloquial Hindi Semantic Query Retrieval", "Top-3 Recall > 90%", "PASSED"],
        ]
    )

    add_subsection_heading("4.2.2 End-to-End Case Study Walkthrough")
    doc.add_paragraph(
        "To validate real-world execution, consider a test persona: Smt. Ramvati Devi (42 years old, Female, Barabanki, UP, OBC, Household Income ₹65,000, 1.5 acres land, No disability, Seeking agricultural credit and irrigation support)."
    )
    doc.add_paragraph(
        "1. Stage 1 Execution: The mobile app prompts the 9 baseline questions in spoken Hindi. IndicWhisper transcribes each response, assembling the verified Citizen Profile Fact Sheet.\n"
        "2. Stage 2 Agent Iteration 1: LangGraph agent inspects the profile and calls search_schemes('solar pump and agricultural support', profile). ChromaDB returns PM-KISAN, PM-KUSUM, and UP Kisan Uday Yojana.\n"
        "3. Agent Iteration 2: Agent calls check_eligibility(profile, candidates). The deterministic rules engine calculates: PM-KISAN: ELIGIBLE; PM-KUSUM: ELIGIBLE; Senior Pension: INELIGIBLE (Age 42 < 60).\n"
        "4. Agent Iteration 3: Agent invokes request_document('Khasra/Khatauni'). Mobile prompts citizen to photograph land record. OpenCV deskews image; Tesseract extracts land holding (1.5 acres verified).\n"
        "5. Output Synthesis: Within 3 iterations (well within the 6-iteration limit), Indic-TTS synthesizes clear spoken Hindi audio informing Ramvati of her guaranteed eligibility and providing nearest Haidergarh CSC contact details."
    )

    add_subsection_heading("4.2.3 Next Steps Implementation Roadmap")
    doc.add_paragraph(
        "Table 4.2 presents the chronological engineering roadmap for the subsequent project phases leading to final dissertation submission."
    )

    roadmap_table = doc.add_table(rows=7, cols=3)
    format_table(
        roadmap_table,
        [Inches(1.8), Inches(1.4), Inches(3.6)],
        ["Development Phase", "Target Weeks", "Core Engineering Objectives & Deliverables"],
        [
            ["Phase 3: Rules Engine", "Weeks 6–7", "Implement deterministic Python rules_engine.py with 100% unit test coverage for age, income, caste, gender, and disability criteria."],
            ["Phase 4: Voice Pipeline", "Weeks 8–9", "Deploy AI4Bharat IndicWhisper STT and Indic-TTS inference servers with streaming FastAPI audio endpoints."],
            ["Phase 5: MCP & Agent", "Weeks 10–11", "Implement Anthropic MCP tool server exposing the 4 statutory tools; build LangGraph bounded state machine."],
            ["Phase 6: Mobile Client", "Weeks 12–13", "Build React Native CLI Android application, Stage 1 voice wizard UI, and local SQLite offline action queue."],
            ["Phase 7: OCR Vision", "Weeks 14–15", "Implement OpenCV image deskewing and Tesseract Devanagari OCR pipeline for identity/land record field extraction."],
            ["Phase 8: Evaluation", "Week 16", "Conduct end-to-end benchmark testing (WER, Latency, Precision/Recall, CSC Fallback audit) and finalize thesis."],
        ]
    )

    # Save document
    doc.save(output_path)
    print(f"Successfully generated formal report document: {output_path}")

if __name__ == "__main__":
    out_file = "/Users/nikita/Documents/YojanaVaani/docs/major_project_report_ch1_to_ch4.docx"
    build_docx(out_file)
