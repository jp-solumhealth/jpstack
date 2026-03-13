# Skill: Fact-Check

Automatically verify numerical claims, data-driven statements, and factual assertions in documents before they are finalized.

## When to Activate

This skill MUST be invoked when any of the following conditions are met:

- The user explicitly asks to "fact-check", "verify data", "validate claims", or similar
- A document, report, or presentation containing numerical claims is about to be finalized
- The user asks to "finalize", "publish", or "send" a document that includes data-driven statements
- A report has been generated from source data and is being reviewed

## Definitions

**Numerical claim**: Any statement containing a number, percentage, count, dollar amount, ratio, date-based statistic, or quantitative comparison (e.g., "revenue grew 34%", "we processed 1,200 claims", "average turnaround is 3.2 days").

**Factual statement**: Any assertion presented as fact that can be checked against source data (e.g., "our largest client is X", "the most common denial reason is Y").

**Source data**: The original dataset from which claims are derived. This may be a database (via SQL), CSV files, JSON files, Excel/Google Sheets, API responses, or any structured data the user can point to.

## Verification Process

Follow these steps in order. Do NOT skip any step.

### Step 1: Read the Document

Read the full document or report content. If the document is being generated in-session, capture all text that will be included in the final output.

### Step 2: Extract All Claims

Systematically go through the document and extract every:
- Numerical value (counts, amounts, durations, dates)
- Percentage or ratio
- Comparative statement ("increased by", "more than", "largest", "fastest")
- Aggregate or summary statistic (averages, totals, medians)
- Factual assertion that can be validated against data

Create a numbered list of every claim found. Do not skip claims that seem obviously correct -- verify everything.

### Step 3: Identify Source Data

Determine where the source data lives. Check for:
- Files referenced in the conversation (CSV, JSON, XLSX, etc.)
- Database connections (Supabase, PostgreSQL, etc.)
- API endpoints that were queried
- Google Sheets or other cloud data sources

If the source data is unclear, ASK the user before proceeding. Do not guess.

### Step 4: Write and Run Verification Scripts

For each claim, write and execute a verification script (Python or Node.js) that:
- Queries or reads the source data
- Computes the correct value independently
- Compares the claimed value against the computed value
- Calculates the percentage deviation

Use the Bash tool to run these scripts. Prefer Python with pandas for CSV/data analysis. For database queries, use the appropriate MCP tools (e.g., Supabase execute_sql).

### Step 5: Classify Each Claim

Assign one of these statuses to every claim:

| Status | Criteria | Action |
|--------|----------|--------|
| CONFIRMED | Exact match or deviation <= 5% | No action needed |
| CLOSE | Deviation between 5% and 15% | Flag for user review; recommend correction |
| WRONG | Deviation > 15% or factually incorrect | Must be corrected before finalizing |
| CANNOT VERIFY | No source data available or accessible | Explicitly note in document or remove claim |

### Step 6: Check Internal Consistency

Beyond individual claim verification, check for:
- **Totals**: Do sub-items add up to the stated total?
- **Percentages**: Do percentage breakdowns sum to 100% (or close)?
- **Contradictions**: Does any claim contradict another claim in the same document?
- **Methodology alignment**: Does the described methodology match how the numbers were actually computed?
- **Time period consistency**: Are all claims referring to the same time period when compared?

Flag any inconsistencies found.

### Step 7: Present the Fact-Check Report

Present findings in a clear table format:

```
## Fact-Check Report

Document: [document name/description]
Source data: [source files/databases used]
Claims verified: [count]

| # | Claim | Claimed Value | Verified Value | Deviation | Status |
|---|-------|---------------|----------------|-----------|--------|
| 1 | ...   | ...           | ...            | ...       | ...    |

### Internal Consistency Checks
- [List any inconsistencies found, or "All consistency checks passed"]

### Recommended Corrections
- [Specific corrections for WRONG and CLOSE claims]

### Unverifiable Claims
- [List claims marked CANNOT VERIFY with recommendation to source or remove]
```

### Step 8: Apply Corrections and Re-verify

If any claims are WRONG or CLOSE:
1. Recommend the exact corrected text to the user
2. Wait for user approval before making changes
3. After corrections are applied, re-run verification on changed values to confirm

### Step 9: Finalize Only After Verification

Only proceed with finalizing the document (saving, sending, publishing) AFTER:
- All claims are CONFIRMED or user-approved
- All internal consistency checks pass
- The user has acknowledged any CANNOT VERIFY claims

## Important Rules

1. **NEVER skip fact-checking** when generating or finalizing reports that contain data claims. This is a blocking requirement.
2. **Always show verification results** to the user before finalizing. Never silently pass a document through.
3. **Verify round numbers too**. A claim of "approximately 1,000" should still be checked -- the actual value might be 800 or 1,300.
4. **Check the math, not just the data**. If a document says "34% of 500 is 180", verify both the percentage AND the arithmetic.
5. **Preserve precision context**. If source data shows 33.7%, and the document says "about 34%", that is CONFIRMED. But if source data shows 28.1% and the document says "about 34%", that is WRONG.
6. **Document the verification**. The fact-check report should be included or referenced so the user has an audit trail.
7. **When in doubt, flag it**. It is better to flag a correct claim for review than to let an incorrect claim pass.
8. **Cross-reference multiple sources** when available. If two data sources disagree, flag the discrepancy.

## Example Invocations

- `/fact-check` -- Run fact-check on the current document or most recent report
- "Verify the data in this report before we send it"
- "Fact-check these numbers against the database"
- "Can you validate the claims in this investor update?"
- Automatically triggered when a report with data claims is about to be finalized
