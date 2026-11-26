---
name: rfi-qa
description: Full QA of a client RFI (Request for Information / onboarding sheet) before a client sees it and every time it is checked. ALWAYS run on every RFI, with no exceptions, whenever an RFI is created, copied from a template or another client, pre-filled, edited, sent, shared, or when the user says "check the RFI", "review the RFI", "QA the RFI", "RFI for [client]", "onboarding sheet", "is the RFI ready", or a client replies about their RFI. Guarantees that no other company, organization or NPI appears anywhere in the sheet (cells, dropdowns, notes, formatting rules, hidden rows, version history), verifies every NPI in NPPES, and checks answers, statuses and follow-ups.
---

# RFI QA

Every RFI gets the full QA below. A copy of an RFI made for one client must never show
another client's name, entity, NPI, email or workflow. That is a confidentiality breach,
not a typo. The most common way it happens: a new RFI is made by copying an older client's
sheet, and the **dropdown option lists** (data validation), conditional-format rules and
version history still carry the old client. Those don't show up when you just read the cells.

Run this QA:
- before an RFI is sent or shared with a client (blocking: do not share until it passes),
- every time anyone asks to check, review or update an RFI,
- whenever the client replies about the RFI or edits it,
- after every fix (re-scan until clean).

## Hard rules

1. **No other company or organization anywhere in the sheet.** That includes cell values,
   formulas, notes, links, smart chips, dropdown option lists, conditional-format rules,
   named ranges, protected-range descriptions, filter views, tab names, hidden tabs, rows
   and columns. Payers, clearinghouses, portals and EHR vendors (Medicaid, Aetna, Availity,
   CentralReach...) are expected and allowed. Other providers, other ABA or therapy groups
   and other clients are not.
2. **No NPI that isn't the client's.** Group NPIs must be NPI-2 records whose legal name is one of the
   client's entities. Rendering-provider NPIs must be NPI-1 records whose name matches the
   person on that row. An organization NPI in an individual column, or another company's
   NPI, gets removed and the client is asked for the right one. Never fill in an NPI you
   can't tie to the person or entity without doubt.
3. **Never edit what the client typed** unless it is another company's data (rule 1 or 2).
   Flag the client's typos and gaps and ask. Fix Solum's own text, dropdowns, formulas and
   formatting directly.
4. **New RFIs start from the clean template via File → Make a copy**, never by renaming
   another client's sheet. A copy starts with no version history; a renamed sheet keeps the
   old client's history, and anyone with edit access can open it.
5. **No client data in this repo.** This skill is public. Client names, NPIs, Tax IDs and
   findings stay in the conversation and in the client's sheet.

## Step 1: Find the sheet and its context

- Drive: `search_files` with `title contains 'RFI'` plus the client name. Note the owner,
  who it's shared with, and the last modified time.
- Gmail: search the client's domain for the welcome / RFI thread and **read the whole thread**
  (`get_thread`; search previews only show the oldest messages). Client replies often report
  problems, including screenshots (download and look at them).
- The proposal or deck for the client, if it exists, to know which products, entities and
  states are in scope.

## Step 2: Pull the whole sheet

Don't trust the Drive text preview. It shows sample rows only and no dropdowns.
Call Google Sheets `get_spreadsheet` with `includeGridData: true` and this field mask:

```
properties.title, namedRanges, developerMetadata, sheets.properties, sheets.protectedRanges,
sheets.filterViews, sheets.basicFilter, sheets.conditionalFormats, sheets.developerMetadata,
sheets.data.startRow, sheets.data.startColumn, sheets.data.rowMetadata.hiddenByUser,
sheets.data.columnMetadata.hiddenByUser, sheets.data.rowData.values.userEnteredValue,
sheets.data.rowData.values.formattedValue, sheets.data.rowData.values.note,
sheets.data.rowData.values.hyperlink, sheets.data.rowData.values.dataValidation,
sheets.data.rowData.values.chipRuns, sheets.data.rowData.values.textFormatRuns.format.link
```

The result is usually too large to return inline and gets saved to a file. That file is the input for step 3.

## Step 3: Run the scanner

