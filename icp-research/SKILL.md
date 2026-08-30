---
name: icp-research
description: >
  Derive or challenge an Ideal Customer Profile from evidence rather than assumption, using a
  parallel agent fan-out across internal deal data, external buyer research, and an adversarial
  red team. Use when the user asks who their real customer is, which verticals or segments to
  focus on, who to target, or wants an existing ICP, segment bet, or vertical strategy stress-tested.
  Triggers - "who is our ICP", "define our ICP", "refine the ICP", "which verticals should we focus
  on", "who should we be selling to", "is our ICP right", "which segment should get the budget",
  "who are our best customers", "what do our best customers have in common", "should we go upmarket",
  "challenge our segment strategy", "red team our ICP", "narrow our focus", "who converts best",
  "research our buyer personas", "multiple agents to research our customers".
  Also use before any vertical-focused GTM, content, or outbound plan that assumes an ICP.
---

# ICP Research

Finds who actually buys, pays most, and expands — then attacks that answer before you spend money on it.

## Core principle

**An ICP is derived from who pays and expands, never from who searches.**

The most common way this goes wrong is picking segments on market size, search volume, CPC, or TAM.
Those are channel signals. They measure how many people google a term, not who signs, renews, and
expands. A segment can have enormous search volume and terrible deal economics — and the reverse is
routinely true of the best segments, which are often too small for competitors to bother naming.

**Corollary — the discriminator test:** an attribute shared by won AND lost deals is not an ICP
signal, however often it appears. "They're a healthcare practice" describes every deal in the
pipeline. Only attributes that *separate* won from lost belong in an ICP.

## When to use

- Defining an ICP for the first time, or re-deriving one after the customer base has changed
- Choosing which verticals or segments get the marketing/sales budget
- Stress-testing a segment bet before committing headcount or spend
- Before any vertical-specific GTM, content, or outbound plan
- When a strategy doc picked its segments on market size or keyword volume

**Do not use for:** individual deal qualification (that's a scoring rubric), or persona copy for a
single campaign when the ICP is already settled.

## The fan-out

Three lanes, dispatched **in one message so they run concurrently**. Lanes are independent; agents
inside a lane must be too. One agent per independent domain — never split one question across agents.

### Lane A — Internal evidence (weight this highest)

The only primary evidence of who actually buys. Usually 3 agents:

| Agent | Source | Answers |
|---|---|---|
| Won/lost patterns | CRM | Which attributes discriminate won from lost |
| Buyer language | Call recordings | Who is in the room, verbatim pain, triggers, objections |
| Customer base | Contracts, SOWs, case studies, billing | Revenue and ARPU by segment, land vs expand, real firmographics |

### Lane B — External research (one agent per segment)

Buyer persona, budget authority, firmographics, tech stack, quantified pain, trigger events, where
they gather, competitive landscape. Cap at 3–4 segments; more produces overlap, not insight.

### Lane C — Red team (one `fork` agent)

Use `subagent_type: "fork"` so it inherits full context and needs no re-briefing. Its job is to
attack the recommendation, including the methodology itself.

## Required in every agent prompt

1. **Scope to one domain.** "Research the ABA market" not "research our verticals."
2. **Self-contained context.** Agents inherit nothing (except `fork`). State what the company sells,
   to whom, at what ACV.
3. **The data traps, explicitly.** Agents will produce confidently wrong findings without them.
   See Data traps below.
4. **Fact vs inference separation.** Require the agent to label which is which.
5. **Confidence floors.** "Flag anything based on fewer than 5 records / 3 calls as low confidence."
6. **A negative-space question.** "State explicitly what you could NOT determine and why." This is
   often the highest-value output — it tells you which instrument to build next.
7. **Specific output shape.** Tables and counts, not prose.

## Data traps to brief agents on

Verify these against current state before pasting; they rot.

- **CRM stage IDs lie.** In Solum's HubSpot the internal ID `closedwon` maps to a stage labeled
  "Proposal Sent" and is an OPEN stage. Require agents to resolve IDs to labels and report the mapping.
- **CRM data is sparse.** ~79% of Solum deals carry no amount, ~67% no close date. Require the
  denominator and the count of unusable records, or win rates will be silently computed on a
  biased subset.
- **The CRM undercounts customers.** Several signed accounts have no deal record at all. Agents must
  never claim a CRM pull is the complete customer list.
- **Never quote ARR from the CRM.** Reconcile from billing.
- **Meeting source is Fathom, not Fireflies.**
- **Proposals are not revenue.** Require agents to label drafts and proposals as such.

## Red team assignments that actually find things

Generic "critique this" produces flattery. Name the specific attack:

- **Methodology:** does the recommendation survive if you delete the selection criterion entirely?
- **Internal contradiction:** find two recommendations in the doc that conflict.
- **Evidence asymmetry:** is a focus segment justified by demonstrated wins, or by assumed pain?
- **Sample size:** is the customer base large enough to support a segment strategy at all?
- **Second-order effects:** what breaks operationally if focus narrows?
- **Strongest counter-thesis:** argue for a completely different ICP axis — a single vertical, a
  workflow-defined ICP ("anyone with high auth volume"), or a tech-stack-defined ICP ("every
  practice on this EHR"). Tech-stack ICPs are frequently stronger than vertical ICPs because they
  are checkable from outside and map directly to outbound segmentation.

## Synthesis

Do not concatenate agent reports. Resolve them:

1. **Contradictions first.** Where internal and external disagree, internal wins — external research
   describes a market, internal describes your customers. Say which you chose and why.
2. **Apply the discriminator test** to every proposed attribute.
3. **Re-rank segments on deal economics** (ARPU, expansion rate, cycle length, win rate), then note
   separately where channel reach happens to align.
4. **Adjudicate the red team.** State plainly what survived and what changed. A red team that
   changed nothing was either wrong or not given a real assignment.
5. **Name the cheapest decisive experiment** for the biggest remaining open question.

## Output

A revised ICP section with: the discriminating attributes and their evidence; segments ranked on
deal economics; the buyer (title, budget authority, trigger events) per segment; verbatim buyer
language; what was rejected and why; open questions with the experiment that would settle each.

Per house rules, write it to a file in the relevant project folder and report the path plus a
`file://` URL. Never dump a full ICP analysis inline in chat.

## Common mistakes

| Mistake | Why it fails |
|---|---|
| Picking segments on search volume or TAM | Channel signal, not buying signal — the error this skill exists to prevent |
| Listing attributes common to all customers | Fails the discriminator test; describes the market, not the ICP |
| Fanning out one question across many agents | Produces duplicate work and contradictions on the overlap |
| Omitting data traps from prompts | Agents produce confident, wrong findings from misleading CRM fields |
| External research weighted equally with internal | Describes a market you don't sell to yet |
| Red team with a vague assignment | Returns agreement dressed as critique |
| Treating agent output as fact | Agents make systematic errors; spot-check every load-bearing number |
| Vertical ICP where a tech-stack ICP is stronger | Verticals are hard to verify from outside; EHR/platform is checkable and targetable |

## Status

Technique skill, derived from the Solum Health growth audit (Aug 2026). Structure and data traps are
from a real run. **Not yet baseline-tested against a no-skill control** — pressure-test before
relying on it to change behavior under time pressure.
