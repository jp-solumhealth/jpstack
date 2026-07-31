#!/usr/bin/env python3
"""
contract_qa.py — deterministic mechanical QA for a commercial contract (.docx or .pdf).

Flags the defects a human skims past: em/en dashes, straight quotes, all-caps wall-of-text
clauses, buzzwords / AI tells, drafting brackets and TBD/(proposed) placeholders, British/American
spelling mix, table-width mismatches (DOCX), and every "Section N.N" reference with no matching
heading (dangling-reference heuristic).

Usage:
    python3 contract_qa.py path/to/contract.docx
    python3 contract_qa.py path/to/contract.pdf
    python3 contract_qa.py --selftest      # prove the text checkers work

Dependencies: standard library + lxml (for DOCX). PDF needs pypdf if reviewing a .pdf.
Report only; never edits the file. Exit code 0 if no FLAGs, 1 if any FLAG.
"""
import sys, re, zipfile

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

BUZZWORDS = ['leverage', 'seamless', 'robust', 'streamline', 'empower', 'unlock',
             'synerg', 'best-in-class', 'cutting-edge', 'world-class', 'game-chang',
             'turnkey', 'frictionless']
BRITISH = ['licence', 'wilful', 'unauthorised', 'authorisation', 'programme ', 'defence',
           'organis', 'recognise', 'fulfil ']
PLACEHOLDERS = ['[attach', 'tbd', 'to be determined', '(proposed)', 'to be confirmed',
                'lorem ipsum', 'xxxx', '[ ]', 'insert ']


# ---------- extractors ----------
def docx_text_and_tables(path):
    z = zipfile.ZipFile(path)
    from lxml import etree
    doc = etree.fromstring(z.read('word/document.xml'))
    text = ' '.join(t.text or '' for t in doc.iter(W + 't'))
    # headings: paragraphs styled Heading1/Heading2, or starting "N." / "N.N"
    heads = []
    for p in doc.iter(W + 'p'):
        sty = p.find(f'{W}pPr/{W}pStyle')
        s = sty.get(W + 'val') if sty is not None else ''
        tx = ''.join(n.text or '' for n in p.iter(W + 't')).strip()
        if tx and (s in ('Heading1', 'Heading2') or re.match(r'^\d{1,2}(\.\d{1,2})?[.\s]', tx)):
            heads.append(tx)
    # tables: (width, sum(gridCol)) per table
    tables = []
    for tb in doc.iter(W + 'tbl'):
        tw = tb.find(f'{W}tblPr/{W}tblW')
        w = int(tw.get(W + 'w')) if tw is not None and tw.get(W + 'w') else None
        cols = sum(int(g.get(W + 'w')) for g in tb.iter(W + 'gridCol') if g.get(W + 'w'))
        tables.append((w, cols))
    raw_xml = z.read('word/document.xml').decode('utf8')
    return text, heads, tables, raw_xml


def pdf_text(path):
    try:
        import pypdf
    except ImportError:
        sys.exit("PDF review needs pypdf: pip install pypdf")
    r = pypdf.PdfReader(path)
    text = ' '.join((pg.extract_text() or '') for pg in r.pages)
    heads = [ln.strip() for ln in text.split('\n') if re.match(r'^\d{1,2}(\.\d{1,2})?[.\s]', ln.strip())]
    return re.sub(r'\s+', ' ', text), heads, [], None


