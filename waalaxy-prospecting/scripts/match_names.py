#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recover LinkedIn URLs and emails for a prospect list by fuzzy-matching it against enrichment
CSVs you already have. Free: no API calls.

Two things this does that an exact join does not:

  1. Survives spelling damage. A list read by OCR contained "lan Santus" for "Ian Santus"
     (lowercase L for capital I). An exact match loses the join, the contact looks brand new,
     and an already-verified email gets re-bought or missed.
  2. Refuses cross-company emails. A prior file may hold the same person at a former employer.
     Reusing that address mails the wrong company, so the email domain is checked against the
     company on the current list; on a mismatch the LinkedIn URL is still taken but the email
     is only flagged.

    python3 match_names.py --selftest
    python3 match_names.py --target list.csv --sources "project/**/*.csv" --out filled.csv
"""
import argparse, csv, difflib, glob, os, re, sys, unicodedata

STOP = {'dr', 'mr', 'mrs', 'ms', 'jr', 'sr', 'ii', 'iii', 'md', 'phd'}
CREDS = {'ms', 'ma', 'med', 'mba', 'phd', 'edd', 'dbh', 'psyd', 'jd', 'bcba', 'bcbad', 'bcaba',
         'lba', 'laba', 'iba', 'rbt', 'cccslp', 'lmft', 'lcsw', 'cphq', 'qba', 'coba'}


def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    return ' '.join(re.sub(r'[^a-z ]', ' ', s.lower()).split())


def toks(name):
    out = []
    for t in norm(name).split():
        if t in STOP or t in CREDS or len(t) < 2:
            continue
        out.append(t)
    return out


def ed1(a, b):
    """True if a and b are equal or one edit apart. Catches lan/ian, jon/john, ann/anne."""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    short, long = (a, b) if len(a) < len(b) else (b, a)
    return any(long[:i] + long[i + 1:] == short for i in range(len(long)))


def first_matches(cand, want):
    """Fuzzy first-name comparison, deliberately generous but anchored on the surname."""
    if not cand or not want:
        return False
    return (cand == want or ed1(cand, want)
            or difflib.SequenceMatcher(None, cand, want).ratio() >= 0.8
            or cand.startswith(want[:4]) or want.startswith(cand[:4]))


def domain_matches_company(email, company):
    """True when the email's domain plausibly belongs to the company on the current list."""
    if not email or '@' not in email or not company:
        return False
    host = email.split('@', 1)[1].lower()
    stem = host.split('.')[0]
    words = [w for w in norm(company).split()
             if len(w) > 2 and w not in ('the', 'llc', 'inc', 'group', 'services', 'center',
                                         'centers', 'health', 'therapy', 'company')]
    if any(w in stem for w in words):
        return True
    initials = ''.join(w[0] for w in norm(company).split() if w)
    return len(initials) >= 3 and initials[:4] in stem


def pick(fieldnames, *cands):
    low = {f.strip().lower(): f for f in fieldnames}
    for c in cands:
        if c in low:
            return low[c]
    return None


def read_sources(patterns):
    """Pool every (name, linkedin, email) record found across the given CSV globs."""
    pool, files = [], []
    for pat in patterns:
        files.extend(sorted(glob.glob(pat, recursive=True)))
    for path in files:
        try:
            with open(path, newline='', encoding='utf-8-sig') as f:
                rows = list(csv.DictReader(f))
        except Exception:
            continue
        if not rows:
            continue
        fn = list(rows[0].keys())
        kf, kl = pick(fn, 'first name', 'firstname'), pick(fn, 'last name', 'lastname')
        kn = pick(fn, 'name', 'full name')
        kli = pick(fn, 'linkedin url', 'linkedin', 'linkedin profile')
        ke, kc = pick(fn, 'email'), pick(fn, 'company', 'company name', 'organization')
        if not (kli or ke):
            continue                      # nothing worth harvesting
        for r in rows:
            t = toks(' '.join(x for x in [r.get(kf, ''), r.get(kl, '')] if x) or r.get(kn, ''))
            if len(t) < 2:
                continue
            pool.append({'first': t[0], 'last': t[-1],
                         'li': (r.get(kli, '') or '').strip() if kli else '',
                         'email': (r.get(ke, '') or '').strip() if ke else '',
                         'company': (r.get(kc, '') or '').strip() if kc else '',
                         'src': os.path.basename(path)})
    return pool, files


def best_match(pool_by_last, first, last):
    best = None
    for c in pool_by_last.get(last, []):
        if not first_matches(c['first'], first):
            continue
        rank = (bool(c['li']), bool(c['email']))
        if best is None or rank > (bool(best['li']), bool(best['email'])):
            best = c
    return best


def fill(target_rows, pool):
    by_last = {}
    for p in pool:
        by_last.setdefault(p['last'], []).append(p)
    fn = list(target_rows[0].keys())
    kli = pick(fn, 'linkedin url', 'linkedin', 'linkedin profile')
    ke = pick(fn, 'email')
    kc = pick(fn, 'company', 'company name', 'organization')
    kf, kl = pick(fn, 'first name', 'firstname'), pick(fn, 'last name', 'lastname')
    kn = pick(fn, 'name', 'full name')
    gained, flagged = [], []
    for r in target_rows:
        t = toks(' '.join(x for x in [r.get(kf, ''), r.get(kl, '')] if x) or r.get(kn, ''))
        if len(t) < 2:
            continue
        m = best_match(by_last, t[0], t[-1])
        if not m:
            continue
        who = '%s %s' % (r.get(kf) and r[kf] or t[0], r.get(kl) and r[kl] or t[-1])
        got = []
        if kli and not (r.get(kli) or '').strip() and m['li']:
            r[kli] = m['li']; got.append('LinkedIn')
        if ke and not (r.get(ke) or '').strip() and m['email']:
            company = (r.get(kc) or '') if kc else ''
            if domain_matches_company(m['email'], company):
                r[ke] = m['email']; got.append('email')
            else:
                flagged.append((who, company, m['email'], m['src']))
        if got:
            gained.append((who, '+'.join(got), m['src']))
    return gained, flagged


