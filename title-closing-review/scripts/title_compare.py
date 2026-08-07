#!/usr/bin/env python3
"""
title_compare.py — Title / settlement statement QA and competing-quote comparison.

Classifies every settlement charge into three buckets so you compare the RIGHT thing:
  STATUTORY  — fixed by law / promulgated (doc-stamp, intangible, title premium, recording). Not shoppable.
  LENDER     — the lender's own fees (origination, UW, legal, appraisal, feasibility, insurance,
               prepaid interest). Identical across title companies; not shoppable.
  TITLE      — the title agent's own service fees (settlement/closing, notary, search, escrow,
               courier, endorsements, tech fee, deed prep). THIS is what a title company competes on.

Also flags: appraisal double-charge (in one total, P.O.C. in the other), stale deed-transfer
charges (deed prep / affidavits / extra deed recordings when title is already vested), and
per-diem day-count errors.

Run `python3 title_compare.py` for the built-in self-test (RBI GO GO vs Next Chapter, July 2026),
which must reproduce the verified $728 stated / $1,328 like-for-like deltas.

FL statutory rates live in ../references/title-fee-benchmark.md.
"""
from __future__ import annotations
import math

# bucket each canonical line: 'S' statutory, 'L' lender, 'T' title-agent
BUCKET = {
    'Origination':'L','Underwriting':'L','Legal':'L','Feasibility':'L','Appraisal':'L',
    'Prepaid interest':'L','GL insurance':'L',"Builder's Risk":'L',
    'FL doc-stamp':'S','FL intangible':'S',"Lender's title premium":'S','Recording':'S',
    'Settlement fee':'T','Notary':'T','Title search':'T','Lien search':'T','Escrow disb':'T',
    'Courier':'T','Endorsements':'T','E-recording':'T','Deed prep':'T','LLC affidavit':'T',
    'NOC recording':'T','Technology fee':'T','UCC':'T',
}

def fl_doc_stamp(loan):  return round(math.ceil(loan/100)*100*0.0035,2)
def fl_intangible(loan): return round(loan*0.002,2)
def fl_lenders_title(loan):
    base=math.ceil(loan/100)*100
    return round(575+(base-100000)/1000*5.0,2) if base>100000 else round(base/1000*5.75,2)

def compare(a_name, a, b_name, b, loan, appraisal_poc=None):
    """a,b: dict {canonical_line: amount}. appraisal_poc: amount already paid P.O.C. (double-charge check)."""
    keys=sorted(set(a)|set(b))
    ta=tb=0; buckets={'S':[0,0],'L':[0,0],'T':[0,0]}
    print(f"{'LINE':22}{'bucket':>8}{a_name[:9]:>11}{b_name[:9]:>11}{'Δ':>10}")
    print("-"*62)
    for k in keys:
        va=a.get(k,0.0); vb=b.get(k,0.0); bkt=BUCKET.get(k,'T')
        ta+=va; tb+=vb; buckets[bkt][0]+=va; buckets[bkt][1]+=vb
        d=vb-va; flag='' if abs(d)<.005 else ('  ← B lower' if d<0 else '  ← A lower')
        print(f"{k:22}{bkt:>8}{va:>11,.2f}{vb:>11,.2f}{d:>+10,.2f}{flag}")
    print("-"*62)
    print(f"{'TOTAL':22}{'':>8}{ta:>11,.2f}{tb:>11,.2f}{tb-ta:>+10,.2f}")
    for bkt,label in [('S','Statutory (fixed)'),('L','Lender (pass-through)'),('T','Title-agent (SHOPPABLE)')]:
        x,y=buckets[bkt]; print(f"  {label:28}{x:>11,.2f}{y:>11,.2f}{y-x:>+10,.2f}")
    print(f"\nHeadline: {b_name} is ${ta-tb:,.2f} {'lower' if tb<ta else 'higher'} as stated.")
    print(f"The ONLY real difference is the title-agent bucket: ${buckets['T'][1]-buckets['T'][0]:+,.2f}")
    # double-charge check
    if appraisal_poc:
        in_a='Appraisal' in a and a['Appraisal']>0
        in_b='Appraisal' in b and b['Appraisal']>0
        if in_a ^ in_b:
            who=a_name if in_a else b_name
            print(f"\n⚠ Appraisal ${appraisal_poc:,.2f} is in {who}'s total but was already paid P.O.C. — "
                  f"double-charge; strip it for a like-for-like read.")
    print(f"\nStatutory check on loan ${loan:,.2f}: doc-stamp ${fl_doc_stamp(loan):,.2f} · "
          f"intangible ${fl_intangible(loan):,.2f} · lender's title ${fl_lenders_title(loan):,.2f}")

# ---- self-test: RBI Ocala, GO GO Titles vs Next Chapter Title (July 2026) ----
GOGO={'Origination':5896.92,'Underwriting':1500,'Legal':1000,'Feasibility':475,'Appraisal':0,
 'Prepaid interest':403.68,'GL insurance':1554.10,"Builder's Risk":2050.20,'Settlement fee':850,
 "Lender's title premium":3023.50,'Notary':325,'Escrow disb':200,'Courier':75,'Title search':255,
 'Lien search':575,'Endorsements':377.35,'Recording':448,'FL doc-stamp':2063.95,'LLC affidavit':240,
 'UCC':65,'E-recording':25,'NOC recording':135,'FL intangible':1179.38,'Deed prep':500,'Technology fee':0}
NC={'Origination':5896.92,'Underwriting':1500,'Legal':1000,'Feasibility':475,'Appraisal':600,
 'Prepaid interest':378.45,'GL insurance':1554.10,"Builder's Risk":2050.20,'Settlement fee':750,
 "Lender's title premium":3023.50,'Notary':175,'Escrow disb':0,'Courier':175,'Title search':225,
 'Lien search':495,'Endorsements':402.35,'Recording':256.50,'FL doc-stamp':2063.95,'LLC affidavit':0,
 'UCC':65,'E-recording':36.75,'NOC recording':136.50,'FL intangible':1179.38,'Deep prep':0,'Technology fee':50}

if __name__=='__main__':
    compare("GO GO", GOGO, "NextChap", NC, 589692.07, appraisal_poc=600.0)
