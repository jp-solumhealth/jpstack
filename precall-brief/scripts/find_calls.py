#!/usr/bin/env python3
"""
Find upcoming intro/discovery calls that need a pre-call brief.

Prints JSON:
  {
    "due":   [ {meeting...} ],   # qualifying calls starting within LEAD_MIN
    "upcoming": [ {meeting...} ],# qualifying calls further out
    "sleep": <seconds>           # how long the loop should wait before re-checking
  }

A call is "due" when it starts within LEAD_MIN minutes and has no brief on disk yet.
Exit code is always 0; errors go to stderr and yield an empty result so the loop
degrades quietly instead of dying.
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

LEAD_MIN = int(os.environ.get("PRECALL_LEAD_MIN", "12"))
HORIZON_DAYS = 10
BRIEF_DIR = os.path.expanduser("~/Documents/Claude/solum-ops/precall-briefs")
KEYS = os.path.expanduser("~/.claude/.api-keys.json")

# Titles that are NOT a first/intro call, checked before the intro patterns.
NOT_INTRO = [
    r"^\s*fup\b", r"\bfollow[- ]?up\b", r"\bmonthly\b", r"\btouchpoint\b",
    r"\bbusiness case\b", r"\binterview\b", r"\bfeedback\b", r"\bsandbox\b",
    r"\bkickoff\b", r"\bonboarding\b", r"\bimplementation\b", r"\bcheck[- ]?in\b",
    r"\bstandup\b", r"\bsync\b", r"\bretro\b", r"\breview\b", r"\bweekly\b",
]
# Titles that positively indicate a first conversation with a new prospect.
IS_INTRO = [
    r"\bass?es?sment call\b",   # tolerates the "Assesment" spelling used on the calendar
    r"\bintro\b", r"\bdiscovery\b", r"\bdemo\b",
    r"\bx solum\b", r"\bsolum health\b",
]
# Deal stages consistent with a first conversation.
EARLY_STAGES = {
    "appointmentscheduled": "Inbound Received",
    "qualifiedtobuy": "Outreach Started",
    "presentationscheduled": "Meeting Booked",
    "1423313650": "Re-engaged Lead",
}
ALL_STAGES = dict(EARLY_STAGES, **{
    "decisionmakerboughtin": "Discovery Completed", "contractsent": "SQL",
    "3363657408": "On Hold", "3249938160": "Pilot Started",
    "closedwon": "Proposal Sent", "1423313647": "Verbal Yes",
    "1423313648": "Closed Won", "closedlost": "Closed Lost",
})
INTERNAL = ("getsolum.com", "gosolum.com", "solumhealth.ai", "gosolum.org",
            "joinsolumhealth.com", "teamsolumhealth.com", "fathom.video")


def hs(path, payload=None, token=None):
    url = f"https://api.hubapi.com{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def classify(title, stage):
    """Return (is_intro, reason). Title is the primary signal, stage corroborates."""
    t = (title or "").lower()
    for p in NOT_INTRO:
        if re.search(p, t):
            return False, f"title matches '{p}'"
    if not any(re.search(p, t) for p in IS_INTRO):
        return False, "no intro/discovery pattern in title"
    if stage and stage not in EARLY_STAGES:
        return False, f"deal already at {ALL_STAGES.get(stage, stage)}"
    return True, "intro/discovery call with a new or early-stage account"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "call").lower()).strip("-")[:60]


def main():
    try:
        token = json.load(open(KEYS))["keys"]["hubspot"]["key"]
    except Exception as e:
        print(json.dumps({"due": [], "upcoming": [], "sleep": 1800,
                          "error": f"no hubspot key: {e}"}))
        return

    now = datetime.now(timezone.utc)
    lo = int(now.timestamp() * 1000)
    hi = int((now + timedelta(days=HORIZON_DAYS)).timestamp() * 1000)

    try:
        res = hs("/crm/v3/objects/meetings/search", {
            "filterGroups": [{"filters": [{
                "propertyName": "hs_meeting_start_time",
                "operator": "BETWEEN", "value": str(lo), "highValue": str(hi)}]}],
            "properties": ["hs_meeting_title", "hs_meeting_start_time",
                           "hs_meeting_end_time", "hs_meeting_external_url",
                           "hs_meeting_location"],
            "sorts": [{"propertyName": "hs_meeting_start_time", "direction": "ASCENDING"}],
            "limit": 50,
        }, token)
    except Exception as e:
        print(json.dumps({"due": [], "upcoming": [], "sleep": 900,
                          "error": f"hubspot meetings failed: {e}"}))
        return

    os.makedirs(BRIEF_DIR, exist_ok=True)
    due, upcoming = [], []

    for r in res.get("results", []):
        p = r["properties"]
        title = p.get("hs_meeting_title") or ""
        start_raw = p.get("hs_meeting_start_time")
        if not start_raw:
            continue
        start = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
        mins = (start - now).total_seconds() / 60.0
        if mins < -5:
            continue

        assoc = {}
        for obj in ("contacts", "companies", "deals"):
            try:
                a = hs(f"/crm/v4/objects/meetings/{r['id']}/associations/{obj}", None, token)
                assoc[obj] = [x["toObjectId"] for x in a.get("results", [])]
            except Exception:
                assoc[obj] = []

        stage = amount = dealname = None
        if assoc["deals"]:
            try:
                d = hs(f"/crm/v3/objects/deals/{assoc['deals'][0]}"
                       "?properties=dealname,dealstage,amount,hs_analytics_source,createdate",
                       None, token)
                dp = d["properties"]
                stage, amount, dealname = dp.get("dealstage"), dp.get("amount"), dp.get("dealname")
            except Exception:
                pass

        is_intro, reason = classify(title, stage)
        if not is_intro:
            continue

        emails, domain = [], None
        for cid in assoc["contacts"]:
            try:
                c = hs(f"/crm/v3/objects/contacts/{cid}"
                       "?properties=email,firstname,lastname,jobtitle,company", None, token)
                em = c["properties"].get("email")
                if em:
                    emails.append(em)
                    dom = em.split("@")[-1].lower()
                    if dom not in INTERNAL and not domain:
                        domain = dom
            except Exception:
                pass

        item = {
            "meeting_id": r["id"], "title": title,
            "start_utc": start.isoformat(), "minutes_away": round(mins, 1),
            "reason": reason, "deal_id": (assoc["deals"] or [None])[0],
            "company_id": (assoc["companies"] or [None])[0],
            "contact_ids": assoc["contacts"], "emails": emails, "domain": domain,
            "deal_name": dealname, "stage": ALL_STAGES.get(stage, stage), "amount": amount,
            "brief_path": os.path.join(
                BRIEF_DIR, f"{start.strftime('%Y-%m-%d')}-{slug(title)}.html"),
        }
        item["already_built"] = os.path.exists(item["brief_path"])

        if mins <= LEAD_MIN and not item["already_built"]:
            due.append(item)
        else:
            upcoming.append(item)

    # Sleep until ~LEAD_MIN before the next qualifying call, clamped to [60s, 1h].
    if due:
        sleep = 60
    elif upcoming:
        nxt = min(u["minutes_away"] for u in upcoming if not u["already_built"]) \
            if any(not u["already_built"] for u in upcoming) else None
        sleep = 3600 if nxt is None else max(60, min(3600, int((nxt - LEAD_MIN) * 60)))
    else:
        sleep = 3600

    print(json.dumps({"due": due, "upcoming": upcoming, "sleep": sleep}, indent=1))


if __name__ == "__main__":
    main()