```
python3 -I <skill dir>/scripts/scan_rfi.py <saved.json> \
  --client "<Client short name>" --client "<Legal entity name>" --domain <clientdomain.com>
```

Add `--allow "<payer or vendor>"` for any legitimate payer or vendor the scanner doesn't know.
Exit code 1 means a hard failure (foreign organization, foreign email domain, NPI that fails
its check digit). Read every flag:

| Flag | What to do |
|---|---|
| FOREIGN_ORG | Remove it now (rule 1). For dropdowns, replace the option list with the client's own entities. |
| FOREIGN_DOMAIN | An email at another company: remove it, or confirm with the user if it's a legitimate vendor. |
| DOMAIN_TYPO | Client typo in its own domain: flag it to the client (invoices and alerts would bounce). |
| NPI | Verify each one in NPPES (step 4). |
| BAD_NPI | Not a valid NPI: ask the client. |
| HIDDEN | Look at it. Hidden content is still shared with the client. |
| STATUS_MISMATCH | Completed with no answer → confirm or set back to Pending. Pending with an answer → review and update. |
| HARDCODED_COUNT | Replace with a formula: `=COUNTIF(B6:B27,"Completed")&" of "&COUNTA(B6:B27)&" completed"` (adjust the range). |
| PLACEHOLDER | Template text left in a data cell: fill it in or ask. |
| HEADERLESS_DV | Dropdown with no header: add the header (for example "PA required?") or remove the dropdown. |
| EMPTY_TAB | Fill it with the open items or hide it. |

The scanner is a floor, not a ceiling. Its organization detection is a heuristic, so also
read every dropdown list and every non-client proper noun yourself.

## Step 4: Verify every NPI in NPPES

For each NPI the scanner lists, run `npi_lookup` and check:
- **Type** matches the column: Group NPI → NPI-2; Individual / Rendering NPI → NPI-1.
- **Name** matches the row: the client's legal entity, or that exact person.
- **Status** is active (A).
- **Taxonomy** fits the service (for ABA: 103K00000X Behavior Analyst, 106E00000X Assistant
  Behavior Analyst, 106S00000X Behavior Technician).
- **License state** covers the state where they'll render services. Flag providers with no
  license on file for that state, and records not updated in years.
- **Sole proprietor = YES** on a rendering provider: confirm they bill under the client's
  group, not their own NPI.
- If an NPI belongs to someone else or to an organization, remove it (rule 2). Use
  `npi_search` by name to find candidates, but only fill one in if it's unambiguous;
  otherwise ask the client.

## Step 5: Read the content end to end

Go row by row on every tab:
- Every question has a sensible answer, or is honestly Pending.
- Answers that conflict with each other or with the proposal (states, entities, payers,
  CPT codes, places of service, EHR).
- Payers mentioned in any answer also appear on the payers tab, with a portal and an
  access status.
- Every rendering provider has a billing entity, a state and their credentialed payers.
- Names and emails spelled the same way everywhere (and the same as in the email thread).
- Solum's own instructions and comments: no typos, no stale promises, no wrong names.
- Dates and deadlines (payer rule changes, go-live) and whether the open items block them.
- Nothing that shouldn't be in a sheet: passwords, PHI or patient documents.

## Step 6: Fix, re-scan, report

1. Fix Solum-side issues and remove anything foreign (rules 1 to 3) in one batch through
   `update_spreadsheet` (`setDataValidation`, `updateCells`).
2. Pull the sheet again (step 2) and re-run the scanner. Repeat until there are no hard failures.
3. If foreign data was ever in a sheet the client can edit, tell the user it is still in
   version history and offer a fresh copy (rule 4) to replace the shared one.
4. Report to the user in this order:
   - **Contamination check:** PASS or FAIL, with exactly what was found and removed.
   - **NPI table:** every NPI with type, name match, status and license notes.
   - **Fixed by Solum:** each change.
   - **Needs the client:** each item, with the cell and the question to ask.
   - **Timing risks:** deadlines and blockers.
   - Link to the sheet.
5. Offer to draft the client reply as a Gmail draft. Never send it without the user's OK.
