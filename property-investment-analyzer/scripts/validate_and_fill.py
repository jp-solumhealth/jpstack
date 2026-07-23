#!/usr/bin/env python3
"""Validate an openpyxl-generated workbook AND embed computed values.

Two jobs in one pass:
  1. Compute every formula with the `formulas` engine; report any error cells
     (#REF!/#NAME?/#DIV/0!/#VALUE!). Exit non-zero if found.
  2. Inject each result as a cached <v> value while KEEPING the formula, so the
     file opens populated in Numbers/Excel/Sheets (openpyxl writes empty <v></v>
     which many viewers show blank until a manual recalc). Also sets
     fullCalcOnLoad so the file still recalculates when inputs change.

Usage:  pip install formulas
        python3 validate_and_fill.py workbook.xlsx
Exit: 0 ok · 1 formula errors found · 2 tooling problem
"""
import sys, re, os, zipfile, shutil, logging, warnings
import xml.sax.saxutils as su

ERR=("#REF!","#NAME?","#DIV/0!","#VALUE!","#NULL!","#N/A","#NUM!")

def main():
    if len(sys.argv)!=2: print(__doc__); return 2
    path=sys.argv[1]
    try:
        import formulas
    except ImportError:
        print("Missing dependency. Run: pip install formulas"); return 2
    logging.getLogger("formulas").setLevel(logging.CRITICAL); warnings.filterwarnings("ignore")
    try:
        xl=formulas.ExcelModel().loads(path).finish(); sol=xl.calculate()
    except Exception as ex:
        print(f"Engine could not solve workbook: {str(ex)[:300]}"); return 2

    def scalar(v):
        try: val=v.value
        except Exception: val=v
        if hasattr(val,"ravel"):
            try: val=val.ravel()[0]
            except Exception: pass
        return val

    errs={}; vals={}
    for k,v in sol.items():
        val=scalar(v)
        for e in ERR:
            if e in str(val): errs.setdefault(e,[]).append(k.split("]")[-1])
        after=k.split("]",1)[-1]
        if "!" in after:
            sh,ref=after.rsplit("!",1); sh=sh.strip().strip("'").upper(); ref=ref.replace("$","").strip()
            if re.match(r"^[A-Z]+\d+$",ref): vals.setdefault(sh,{})[ref]=val
    if errs:
        for e,l in errs.items(): print(f"{e}: {len(l)} -> {sorted(set(l))[:10]}")
        return 1

    zin=zipfile.ZipFile(path)
    rels=zin.read("xl/_rels/workbook.xml.rels").decode(); wbx=zin.read("xl/workbook.xml").decode()
    r2t={}
    for m in re.finditer(r"<Relationship\b[^>]*/>",rels):
        t=m.group(0); i=re.search(r'Id="([^"]+)"',t); g=re.search(r'Target="([^"]+)"',t)
        if i and g: r2t[i.group(1)]=os.path.basename(g.group(1))
    n2f={}
    for m in re.finditer(r"<sheet\b[^>]*/?>",wbx):
        t=m.group(0); nm=re.search(r'name="([^"]+)"',t); i=re.search(r'r:id="([^"]+)"',t)
        if nm and i and i.group(1) in r2t: n2f[su.unescape(nm.group(1)).upper()]=r2t[i.group(1)]

    pat=re.compile(r'(<c r="([A-Z]+\d+)")([^>]*)>(<f[^>]*>[^<]*</f>)<v\s*/?>(?:</v>)?</c>')
    def inject(xml,vm,cnt):
        def rep(m):
            oc,ref,at,ft=m.groups()
            val=vm.get(ref)
            if val is None or (isinstance(val,float) and val!=val): return m.group(0)
            if isinstance(val,bool):
                a=at if " t=" in at else at+' t="b"'; vt=f"<v>{1 if val else 0}</v>"
            elif isinstance(val,str):
                if val=="": return m.group(0)
                a=re.sub(r'\st="[^"]*"',"",at)+' t="str"'; vt=f"<v>{su.escape(val)}</v>"
            else:
                try: nu=float(val)
                except Exception: return m.group(0)
                a=re.sub(r'\st="[^"]*"',"",at); vt=f"<v>{int(nu) if nu==int(nu) else round(nu,6)}</v>"
            cnt[0]+=1; return f"{oc}{a}>{ft}{vt}</c>"
        return pat.sub(rep,xml)

    tmp=path+".tmp"; zout=zipfile.ZipFile(tmp,"w",zipfile.ZIP_DEFLATED); cnt=[0]
    for it in zin.infolist():
        d=zin.read(it.filename); fn=it.filename
        if fn.startswith("xl/worksheets/sheet") and fn.endswith(".xml"):
            base=os.path.basename(fn); s=next((n for n,f in n2f.items() if f==base),None)
            if s and s in vals: d=inject(d.decode(),vals[s],cnt).encode()
        if fn=="xl/workbook.xml":
            t=d.decode(); t=re.sub(r"<calcPr[^/]*/>","",t).replace("</workbook>",'<calcPr calcId="124519" fullCalcOnLoad="1"/></workbook>'); d=t.encode()
        zout.writestr(it,d)
    zin.close(); zout.close(); shutil.move(tmp,path)
    print(f"Zero formula errors. Embedded {cnt[0]} cached values (file opens populated, still recalculates).")
    return 0

if __name__=="__main__":
    sys.exit(main())
