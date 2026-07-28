---
name: client-welcome-email
description: >
  Draft the welcome / intro / next-steps email a new Solum Health client receives
  right after signing. Use when the user says "welcome email for [name]", "intro
  email for [client]", "[client] just signed", "kickoff email", "onboarding email",
  or dictates additions/corrections to a welcome draft already in progress
  (dictation is often garbled — see Dictation handling). Also triggers on "next
  steps email for [new client]" or a signed-agreement notification that needs a
  client-facing reply.
---

# Client Welcome Email

## Overview

The deliverable is ONE plain-text email, built only from verified agreements. Anything uncertain becomes a flag to JP under the draft — never content inside the email, and never a blocking question.

**Core principle: the email contains only what was actually agreed or dictated. If you didn't see it in a source or in JP's words, it doesn't go in the email.**

## Step 1 — Gather context (before drafting)

1. Memory: check `MEMORY.md` / project memories for the deal.
2. Client folder: `~/Documents/Claude/solum-ops/clients/<client-name>/` (SOPs, call notes).
3. If still thin: Fathom recording link in notes, HubSpot deal.

From these, extract: contact first name, what they signed up for, their urgency/situation, who owns implementation, what was promised (timeline, access, call times), and how pricing is structured (fixed vs usage-based).

## Step 2 — The email (this shape, in this order)

1. **Subject**: short and plain. "Welcome to Solum — next steps" works.
2. **Open**: confirm the signed agreement came through + one warm line tied to their specific situation.
3. **Numbered next steps** — only steps that were actually agreed or dictated. Typical slots:
   - Data request they should expect, and what happens once it's back (timeline).
   - System access ask (e.g., an EMR login for Solum), with the one-line reason it matters to them.
   - First workload priority (e.g., clearing the backlog first).
   - Intro call invite naming the implementation lead, with the proposed time only if JP gave one.
4. **Billing clarification** — include only when pricing has usage-based components: the monthly minimum is the only fixed piece; services they don't use are never billed. Name the services JP named. No dollar figures, ever — "as we discussed" replaces numbers.
5. **Close**: open-channel line ("just reply here or call me directly"), a thanks-for-the-trust line using their first name, sign "JP".

## Step 3 — Deliver

- Email as plain text ready to copy-paste: no code blocks, no bold section labels, no markdown, no em-dashes.
- Under the email, a short "flags" note: each interpretation call or assumption you made, one line each, with what to say if JP meant something else.

## Dictation handling

JP dictates additions across several messages and transcription garbles terms ("RFE" for a data request; "There's no availability for a call" when the next line offers a time — meaning "Is there any availability"). Restate your reading of the dictation in one sentence before the revised draft, pick the most sensible interpretation, and put the call you made in the flags note. A garbled service name you can't map to the deal ("product research") gets your best mapping plus a flag — never a literal copy into the email.

## Hard limits

The deliverable is the email plus flags. Internal action plans, HubSpot updates, team to-dos, and follow-on offers are out of scope unless JP asks. Invented specifics — meeting lengths, "you have my cell", times JP never gave — don't go in; leave the slot out or flag it.

## Example (condensed, from the TruWell close)

Subject: Welcome to Solum — next steps

Hi Brian,

Just saw the signed agreement come through. Welcome to Solum, we're excited to get you back up and running.

1. Data request. You'll get a short request from us with everything we need for setup. Once we have it back, we'll run the setup over the weekend so you're live next week.

2. Prompt access. Could you create a Prompt user login for Solum, same as Spike had? That's how results show up inside each patient's profile without your team re-entering anything.

3. Quick intro call. Do you and Jessa have availability tomorrow? Santiago will be leading the implementation. 11:00 AM Eastern works well on our side if it works for you.

One thing on billing: as we discussed, the only fixed piece is the monthly minimum. If you don't use prior auth or referral automation in a given month, you won't be charged anything on that side.

Anything you need in the meantime, just reply here or call me directly.

Thanks for trusting us with this, Brian.

JP
