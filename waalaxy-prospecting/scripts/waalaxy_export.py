#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build and QA a Waalaxy-ready CSV from an enriched prospect list.

Waalaxy renders First Name straight into "Hi {{firstName}}", so a dirty name ships a broken
message to a real prospect. This script normalises names and LinkedIn URLs, splits the rows
Waalaxy cannot use (no LinkedIn profile) into their own file, and refuses to stay silent about
anything it could not fix.

    python3 waalaxy_export.py --selftest
    python3 waalaxy_export.py --in enriched.csv --outdir ./out --segment providers

Input columns are matched case-insensitively; any of these work:
    name | full name            (or)  first name + last name
    company | organization
    title | position
    email
    linkedin | linkedin url | linkedin profile
    category, priority, email status        (optional, passed through)
"""
import argparse, csv, os, re, sys, unicodedata
from collections import Counter

# --------------------------------------------------------------------------- names

# Credential tokens that must never be mistaken for part of a name or a title.
CREDENTIALS = {
    'ms', 'm.s.', 'ma', 'm.a.', 'med', 'm.ed.', 'msed', 'mssped', 'm.s.sped.', 'mba', 'ba', 'bs',
    'phd', 'ph.d.', 'ph.d', 'edd', 'ed.d.', 'ed.d', 'dbh', 'psyd', 'jd', 'md',
    'bcba', 'bcba-d', 'bcaba', 'lba', 'laba', 'iba', 'rbt', 'qba', 'coba', 'cas', 'lbs',
    'ccc-slp', 'lmft', 'lcsw', 'limhp', 'lmhc', 'shrm-scp', 'acc', 'racr', 'cphq', 'obm',
    'otr/l', 'pt', 'dpt', 'rn', 'cpa',
}
# Words that mark a comma-fragment as a job title rather than a credential.
TITLE_WORDS = ('ceo', 'coo', 'cfo', 'cro', 'cto', 'chief', 'founder', 'owner', 'president',
               'director', 'vp', 'vice president', 'manager', 'partner', 'principal', 'head of',
               'executive', 'consultant')

# Only fired for the exact lowercase token: a genuine "Lan" keeps its capital L and is left alone.
OCR_FIXES = {'lan': 'Ian'}


def _cap(token):
    """Capitalise one name token without destroying intentional inner capitals."""
    if not token:
        return token
    for sep in ('-', "'"):
        if sep in token and len(token) > 1:
            return sep.join(_cap(p) for p in token.split(sep))
    if any(c.islower() for c in token) and token[:1].isupper():
        return token                      # DiNovi, McComas, O'Brien already correct
    out = token[:1].upper() + token[1:].lower()
    m = re.match(r"^(Mc)(.)(.*)$", out)
    if m:
        out = m.group(1) + m.group(2).upper() + m.group(3)
    return out


def clean_name_token(token, ocr_fixes=True, report=None):
    """Normalise a single name token for use in {{firstName}}."""
    t = token.strip().strip(',')
    t = re.sub(r'"[^"]*"', '', t).strip()          # drop "Paulie" style nicknames
    if not t:
        return ''
    if ocr_fixes and t in OCR_FIXES:               # exact lowercase match only
        fixed = OCR_FIXES[t]
        if report is not None:
            report.append('OCR fix: %r -> %r' % (t, fixed))
        return fixed
    return _cap(t)


def clean_person(name, ocr_fixes=True, report=None):
    """Normalise a whole name string (may be multi-token)."""
    n = re.sub(r'"[^"]*"', ' ', name or '')
    n = re.sub(r'\s+', ' ', n).strip(' ,')
    return ' '.join(x for x in (clean_name_token(p, ocr_fixes, report) for p in n.split()) if x)


def is_initial(token):
    return bool(re.fullmatch(r"[A-Za-z]\.?", token.strip()))


def split_full_name(full):
    """Return (first, last). First is always exactly one usable token, never an initial."""
    toks = [t for t in re.sub(r'"[^"]*"', ' ', full or '').replace(',', ' ').split()
            if t.strip('.').lower() not in ('dr', 'mr', 'mrs', 'ms', 'jr', 'sr', 'ii', 'iii')
            and t.strip('.').lower() not in CREDENTIALS]
    if not toks:
        return '', ''
    if len(toks) == 1:
        return toks[0], ''
    i = 0
    while i < len(toks) - 1 and is_initial(toks[i]):
        i += 1                                     # "S. Shanun Kunnavatana" -> first = Shanun
    return toks[i], ' '.join(toks[i + 1:]) or ' '.join(toks[:i]) or ''


def parse_name_field(raw):
    """Split a dirty name cell into (name, credentials, inline_title)."""
    parts = [p.strip() for p in (raw or '').split(',')]
    name, creds, titles = parts[0] if parts else '', [], []
    for p in parts[1:]:
        if not p:
            continue
        low = p.lower()
        if any(w in low for w in TITLE_WORDS):
            titles.append(p)
        else:
            creds.append(p)
    return name, '; '.join(creds), '; '.join(titles)


# --------------------------------------------------------------------- linkedin urls

LI_OK = re.compile(r'^https://www\.linkedin\.com/in/[A-Za-z0-9\-_%\.]+/$')


def normalize_linkedin(url):
    """Canonicalise a LinkedIn profile URL, or return '' if it is not a personal profile."""
    u = (url or '').strip()
    if not u:
        return ''
    u = u.replace('http://', 'https://')
    if not u.startswith('https://'):
        u = 'https://' + u.lstrip('/')
    u = re.sub(r'\?.*$', '', u).rstrip('/')
    u = u.replace('https://linkedin.com', 'https://www.linkedin.com')
    u = re.sub(r'^https://[a-z]{2}\.linkedin\.com', 'https://www.linkedin.com', u)
    if '/in/' not in u:
        return ''                                   # company page, /pub/dir, /jobs -> unusable
    return u + '/'


# --------------------------------------------------------------------------- csv io

def pick(fieldnames, *candidates):
    low = {f.strip().lower(): f for f in fieldnames}
    for c in candidates:
        if c in low:
            return low[c]
    return None


def load(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit('input has no data rows: %s' % path)
    fn = list(rows[0].keys())
    k = {
        'name':  pick(fn, 'name', 'full name'),
        'first': pick(fn, 'first name', 'firstname', 'first'),
        'last':  pick(fn, 'last name', 'lastname', 'last'),
        'co':    pick(fn, 'company', 'organization', 'company name'),
        'title': pick(fn, 'title', 'position'),
        'email': pick(fn, 'email'),
        'li':    pick(fn, 'linkedin url', 'linkedin', 'linkedin profile'),
        'cat':   pick(fn, 'category', 'segment'),
        'pri':   pick(fn, 'priority'),
        'est':   pick(fn, 'email status'),
    }
    if not (k['name'] or (k['first'] and k['last'])):
        raise SystemExit('input needs a "Name" column, or "First Name" + "Last Name"')
    return rows, k


def build(rows, k, ocr_fixes=True):
    out, notes = [], []
    for r in rows:
        if k['first'] or k['last']:
            first_raw, last_raw = r.get(k['first'], ''), r.get(k['last'], '')
            creds = inline = ''
            if not (first_raw or '').strip() and k['name']:
                nm, creds, inline = parse_name_field(r.get(k['name'], ''))
                first_raw, last_raw = split_full_name(nm)
        else:
            nm, creds, inline = parse_name_field(r.get(k['name'], ''))
            first_raw, last_raw = split_full_name(nm)
        first = clean_person(first_raw, ocr_fixes, notes)
        if len(first.split()) > 1:                  # First Name must be one token
            extra = first.split()
            first, last_raw = extra[0], (' '.join(extra[1:]) + ' ' + (last_raw or '')).strip()
        last = clean_person(last_raw, ocr_fixes, notes)
        out.append({
            'LinkedIn URL': normalize_linkedin(r.get(k['li'], '') if k['li'] else ''),
            'Email': (r.get(k['email'], '') or '').strip() if k['email'] else '',
            'First Name': first,
            'Last Name': last,
            'Company': (r.get(k['co'], '') or '').strip() if k['co'] else '',
            'Title': ((r.get(k['title'], '') or '').strip() if k['title'] else '') or inline,
            'Category': (r.get(k['cat'], '') or '').strip() if k['cat'] else '',
            'Priority': (r.get(k['pri'], '') or '').strip() if k['pri'] else '',
            'Email Status': (r.get(k['est'], '') or '').strip() if k['est'] else '',
        })
    return out, notes


def qa(rows):
    """Return a list of human-readable problems. Empty list means the export is clean."""
    problems = []
    withli = [r for r in rows if r['LinkedIn URL']]
    for r in rows:
        who = '%s %s (%s)' % (r['First Name'], r['Last Name'], r['Company'])
        if not r['First Name']:
            problems.append('blank First Name: %s' % who)
        elif len(r['First Name'].split()) > 1:
            problems.append('multi-token First Name %r: %s' % (r['First Name'], who))
        elif r['First Name'].isupper() or r['First Name'].islower():
            problems.append('miscased First Name %r: %s' % (r['First Name'], who))
        elif is_initial(r['First Name']):
            problems.append('First Name is an initial %r: %s' % (r['First Name'], who))
        if r['LinkedIn URL'] and not LI_OK.match(r['LinkedIn URL']):
            problems.append('malformed LinkedIn URL %r: %s' % (r['LinkedIn URL'], who))
        if r['Email'] and '@' not in r['Email']:
            problems.append('malformed email %r: %s' % (r['Email'], who))
        if 'invalid' in (r['Email Status'] or '').lower() and r['Email']:
            problems.append('email marked invalid but still populated: %s' % who)
    for u, n in Counter(r['LinkedIn URL'] for r in withli).items():
        if n > 1:
            problems.append('duplicate LinkedIn URL x%d: %s' % (n, u))
    for e, n in Counter(r['Email'] for r in rows if r['Email']).items():
        if n > 1:
            problems.append('duplicate email x%d: %s' % (n, e))
    return problems


WA_COLS = ['LinkedIn URL', 'Email', 'First Name', 'Last Name', 'Company', 'Title',
           'Category', 'Priority']
NL_COLS = ['Email', 'First Name', 'Last Name', 'Company', 'Title', 'Category', 'Priority',
           'Email Status']


def write(rows, outdir, segment):
    os.makedirs(outdir, exist_ok=True)
    wl = [r for r in rows if r['LinkedIn URL']]
    nl = [r for r in rows if not r['LinkedIn URL']]
    p1 = os.path.join(outdir, 'waalaxy_%s.csv' % segment)
    p2 = os.path.join(outdir, '%s_NO_linkedin_email_only.csv' % segment)
    with open(p1, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=WA_COLS, extrasaction='ignore')
        w.writeheader(); w.writerows(wl)
    with open(p2, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=NL_COLS, extrasaction='ignore')
        w.writeheader(); w.writerows(nl)
    return p1, len(wl), p2, len(nl)


# ------------------------------------------------------------------------- selftest

def selftest():
    a = 0

    def eq(got, want, label):
        nonlocal a
        a += 1
        assert got == want, '%s: got %r want %r' % (label, got, want)

    # name token hygiene -- every one of these was a real defect in a shipped list
    eq(clean_name_token('lan'), 'Ian', 'OCR lowercase l read for capital I')
    eq(clean_name_token('Lan'), 'Lan', 'genuine capitalised Lan is left alone')
    eq(clean_name_token('kristen'), 'Kristen', 'lowercase first name')
    eq(clean_name_token('GUY'), 'Guy', 'ALL CAPS first name')
    eq(clean_name_token('PAIGE'), 'Paige', 'ALL CAPS first name 2')
    eq(clean_name_token('DiNovi'), 'DiNovi', 'intentional inner capital preserved')
    eq(clean_name_token('mcdermott'), 'McDermott', 'Mc prefix')
    eq(clean_name_token("o'brien"), "O'Brien", 'apostrophe prefix')
    eq(clean_name_token('franz-mesick'), 'Franz-Mesick', 'hyphenated')
    eq(clean_person('Paul "Paulie" Gavoni'), 'Paul Gavoni', 'quoted nickname stripped')

    # name splitting
    eq(split_full_name('Julie Adcock'), ('Julie', 'Adcock'), 'plain two-token')
    eq(split_full_name('Miladys Rodriguez Silveira'), ('Miladys', 'Rodriguez Silveira'),
       'two-word surname keeps First Name single-token')
    eq(split_full_name('S. Shanun Kunnavatana'), ('Shanun', 'Kunnavatana'),
       'leading initial skipped so {{firstName}} is not "S."')
    eq(split_full_name('Jay'), ('Jay', ''), 'single token')

    # dirty name cell parsing
    eq(parse_name_field('Julie Adcock, M.S., LBA, BCBA'),
       ('Julie Adcock', 'M.S.; LBA; BCBA', ''), 'credentials separated')
    eq(parse_name_field('Dan Dube, Founder and CEO'),
       ('Dan Dube', '', 'Founder and CEO'), 'inline title harvested')

    # linkedin normalisation
    eq(normalize_linkedin('http://www.linkedin.com/in/isaacbcba'),
       'https://www.linkedin.com/in/isaacbcba/', 'http upgraded, slash added')
    eq(normalize_linkedin('https://www.linkedin.com/in/x/?trk=abc'),
       'https://www.linkedin.com/in/x/', 'tracking query stripped')
    eq(normalize_linkedin('linkedin.com/in/foo'), 'https://www.linkedin.com/in/foo/',
       'bare domain')
    eq(normalize_linkedin('https://uk.linkedin.com/in/bar'), 'https://www.linkedin.com/in/bar/',
       'country subdomain normalised')
    eq(normalize_linkedin('https://www.linkedin.com/company/acme'), '',
       'company page rejected -- not a personal profile')
    eq(normalize_linkedin('https://linkedin.com/pub/dir/Jess/White'), '',
       'directory page rejected')
    eq(normalize_linkedin(''), '', 'empty stays empty')

    # end-to-end: 3 rows, one with no LinkedIn, one with a company page, one clean
    import tempfile
    src = [
        {'Name': 'lan Santus, MS, BCBA', 'Company': 'Akoya', 'Title': 'COO & Co-Founder',
         'Email': 'Ian@akoyabh.com', 'LinkedIn': 'http://linkedin.com/in/ian-santus-b2548010b',
         'Category': 'PROVIDER', 'Priority': 'P1', 'Email Status': 'valid'},
        {'Name': 'Haley Kemp, M.S., BCBA', 'Company': 'Building Blocks',
         'Title': 'Co-Founder', 'Email': '', 'LinkedIn': '',
         'Category': 'PROVIDER', 'Priority': 'P1', 'Email Status': 'no email found'},
        {'Name': 'Jess White', 'Company': 'ABA Tech', 'Title': 'AE', 'Email': 'j@x.com',
         'LinkedIn': 'https://www.linkedin.com/company/aba-tech',
         'Category': 'PROVIDER', 'Priority': 'P2', 'Email Status': 'valid'},
    ]
    d = tempfile.mkdtemp()
    p = os.path.join(d, 'in.csv')
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(src[0].keys())); w.writeheader(); w.writerows(src)
    rows, k = load(p)
    built, notes = build(rows, k)
    eq(built[0]['First Name'], 'Ian', 'end-to-end OCR fix applied')
    eq(built[0]['LinkedIn URL'], 'https://www.linkedin.com/in/ian-santus-b2548010b/',
       'end-to-end URL canonicalised')
    eq(built[2]['LinkedIn URL'], '', 'company page dropped so the row is routed to email-only')
    eq(qa(built), [], 'clean fixture produces no QA problems')
    _, nwl, _, nnl = write(built, d, 'test')
    eq((nwl, nnl), (1, 2), 'split by presence of a usable LinkedIn URL')
    eq(any('OCR fix' in n for n in notes), True, 'OCR fix is reported, not silent')

    # QA must actually catch things
    bad = [{'LinkedIn URL': 'https://www.linkedin.com/in/a/', 'Email': 'x@y.com',
            'First Name': 'GUY', 'Last Name': 'B', 'Company': 'C', 'Title': 'T',
            'Category': '', 'Priority': '', 'Email Status': ''},
           {'LinkedIn URL': 'https://www.linkedin.com/in/a/', 'Email': 'x@y.com',
            'First Name': 'Ann', 'Last Name': 'B', 'Company': 'C', 'Title': 'T',
            'Category': '', 'Priority': '', 'Email Status': ''}]
    probs = qa(bad)
    eq(any('miscased' in p for p in probs), True, 'QA catches miscased first name')
    eq(any('duplicate LinkedIn URL' in p for p in probs), True, 'QA catches duplicate URL')
    eq(any('duplicate email' in p for p in probs), True, 'QA catches duplicate email')

    print('selftest: ALL PASS (%d assertions)' % a)
    return 0


# ----------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description='Build and QA a Waalaxy-ready CSV.')
    ap.add_argument('--selftest', action='store_true', help='run assertions and exit')
    ap.add_argument('--in', dest='inp', help='input CSV of enriched prospects')
    ap.add_argument('--outdir', default='.', help='where to write the CSVs')
    ap.add_argument('--segment', default='prospects', help='used in the output filenames')
    ap.add_argument('--no-ocr-fix', action='store_true', help='disable the lan->Ian style fix')
    ap.add_argument('--strict', action='store_true', help='exit non-zero if QA finds anything')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.inp:
        ap.error('--in is required (or use --selftest)')
    rows, k = load(a.inp)
    built, notes = build(rows, k, ocr_fixes=not a.no_ocr_fix)
    for n in sorted(set(notes)):
        print('  note: %s' % n)
    p1, n1, p2, n2 = write(built, a.outdir, a.segment)
    print('\nwrote %s  %d rows  (Waalaxy-ready, all have a LinkedIn profile)' % (p1, n1))
    print('wrote %s  %d rows  (no LinkedIn -- email or in person)' % (p2, n2))
    print('reconcile: %d + %d = %d == %d input rows -> %s'
          % (n1, n2, n1 + n2, len(rows), n1 + n2 == len(rows)))
    m = Counter((r['Category'], r['Priority']) for r in built if r['LinkedIn URL'])
    if any(c for c, _ in m):
        print('\nWaalaxy-ready by category x priority:')
        for (c, pr), v in sorted(m.items()):
            print('  %-12s %-40s %d' % (c or '-', pr or '-', v))
    probs = qa(built)
    print('\nQA: %s' % ('clean' if not probs else '%d problem(s)' % len(probs)))
    for p in probs:
        print('  - %s' % p)
    return 1 if (probs and a.strict) else 0


if __name__ == '__main__':
    sys.exit(main())
