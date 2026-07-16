#!/usr/bin/env python3
"""Validate a generated workbook: compute every formula, report error cells.

Usage:  python3 validate_model.py model.xlsx
Requires:  pip install formulas   (pure-Python Excel formula engine)

Exit code 0 = zero formula errors; 1 = errors found (listed); 2 = tooling issue.
A model with ANY #REF!/#NAME?/#DIV/0!/#VALUE! error must not be delivered.
"""
import sys, logging, warnings

ERR_TOKENS = ("#REF!", "#NAME?", "#DIV/0!", "#VALUE!", "#NULL!", "#N/A", "#NUM!")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    try:
        import formulas
    except ImportError:
        print("Missing dependency. Run: pip install formulas")
        return 2
    logging.getLogger("formulas").setLevel(logging.CRITICAL)
    warnings.filterwarnings("ignore")
    try:
        xl = formulas.ExcelModel().loads(path).finish()
        sol = xl.calculate()
    except Exception as ex:
        print(f"Engine could not solve workbook: {str(ex)[:300]}")
        print("Fallback: recalc with LibreOffice (document-skills:xlsx recalc.py) or open in Excel.")
        return 2
    errs = {}
    for k, v in sol.items():
        try:
            val = v.value[0, 0] if hasattr(v, "value") else v
        except Exception:
            val = v
        sval = str(val)
        for e in ERR_TOKENS:
            if e in sval:
                errs.setdefault(e, []).append(k.split("]")[-1])
    if errs:
        for e, locs in errs.items():
            print(f"{e}: {len(locs)} -> {sorted(set(locs))[:10]}")
        return 1
    print("ZERO formula errors across all sheets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