# ---------- checks (each returns (label, ok, detail)) ----------
def check_text(text, heads, tables, raw_xml):
    out = []
    def flag(label, ok, detail=''):
        out.append((label, ok, detail))

    flag('no em/en dashes', '—' not in text and '–' not in text,
         'found ' + (('em' if '—' in text else '') + (' en' if '–' in text else '')).strip())
    caps = [m for m in re.findall(r'[A-Z][A-Z ,.;:()’“”$%0-9-]{40,}', text)]
    flag('no all-caps clause runs', not caps, (caps[0][:60] + '…') if caps else '')
    bz = sorted({b for b in BUZZWORDS if b in text.lower()})
    flag('no buzzwords / AI tells', not bz, ', '.join(bz))
    br = sorted({b for b in BRITISH if b in text.lower()})
    flag('no British spelling (American only)', not br, ', '.join(br))
    ph = sorted({b for b in PLACEHOLDERS if b in text.lower()})
    flag('no drafting brackets / TBD / (proposed)', not ph, ', '.join(ph))

    if raw_xml is not None:  # DOCX-only
        straight = bool(re.search(r'<w:t[^>]*>[^<]*[\x22\x27]', raw_xml))
        flag('no straight quotes in body text', not straight)
        fonts = set(re.findall(r'w:ascii="([^"]+)"', raw_xml))
        flag('single consistent font', len(fonts) <= 1, ', '.join(sorted(fonts)))
        mism = [(w, c) for (w, c) in tables if w is not None and w != c]
        flag('tables width-aligned (width == sum of columns)', not mism,
             f'{len(mism)} mismatched of {len(tables)}')
        breaks = raw_xml.count('<w:br w:type="page"/>')
        flag('no stray page breaks', breaks == 0, f'{breaks} standalone page break(s)')

    # dangling-reference heuristic: every "Section N[.M]" whose top-level N has no heading
    head_nums = set()
    for h in heads:
        m = re.match(r'^(\d{1,2})', h.strip())
        if m:
            head_nums.add(m.group(1))
    refs = set(re.findall(r'Section (\d{1,2})(?:\.\d{1,2})?', text))
    dangling = sorted(r for r in refs if r not in head_nums)
    # namespace note: Order-Form (bare "Section 4.x") vs Terms ("Section N of the Terms")
    flag('Section references resolve to a heading', not dangling,
         'no heading for Section ' + ', '.join(dangling) + ' (check namespaces)' if dangling else '')
    # the classic post-restructure trap
    trap = 'Section 11 of the Terms' in text and not any(h.strip().startswith('11') for h in heads)
    flag('no dangling "Section 11 of the Terms" after moved Definitions', not trap)

    return out


def run(path):
    if path.lower().endswith('.docx'):
        text, heads, tables, raw = docx_text_and_tables(path)
    elif path.lower().endswith('.pdf'):
        text, heads, tables, raw = pdf_text(path)
    else:
        sys.exit('Provide a .docx or .pdf')
    results = check_text(text, heads, tables, raw)
    print(f'\ncontract_qa — {path}\n' + '=' * 60)
    n_flag = 0
    for label, ok, detail in results:
        tag = '  PASS ' if ok else '  FLAG '
        if not ok:
            n_flag += 1
        print(f'{tag} {label}' + (f'   [{detail}]' if detail else ''))
    print('=' * 60)
    print(f'{len(results) - n_flag}/{len(results)} passed, {n_flag} flag(s)')
    print('headings found:', len(heads), '| tables:', len(tables))
    return 1 if n_flag else 0


def selftest():
    bad = ('This Agreement — governed by Delaware law — shall leverage a seamless licence. '
           'THE PLATFORM IS PROVIDED AS IS AND SOLUM HEALTH DISCLAIMS ALL WARRANTIES OF EVERY KIND WHATSOEVER. '
           'See Section 9 of the Terms. [Attach BAA here] (proposed).')
    res = check_text(bad, ['1. Scope', '2. Terms'], [], None)
    flags = {label for label, ok, _ in res if not ok}
    expect = {'no em/en dashes', 'no buzzwords / AI tells', 'no all-caps clause runs',
              'no British spelling (American only)', 'no drafting brackets / TBD / (proposed)',
              'Section references resolve to a heading'}
    missing = expect - flags
    print('selftest flags:', sorted(flags))
    print('SELFTEST', 'PASS' if not missing else f'FAIL (missed {missing})')
    return 0 if not missing else 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == '--selftest':
        sys.exit(selftest())
    sys.exit(run(sys.argv[1]))