def selftest():
    a = 0

    def eq(got, want, label):
        nonlocal a
        a += 1
        assert got == want, '%s: got %r want %r' % (label, got, want)

    eq(ed1('lan', 'ian'), True, 'the real OCR case: lan vs ian')
    eq(ed1('jon', 'john'), True, 'insertion')
    eq(ed1('ann', 'anne'), True, 'trailing insertion')
    eq(ed1('mark', 'jane'), False, 'unrelated names are not one edit apart')
    eq(ed1('lee', 'lee'), True, 'identical')
    eq(first_matches('ian', 'lan'), True, 'fuzzy first name accepts the OCR variant')
    eq(first_matches('kathryn', 'katharine'), True, 'prefix variant')
    eq(first_matches('robert', 'jennifer'), False, 'clearly different names rejected')

    eq(domain_matches_company('t.yeager@centriahealthcare.com', 'Centria Autism'), True,
       'company word appears in the domain')
    eq(domain_matches_company('r@centerforaba.com', 'Center for Applied Behavior Analysis'), True,
       'multi-word company matched on a shared word')
    # An acronym on the list cannot be tied to a spelled-out domain by string matching alone:
    # "BDA" vs brettdassociates.com needs the knowledge that BDA = Brett DiNovi & Associates.
    # Staying conservative is correct -- the email is FLAGGED for a human, never silently used
    # and never silently dropped.
    eq(domain_matches_company('isaac@brettdassociates.com', 'BDA'), False,
       'acronym company is not auto-validated; it gets flagged for review')
    eq(domain_matches_company('nathan@juniperplatform.com', 'Camber Health'), False,
       'former-employer domain refused')
    eq(domain_matches_company('melissa@gatewayaba.com', 'The Light'), False,
       'unrelated domain refused')
    eq(domain_matches_company('', 'Acme'), False, 'empty email')

    eq(toks('lan Santus, MS, BCBA'), ['lan', 'santus'], 'credentials stripped from tokens')
    eq(toks('Dr. Ally Dube'), ['ally', 'dube'], 'honorific stripped')

    # end to end
    import tempfile
    d = tempfile.mkdtemp()
    srcp = os.path.join(d, 'prior.csv')
    with open(srcp, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['First Name', 'Last Name', 'Company', 'LinkedIn URL',
                                          'Email'])
        w.writeheader()
        w.writerows([
            {'First Name': 'Ian', 'Last Name': 'Santus', 'Company': 'Akoya Behavioral Health',
             'LinkedIn URL': 'https://www.linkedin.com/in/ian-santus/',
             'Email': 'Ian@akoyabh.com'},
            {'First Name': 'Nathan', 'Last Name': 'Lee', 'Company': 'Juniper',
             'LinkedIn URL': 'https://www.linkedin.com/in/nathanlee-145/',
             'Email': 'nathan@juniperplatform.com'},
        ])
    target = [
        {'First Name': 'lan', 'Last Name': 'Santus', 'Company': 'Akoya Behavioral Health',
         'LinkedIn URL': '', 'Email': ''},
        {'First Name': 'Nathan', 'Last Name': 'Lee', 'Company': 'Camber Health',
         'LinkedIn URL': '', 'Email': ''},
    ]
    pool, files = read_sources([os.path.join(d, '*.csv')])
    eq(len(files), 1, 'source file discovered')
    gained, flagged = fill(target, pool)
    eq(target[0]['Email'], 'Ian@akoyabh.com',
       'OCR-damaged row recovered its email despite the misspelling')
    eq(target[0]['LinkedIn URL'], 'https://www.linkedin.com/in/ian-santus/',
       'and its LinkedIn URL')
    eq(target[1]['LinkedIn URL'], 'https://www.linkedin.com/in/nathanlee-145/',
       'LinkedIn still taken for the changed-employer row')
    eq(target[1]['Email'], '', 'but the former-employer email was NOT written')
    eq(len(flagged), 1, 'the refused email is reported, not dropped in silence')

    print('selftest: ALL PASS (%d assertions)' % a)
    return 0


def main():
    ap = argparse.ArgumentParser(description='Backfill LinkedIn/email from prior CSVs.')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--target', help='CSV to enrich in place (written to --out)')
    ap.add_argument('--sources', nargs='+', default=[],
                    help='glob(s) of prior enrichment CSVs, e.g. "proj/**/*.csv"')
    ap.add_argument('--out', help='where to write the filled CSV')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.target and a.sources and a.out):
        ap.error('--target, --sources and --out are required (or use --selftest)')
    with open(a.target, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit('target has no rows')
    pool, files = read_sources(a.sources)
    print('pooled %d prior records from %d files' % (len(pool), len(files)))
    gained, flagged = fill(rows, pool)
    print('\nrows improved: %d' % len(gained))
    for who, what, src in gained:
        print('  %-28s +%-16s (from %s)' % (who[:26], what, src))
    print('\ncross-company emails refused: %d' % len(flagged))
    for who, company, email, src in flagged:
        print('  %-24s listed at %-22s -> %-34s (%s) domain does not match company'
              % (who[:22], company[:20], email, src))
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print('\nwrote %s (%d rows)' % (a.out, len(rows)))
    print('NOTE: any newly added email is unverified. Run it through the verifier before use.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
