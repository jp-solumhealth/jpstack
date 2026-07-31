# Drafting Standards & Clean-Language QA

The contract must read like modern enterprise paper from a top technology-transactions practice:
professional, concise, plain English, legally enforceable, and free of AI-generation tells. Apply
this to any clause we draft or rewrite, and check the whole document against it before signature.

## Plain, modern legal English

- Active voice; short sentences; short paragraphs. Split anything over ~40 words.
- Say what happens, plainly. Define terms once, use them consistently.
- Understandable by procurement, executives, operations, and counsel — not just lawyers.
- No archaic legalese: strike **herein, thereof, wherein, whereas, witnesseth, hereinafter,
  aforesaid**. Each has a plain equivalent.
- Avoid "Notwithstanding" pile-ups. Prefer "This overrides Section X" or "Instead of Section X" where
  precision allows. If you align the Terms directly to the deal, most overrides disappear.
- No customer-success or sales language inside legal text ("weekly touchpoints", "as a goodwill
  accommodation", "remain reasonably engaged") — state the right or obligation plainly.

## Conspicuousness without walls of caps

- Warranty disclaimers and liability caps must be **conspicuous** (UCC 1-201(b)(10)) — but
  **contrasting type (bold) satisfies it**; a wall of ALL CAPS reads as less readable and courts
  increasingly disfavor it. Render disclaimers and the cap in **bold sentence case**, not caps.
- A disclaimer of implied warranties must still name **"merchantability"** (UCC 2-316(2)) to be
  effective — do not paraphrase it away.

## Cross-reference discipline

- Every "Section N" / "Section N.N" resolves to a heading that exists. After any restructure, re-run
  the check — moving a section breaks every pointer to it.
- Distinguish namespaces explicitly: "Section N **of the Terms**" vs a bare "Section 4.x" for the
  Order Form / Key Terms. Keep the convention consistent so bare references are unambiguous.
- Classic trap: moving **Definitions** out of the Terms leaves "Section 11 of the Terms" dangling —
  it must then appear nowhere; repoint every reference to "the Definitions."
- A **modification recap** ("this Section modifies Sections X, Y, Z and supplements A, B") must list
  exactly the sections actually touched — no more, no less.

## Defined-term hygiene

- Every capitalized defined term is defined **once**, in the Definitions, and used consistently.
- Flag **capitalized-but-undefined** terms (e.g., a stray "Minimum Fee" when only "Fees" is defined)
  and **defined-but-unused** terms (delete them, or the definition orphan invites a "is there also
  a separate X?" question).
- Keep definitions alphabetical and one format; a bolt-on definition using a different lead-in
  ("means the…" among bare "X  the…") reads as a template seam.

## AI-generation tells to remove

These read as machine-generated to a sophisticated GC — remove all of them:

- **Em dashes and en dashes** ( — , – ). Use commas, periods, parentheses, or a colon. (Enforced by
  `scripts/contract_qa.py`.)
- **Straight quotes/apostrophes** in a document that otherwise uses curly typographic quotes.
- **Buzzwords**: leverage, seamless, robust, streamline, empower, unlock, synergy, best-in-class,
  cutting-edge, world-class.
- **British/American spelling mix** in one document (licence/license, wilful/willful, unauthorised,
  programme, defence). Pick one (American for a Delaware contract) and sweep.
- **Over-parallel structure and over-consistent paragraph lengths**; unnaturally precise ranges
  ("within one (1) to ten (10) days" → "within ten (10) days").
- **Duplicate clauses** (the same upgrade/downgrade rule stated in two sections; two differently
  triggered 30-day exit rights) — template accretion; keep one.
- **Drafting brackets / placeholders** ("[Attach … here]", "TBD", "(proposed)", "to be confirmed")
  in a document called final — convert to real text or a formal "attached hereto" recital.
- Deal-specific text stranded inside a versioned master (one customer's Order Form number inside the
  generic Terms).

## Formatting checklist (measure it)

Single font · consistent heading numbering with no duplicates · correct margins/page size · page
breaks only where intended, none stray/blank · tables width-aligned (table width = sum of column
widths) with marked header rows · appendices lettered in order · dual-party signature block ·
version stamp in header and body · no straight quotes · no dashes · no all-caps clause runs. The QA
script checks the mechanical ones on a DOCX or PDF.
