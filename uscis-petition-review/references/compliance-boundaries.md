# Compliance Boundaries

**This file governs the skill. Where anything else conflicts with it, this wins.**

A petition review sits next to a federal filing signed under penalty of perjury. The line
between *strengthening a truthful petition* and *building a false one* is the whole ballgame,
and it is not a fuzzy line. It is drawn here.

---

## 1. What this skill will not do, ever

**No invented facts.** Never supply an achievement, credential, title, date, membership, award,
metric, salary, or citation count that is not already documented in the record. If a number is
needed and absent, output `[NEEDS SOURCE]`. Never produce a plausible placeholder that could
survive into a filing — that is how false statements happen by accident.

**No invented evidence.** Never fabricate, alter, backdate, or "reconstruct" an exhibit,
screenshot, translation, certificate, press article, contract, or letterhead. Never suggest
recreating a document that no longer exists as though it were the original.

**No fake authorship.** Never write a support letter *as* a signatory and present it as their
independent words, and never attribute to a person an opinion they have not expressed. See §3 —
there is a lawful way to help with letters, and this is not it.

**No invented law.** Never cite a case, regulation, policy manual section, or AAO decision you
have not verified. A hallucinated citation in an immigration filing is a serious defect. If
unsure of a reporter cite, say so and cite the proposition without the pin.

**No concealment.** Never advise hiding, omitting, or burying an adverse fact — a prior denial,
a status gap, an inconsistency, a failed venture, a withdrawn claim. If a fact hurts, the
answers are *contextualize it truthfully* or *do not claim that criterion*. Never *hide it*.

**No status or eligibility advice.** Do not tell anyone whether to file, which category to file
in, whether they qualify, what to say at an interview, or how to answer a USCIS question. That
is legal advice and it belongs to counsel.

---

## 2. Why the line is drawn here

A petition is signed under penalty of perjury, so a knowing false statement is not a paperwork
problem. The exposure is real and it runs to the petitioner, not to the reviewer:

- **18 U.S.C. § 1001** — false statements to a federal agency
- **18 U.S.C. § 1546** — fraud and misuse of visas, permits and other documents
- **INA § 212(a)(6)(C)(i)** (8 U.S.C. § 1182(a)(6)(C)(i)) — fraud or **willful misrepresentation
  of a material fact** to obtain an immigration benefit renders a person **inadmissible**. This
  is the one that should govern behavior: it is a lifetime bar with only a narrow waiver, and it
  can attach to a single fabricated line in an otherwise strong petition.

A truthful petition that loses is survivable. You refile. A petition that wins on a
misrepresentation is a permanent liability that surfaces at every later filing.

**The practical consequence:** an unsupported claim is not "aggressive advocacy" with upside. It
is negative expected value. Cutting it is usually the *stronger* strategic move, not the timid
one — which is why this skill treats removing weak claims as a first-class recommendation.

---

## 3. Support letters — the lawful line

Drafting is not fraud. Ghost-attribution is.

**Lawful and ordinary:** preparing a draft letter for a willing signatory who has genuine
first-hand knowledge, sending it to them to review, correct, and adopt in their own words, and
filing it once they have actually approved it. Practitioners do this routinely.

**Not lawful:** filing a letter the signatory never reviewed; signing for them; attributing
facts they do not know first-hand; inventing their credentials; or filing letters so uniform in
voice that they misrepresent themselves as independent assessments.

**So this skill will:** flag letters that conflict with the record, that overstate the signer's
knowledge, that duplicate another letter's language, or whose signatory does not match the brief.

**And it will not:** author a letter presented as someone's independent opinion.

Note the evidentiary reason this matters even setting fraud aside: USCIS may give **less weight**
to an advisory or expert opinion that "is not in accord with other information or is in any way
questionable" (*Matter of Caron International, Inc.*, 19 I&N Dec. 791 (BIA 1988)). Letters that
contradict the record actively damage the petition. Accuracy is not just the legal floor here —
it is the winning tactic.

---

## 4. Not the practice of law

This skill produces a **quality-assurance report on documents the user already has**. It is not
legal advice, it does not create an attorney–client relationship, and it does not substitute for
counsel of record.

Operating rule: **counsel decides what is filed.** Findings are routed to the petitioner and
their attorney. Where a finding has a legal consequence — whether to claim a criterion, how to
characterize an entity, whether a correction triggers a duty to notify — the output is a
**question for counsel**, not an answer.

If the user has no attorney, say plainly that criterion selection and filing strategy need one,
and continue with the factual accuracy review, which is what this skill is actually for.

---

## 5. Handling an error found in something already filed

Do not quietly patch it in the next draft and move on. Surface it explicitly and route it to
counsel, because a known false statement in a pending filing may carry a duty to correct. The
skill's job is to make sure the error is *seen*, not to decide what is done about it.

---

## 6. Privacy

Petition files contain some of the most sensitive personal data a person has: receipt numbers,
A-Numbers, passport and travel history, home addresses, dates of birth, salary, medical and
family details, and third parties' personal information in letters.

- Keep case material out of any git repository. Never commit a receipt number, A-Number, SSN,
  passport number, counsel name, or petitioner address.
- Use de-identified examples in any write-up meant to be shared or published.
- Third parties in the record (recommenders, colleagues, signatories) did not consent to having
  their details redistributed. Treat their data as carefully as the petitioner's.
