# Redline mechanics — building and verifying a tracked-changes BAA

How to turn approved positions into a DOCX with tracked changes and anchored comments, and
how to prove you did not corrupt the counterparty's document.

**Do not start here.** Gate 1 (review only) and Gate 2 (two editable files, client edits and
hands back) come first. See the skill body. This file is Gate 3.

---

## Toolchain constraints (verified on JP's Mac, 2026-07-30)

Check these before planning the build. Several obvious tools are unavailable.

| Tool | Status | Consequence |
|---|---|---|
| Python | **3.9 only** | The bundled `document-skills:docx` helpers (`merge_runs.py`, `comment.py`, `validate.py`, `accept_changes.py`) use `str \| None` unions and `ignore_cleanup_errors` — they crash on import. Do the OOXML work directly. |
| `lxml` | Available (6.x) | Use it. Preserves namespaces correctly on round-trip. |
| `python-docx` | Available (1.2) | Cannot create tracked changes. Not useful here. |
| LibreOffice / `soffice` | **Not installed** | No headless convert. The skill's `soffice.py` wrapper also fails on Python 3.9. |
| `pandoc` | **Not installed** | No markdown round-trip. |
| `pdftoppm` | **Not installed** | Cannot rasterise pages. |
| **Pages.app** | Available | The workaround. Opens DOCX and exports PDF via AppleScript. Use for pagination and as an opens-without-corruption check. |
| `pypdf` | Available | Per-page text extraction. |
| `timeout` | **Not present** (macOS) | Use `subprocess.run(..., timeout=)` in Python instead. |

### Page numbers for the negotiation email

The client will want "page 5, Limitation of Liability". Get real numbers, do not estimate:

```python
import subprocess, os
src = "/path/to/BAA.docx"; out = os.path.abspath("baa_pages.pdf")
script = f'''
tell application "Pages"
  set d to open POSIX file "{src}"
  delay 2
  export d to POSIX file "{out}" as PDF
  delay 1
  close d saving no
end tell'''
subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=180)
```

Then map clauses to pages with `pypdf`, searching each page's extracted text for a
distinctive phrase from the clause. Note in the email that pagination is from the rendered
document; Word may differ by a line. Prefer **section plus clause caption** as the primary
reference and page as a helper — many BAAs have unreliable sub-clause numbering (see below).

---

## Unreliable clause numbering

Before citing any clause number, check whether the document uses more than one Word numbering
instance. A second `numId` pointing at the same `abstractNum` restarts the counter partway
through a section, so two clauses can render with the same number and duplicate captions get
missed.

```python
from lxml import etree
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda t: f"{{{W}}}{t}"
# inspect w:numPr/w:numId per paragraph; more than one numId at the same ilvl = restart risk
```

If numbering is unreliable, **cite by caption throughout** and say so in the report. Duplicate
captions ("Access to Records" twice) are a real and easily missed defect.

---

## Building tracked changes

Work on the unpacked directory, not through a library:

```bash
unzip -q original.docx -d unpacked/
find unpacked -type l -delete      # untrusted third-party docx
# ... edit unpacked/word/document.xml with lxml ...
(cd unpacked && zip -Xrq ../REDLINE.docx .)
```

### The replacement pattern that works

Word splits sentences across runs unpredictably. Matching a single run mid-paragraph is the
main source of corrupted output.

**Rule: delete from the matching run through the end of the paragraph, and supply the full
replacement including its leading separator.**

Matching only the run containing your target phrase produces two failure modes seen in
practice:
- the `".  "` run after a caption gets swallowed, yielding `Access to RecordsBusiness Associate agrees`
- a trailing run survives, yielding duplicated text such as `(collectively, the "Agreement"), (the "Agreement") with Business Associate`

Inspect the actual run structure first:

```python
for i, r in enumerate(p.findall(w("r"))):
    t = r.find(w("t"))
    if t is not None:
        print(f"run[{i}] {t.text[:110]!r}")
```

Then delete `runs[idx:]` and insert one new run carrying the whole replacement.

### Revision markup

- Wrap deleted runs in `<w:del w:id w:author w:date>`; inside, `<w:t>` becomes `<w:delText>`.
- Wrap inserted runs in `<w:ins w:id w:author w:date>`.
- Set `xml:space="preserve"` on every `<w:t>` and `<w:delText>` — leading and trailing spaces
  around clause separators matter.
