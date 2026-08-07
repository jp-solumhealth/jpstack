"""Apply LTV to appraised value to get a suggested max loan amount (COP)."""
from __future__ import annotations


def size(appraised_mid: float | None, ltv: float = 0.60) -> dict:
    if not appraised_mid:
        return {"ltv": ltv, "max_loan_cop": None, "note": "No appraised value"}
    return {"ltv": ltv, "max_loan_cop": appraised_mid * ltv}
