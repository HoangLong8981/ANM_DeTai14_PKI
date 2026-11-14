---
name: ieee-report-writer
description: Formats, structures, and writes technical reports, lab assignments, and research papers following IEEE standard guidelines. Use when the user requests IEEE-style reporting, academic paper formatting, IEEE citations, or technical documentation structure for engineering and IT projects.
---

# IEEE Report Writer

A specialized skill for structuring, drafting, and validating academic and technical laboratory reports in accordance with the IEEE standard publication style.

## When to Use

- Formatting university lab reports, capstone projects, or technical documentation in IEEE format.
- Structuring engineering papers into standard sections: Abstract, Introduction, System Design, Implementation, Results, Conclusion, References.
- Formatting citations and references using IEEE bracketed numeric notation [1], [2].
- Converting raw notes or lab logs into formal academic technical prose.

## Core Structure and Heading Hierarchy

Structure all comprehensive reports using IEEE standard sectional hierarchy:

1. Title and Abstract:
   - Title: Centered, concise, and descriptive of the engineering objective.
   - Abstract: Single paragraph (150-250 words) summarizing objective, methodology, key findings, and technical conclusions.
   - Keywords: 4 to 6 comma-separated technical keywords.

2. Heading Levels:
   - Primary Headings: Roman numerals, capitalized, centered or bold (e.g., I. INTRODUCTION, II. SYSTEM ARCHITECTURE).
   - Secondary Headings: Capital letters, title case, left-aligned or italicized/bold (e.g., A. Cryptographic Foundations, B. Certificate Authority Architecture).
   - Tertiary Headings: Arabic numerals followed by parentheses (e.g., 1) Key Generation Process, 2) Revocation Verification).

## Formatting Rules

Follow these rules for technical presentation:

1. Figures and Tables:
   - Reference every figure and table in the preceding text before it appears.
   - Figure captions are placed below the figure: "Fig. 1. Network topology for PKI deployment."
   - Table captions are placed above the table: "TABLE I. COMPARISON OF CRL AND OCSP CHARACTERISTICS".

2. Equations and Mathematical Notation:
   - Format equations with centered notation and right-aligned sequential numbering:
     $$E = mc^2 \quad (1)$$
   - Refer to equations in text as "(1)" or "Equation (1)".

3. Citations and References:
   - Use bracketed numbers sequentially in order of appearance: [1], [2], [1, 2], [3-5].
   - Place citation brackets inside sentence punctuation: "...as demonstrated in previous studies [1]."
   - References section is ordered by citation number, never alphabetically:
     - [1] J. Doe, "Title of paper," *IEEE Trans. Inf. Forensics Security*, vol. 10, no. 2, pp. 100-110, Feb. 2024.
     - [2] OpenSSL Project, "OpenSSL Cryptography and SSL/TLS Toolkit," openssl.org, 2024.

4. Academic Tone and Precision:
   - Use formal, objective third-person or passive voice. Avoid informal conversational prose.
   - Avoid generic claims. Replace vague descriptions with concrete parameters, command syntax, throughput metrics, or exact status codes.

## Step-by-Step Report Generation Workflow

When generating report sections from user data:

1. Step 1: Establish Section Scope:
   - Identify the target section (e.g., Section III. Experimental Setup).
   - Do not merge distinct sections unless explicitly requested.

2. Step 2: Ingest Technical Context:
   - Extract raw configurations, terminal outputs, IP addresses, and command arguments from user-provided notes or notebooks.
   - Preserve exact commands, parameters, and variable values without hallucination.

3. Step 3: Draft Sectional Text:
   - Write thorough analytical descriptions connecting theoretical rationale to experimental actions.
   - Provide concrete test scenarios, observed outputs, and verification checks.

4. Step 4: Verification and Quality Check:
   - Ensure all citations correspond to entries in the References section.
   - Verify that tables and figures are numbered sequentially.
   - Ensure no conversational filler or ungrounded conclusions are present.

## Gotchas

- Do not use conversational bullet lists where continuous formal paragraphs are required by IEEE format.
- Do not cite references alphabetically. IEEE strictly requires order of appearance.
- Do not invent experimental results or command logs. Always request or extract them from real user lab outputs.
- Never place table captions below tables or figure captions above figures.