- Clone the formatting of the run you are replacing rather than building a run from scratch.
- For a wholly new paragraph, mark the paragraph mark inserted too:
  `<w:pPr><w:rPr><w:ins .../></w:rPr></w:pPr>`. The `<w:ins/>` must come **first** among the
  `rPr` children — child order is schema-enforced.
- Use a meaningful author name. It appears in Word's review pane.

---

## Comments

Comments need a part, a relationship, and a content-type override, plus anchors in
`document.xml`. Miss the anchors and the comment exists but is invisible.

1. `word/comments.xml` — `<w:comments>` root, one `<w:comment w:id w:author w:date w:initials>`
   each, containing a `<w:p><w:r><w:t>`.
2. `word/_rels/document.xml.rels` — a Relationship with Type
   `.../officeDocument/2006/relationships/comments`, Target `comments.xml`.
3. `[Content_Types].xml` — Override for `/word/comments.xml`, ContentType
   `application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml`.
4. In `document.xml`, around the edited region:
   `<w:commentRangeStart w:id="N"/>` … `<w:commentRangeEnd w:id="N"/>` followed by a run
   containing `<w:commentReference w:id="N"/>`.

Anchor each comment across **both** the `w:del` and the `w:ins` so it reads against the change
as a whole.

---

## Verification — mandatory, not optional

Three checks. Do not ship without all three.

**1. Reject-all must reproduce the original exactly.** This is the one that catches untracked
edits, which are invisible in the accepted view and are the worst possible defect — a silent
alteration of the counterparty's document.

```python
def paras(xml, mode):          # mode: "accept" | "reject"
    d = etree.fromstring(xml); out = []
    for p in d.iter(w("p")):
        buf = []
        for n in p.iter():
            if n.tag == w("t"):
                if mode == "reject" and any(a.tag == w("ins") for a in n.iterancestors()):
                    continue
                buf.append(n.text or "")
            elif n.tag == w("delText"):
                if mode == "accept":
                    continue
                buf.append(n.text or "")
        out.append("".join(buf))
    return [t for t in out if t.strip()]

assert paras(original_xml, "accept") == paras(redline_xml, "reject")
```

**2. Read the accepted text of every changed paragraph.** Reject-all passing does not mean the
accepted text is clean — the separator and duplication bugs above both survive check 1. Print
each changed paragraph in accepted form and read it.

**3. Open both files.** Export via Pages. A file that will not open is worse than no redline.

Also confirm: `commentRangeStart` / `commentRangeEnd` / `commentReference` id sets are equal to
the ids in `comments.xml`, and no `delText` sits outside a `w:del`.

---

## Producing the clean copy

Accepting changes without LibreOffice: drop every `w:del` subtree, unwrap every `w:ins`
(splicing children into the parent, except an `rPr` insert-mark which is simply removed), and
strip comment markers plus the comments part, relationship and content-type override. Then
verify `paras(clean, "accept") == paras(redline, "accept")`.

Note the known artifact: a fully deleted paragraph should merge into the next one. Naive
accept leaves an empty paragraph behind, which shows as a stray empty bullet in a numbered
list. Check paragraph deletions in the XML rather than trusting the rendered view.

---

## Google Docs suggestion-mode review

Google Docs **imports Word tracked changes as native suggestions** and Word comments as
comments. This is the cleanest way to let a client or counterparty accept and reject inline.

Upload the DOCX to Drive and open it as a Google Doc — either by drag-and-drop plus "Open
with Google Docs", or via the Drive API by setting the target mimeType to
`application/vnd.google-apps.document` on create.

**Do not attempt to create suggestions through the Google Docs API.** `batchUpdate` writes are
applied as direct edits; `SuggestionsViewMode` is a read-only parameter. Conversion on import
is the only route to native suggestions.

Note: the `gws` CLI was broken on this machine (a jdeploy Java wrapper failing to install a JRE
on arm64) and `gws-shared/SKILL.md` was absent. Verify `gws` works before promising automation;
manual upload is a reliable fallback and takes seconds.

---

## Deliverable set

| File | Purpose |
|---|---|
| `*_REDLINE.docx` | Tracked changes plus one anchored comment per edit |
| `*_CLEAN.docx` | Changes accepted, comments stripped |
| `*_Redline_Email.txt` | Plain text, per edit: page, the ask, and the proposed wording verbatim |
| original | Untouched, kept alongside for diffing |

The email carries the proposed wording verbatim so the counterparty can act on it without
opening the attachment. Confirm it matches what is actually in the DOCX — they drift when
edits are revised late.
