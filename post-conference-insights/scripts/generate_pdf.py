#!/usr/bin/env python3
"""
Solum Health Industry Insights — Branded One-Pager Generator

This is a TEMPLATE. To use for a new conference:
1. Copy this file to a working directory
2. Modify the CONTENT section (title, subtitle, event_details, stats, sections, role_cards, closing_message)
3. Run: python generate_pdf.py

The layout, branding, and styling should NOT change between conferences.
Only the content variables should be modified.

Requirements:
  pip install fpdf2
"""

from fpdf import FPDF
import os
import sys

# ─── PALETTE (do not change) ───
NAVY         = (14, 28, 54)
NAVY_MID     = (27, 58, 92)
TERRACOTTA   = (189, 82, 55)
TEAL         = (38, 118, 136)
TEXT_HEAD     = (14, 28, 54)
TEXT_BODY     = (60, 68, 82)
TEXT_LIGHT    = (130, 142, 158)
WHITE         = (255, 255, 255)
BG_CARD       = (241, 244, 248)
BG_WARM       = (248, 245, 241)
BORDER        = (214, 221, 229)

# ─── PATHS ───
# Logo: check skill assets first, then home directory
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATHS = [
    os.path.join(SKILL_DIR, 'assets', 'solum_logo.png'),
    os.path.expanduser('~/solum_logo.png'),
]
LOGO = None
for p in LOGO_PATHS:
    if os.path.exists(p):
        LOGO = p
        break
if LOGO is None:
    print("ERROR: solum_logo.png not found. Expected at:")
    for p in LOGO_PATHS:
        print(f"  {p}")
    sys.exit(1)

# macOS system fonts
FD = '/System/Library/Fonts/Supplemental'
M = 18  # margin


# ═══════════════════════════════════════════════════════
# CONTENT — Modify this section for each new conference
# ═══════════════════════════════════════════════════════

TITLE = 'BHASe 2026: What We Took Away'
SUBTITLE = "Three days with the operators, investors, and decision makers shaping behavioral health."
EVENT_DETAILS = 'BHASe Summit  |  Feb 11-13, 2026  |  Miami, FL'

# 4 stat cards: (number, line1, line2, color)
# Colors: TERRACOTTA, TEAL, NAVY_MID
STATS = [
    ('10-20%', 'Revenue lost to', 'preventable denials', TERRACOTTA),
    ('70%', 'Doc time cut with', 'AI-assisted notes', TEAL),
    ('90%', 'Patients lost in', 'manual intake', NAVY_MID),
    ('51%', 'Denials tagged', '"non-medical necessity"', TERRACOTTA),
]

# Insight sections for page 1
# Each entry: (title, content_type, content)
# content_type: 'para' for paragraph, 'bullets' for bulleted list
# For 'para': content is a string
# For 'bullets': content is a list of (bold_prefix, rest_of_text)
SECTIONS = [
    ('The Big Shift: From Growth to Proof', 'para',
     "The industry is done rewarding scale for scale's sake. Payers, investors, and "
     "regulators all want proof: outcomes data, clean financials, defensible margins. "
     "74% of healthcare buyers now deselect vendors who can't show in-year financial "
     "impact. If you can't produce a denial rate by payer or an outcome report on "
     "demand, you're weaker in every negotiation you walk into."),

    ("AI That's Actually Working Right Now", 'bullets', [
        ('Revenue cycle:', "AI claims scrubbing cuts denial rates up to 30%. For a 20-clinician practice, that's $60K+ per year recovered."),
        ('Documentation:', "Ambient AI notes reduce doc time 50-70%. One system saw burnout drop from 52% to 39% in 30 days."),
        ('Intake:', "Practices automating intake saw bookings double or quadruple. Most providers lose patients to phone tag before visit one."),
        ('Denial management:', "Teams spending 50-75 hrs/week on denials cut that with AI that learns patterns and auto-generates appeals."),
    ]),

    ('Payers Have Already Automated. Have You?', 'para',
     "Payers have invested heavily in AI-driven denial engines. They're running automated "
     "medical-necessity reviews and flagging documentation gaps your team doesn't know exist. "
     "One operator described a spike in denials after a payer updated their algorithm over a "
     "weekend. Forty hands went up with the same story. You can't bring a manual process to "
     "an AI-powered fight."),

    ('Revenue Cycle = Strategic Asset', 'para',
     "A practice doing $5M with 95% clean claims is more attractive than one doing $8M with "
     "a 15% denial rate (that's ~$1.2M in first-pass rejections). For M&A, denial rates and "
     "days in A/R are now due diligence items. Automate the routine 80% so your best people "
     "handle the complex 20%."),

    ("Workforce: You Can't Hire Your Way Out", 'para',
     "Burnout sits above 50% among providers using traditional documentation. The conversation "
     "shifted from \"we can't find people\" to \"how do we keep the ones we have?\" Reduce "
     "their burden with automation. Nobody's getting replaced. Each person's time becomes worth more."),

    ('Specialization Wins. Consolidation Accelerates.', 'para',
     "Specialized SUD programs with MAT are negotiating 25-40% higher rates from the same "
     "payers because they have outcome data on relapse and ER visits. M&A in behavioral health "
     "(especially ABA) is accelerating. Clean books and mature billing ops give you options."),
]

# Optional intro text above bullets sections (used after section title if content_type is 'bullets')
SECTION_INTROS = {
    "AI That's Actually Working Right Now": "Not everything labeled AI is delivering yet. But four areas are producing real, measurable results:",
}

# Role-based action cards for page 2
# Each: (title, [list of action items], color)
# Left column cards listed first, then right column
ROLE_CARDS_LEFT = [
    ('BILLING TEAM', [
        "Pull denial reports by payer for 90 days. Sort by reason code. Top 3 reasons hold 80% of your recoverable revenue. Fix those first.",
        "Map every auth renewal deadline for your highest-volume payer. If you're tracking on spreadsheets, that's automation target #1.",
        "Scrub audit last month's claims: missing modifiers, wrong POS codes, expired auths. That number is your baseline.",
    ], TERRACOTTA),
    ('FRONT DESK / INTAKE', [
        "Track voicemail calls this week. Then track callbacks. The gap = patients you're losing. Put a number on it.",
        "Time first-call-to-first-appointment. Over 48 hours? The 24-to-72 hour drop-off is steep.",
        "List the 3 most repetitive daily tasks (eligibility, confirmations, paperwork). Those are your automation candidates.",
    ], TEAL),
]

ROLE_CARDS_RIGHT = [
    ('CLINICAL DIRECTORS', [
        "Survey clinicians: hours/week on documentation outside sessions? Above 5 = a documentation problem, not morale.",
        "Pick one outcome measure (PHQ-9 or GAD-7). Collect at intake + every 30 days. A spreadsheet works for now.",
        "Talk to your team about AI doc tools. Not to buy. To understand concerns. The best rollouts started by listening.",
    ], NAVY_MID),
    ('OWNERS & OPERATORS', [
        "Block 2 hours on the A/R aging report with your billing manager. You'll rethink at least one payer relationship.",
        "Ask your EHR vendor what automations you're not using. Most practices use 40-60% of what they already pay for.",
        "Start a 3-metric dashboard: denial rate, doc turnaround, no-show rate. Review weekly. That discipline changes everything.",
    ], TERRACOTTA),
]

PAGE2_TITLE = 'What Your Team Can Do Monday Morning'
PAGE2_SUBTITLE = "Page one was strategy. This page is action. Print it, send it to your leads, and start this week."

CLOSING_MESSAGE = "That's what we took away from BHASe 2026.\nIf any of this hits close to home,\nwe'd love to talk."

# Contact info (do not change unless company info changes)
CONTACT_NAME = 'JP Montoya'
CONTACT_EMAIL = 'jp@getsolum.com'
CONTACT_PHONE = '628 276 2659'
CONTACT_WEB = 'getsolum.com'

# Output path — modify the conference name
OUTPUT_PATH = os.path.expanduser('~/BHASe_2026_OnePager_Solum_Health.pdf')


# ═══════════════════════════════════════════════════════
# PDF CLASS — Do not modify unless fixing a bug
# ═══════════════════════════════════════════════════════

class PDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'Letter')
        self.set_auto_page_break(auto=False)
        self.add_font('Geo', '', os.path.join(FD, 'Georgia.ttf'))
        self.add_font('Geo', 'B', os.path.join(FD, 'Georgia Bold.ttf'))
        self.add_font('Geo', 'I', os.path.join(FD, 'Georgia Italic.ttf'))
        self.add_font('Ar', '', os.path.join(FD, 'Arial.ttf'))
        self.add_font('Ar', 'B', os.path.join(FD, 'Arial Bold.ttf'))
        self.add_font('Ar', 'I', os.path.join(FD, 'Arial Italic.ttf'))

    def header(self):
        pass  # handled manually per page

    def footer(self):
        self.image(LOGO, M, self.h - 14, 24)
        self.set_draw_color(*BORDER)
        self.set_line_width(0.2)
        self.line(M + 28, self.h - 10.5, self.w - M, self.h - 10.5)
        self.set_xy(M + 30, self.h - 13)
        self.set_font('Ar', '', 7.5)
        self.set_text_color(*TEXT_LIGHT)
        self.cell(0, 5, 'Solum Health Industry Insights', 0, 0, 'L')
        self.cell(0, 5, f'{CONTACT_EMAIL}  |  {CONTACT_PHONE}  |  {CONTACT_WEB}', 0, 0, 'R')


# ═══════════════════════════════════════════════════════
# BUILD — Do not modify unless fixing a bug
# ═══════════════════════════════════════════════════════

def build():
    pdf = PDF()
    pdf.set_left_margin(M)
    pdf.set_right_margin(M)
    pw = pdf.w - 2 * M

    # ═══════════════════════════════════════
    # PAGE 1
    # ═══════════════════════════════════════
    pdf.add_page()

    # White top bar with logo
    pdf.set_fill_color(*WHITE)
    pdf.rect(0, 0, pdf.w, 16, 'F')
    pdf.image(LOGO, M, 3, 48)

    # "INDUSTRY INSIGHTS" tag
    pdf.set_xy(pdf.w - 70, 5)
    pdf.set_font('Ar', 'B', 7.5)
    pdf.set_text_color(*TERRACOTTA)
    pdf.cell(52, 4, 'INDUSTRY INSIGHTS', 0, 0, 'R')
    pdf.set_fill_color(*TERRACOTTA)
    pdf.rect(pdf.w - 70, 10, 52, 0.6, 'F')

    # Navy banner
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 16, pdf.w, 26, 'F')

    # Title
    pdf.set_xy(M, 19)
    pdf.set_font('Geo', 'B', 19)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 9, TITLE, 0, 1, 'L')

    # Subtitle
    pdf.set_x(M)
    pdf.set_font('Ar', '', 9)
    pdf.set_text_color(185, 200, 218)
    pdf.cell(0, 4.5, SUBTITLE, 0, 1)
    pdf.set_x(M)
    pdf.set_font('Ar', '', 7.5)
    pdf.set_text_color(130, 158, 190)
    pdf.cell(0, 4, EVENT_DETAILS, 0, 1)

    pdf.set_y(45)

    # Stat cards
    y = pdf.get_y()
    gap = 3.5
    cw = (pw - gap * 3) / 4
    for i, (num, l1, l2, color) in enumerate(STATS):
        x = M + i * (cw + gap)
        pdf.set_fill_color(*BG_CARD)
        pdf.rect(x, y, cw, 22, 'F')
        pdf.set_fill_color(*color)
        pdf.rect(x, y, cw, 2, 'F')
        pdf.set_xy(x, y + 3.5)
        pdf.set_font('Geo', 'B', 16)
        pdf.set_text_color(*color)
        pdf.cell(cw, 7, num, 0, 2, 'C')
        pdf.set_font('Ar', '', 7.5)
        pdf.set_text_color(*TEXT_BODY)
        pdf.cell(cw, 3.5, l1, 0, 2, 'C')
        pdf.set_font('Ar', '', 7)
        pdf.cell(cw, 3, l2, 0, 0, 'C')

    pdf.set_y(y + 25)

    # Helper functions
    def sec(title):
        pdf.ln(2.5)
        yy = pdf.get_y()
        pdf.set_fill_color(*TERRACOTTA)
        pdf.rect(M, yy, 2, 6, 'F')
        pdf.set_x(M + 5)
        pdf.set_font('Geo', 'B', 10.5)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 6, title, 0, 1)
        pdf.ln(0.5)

    def para(text):
        pdf.set_font('Ar', '', 9.5)
        pdf.set_text_color(*TEXT_BODY)
        pdf.multi_cell(pw, 4.6, text, 0, 'L')
        pdf.ln(1.5)

    def bul(bold, rest):
        pdf.set_x(M + 3)
        pdf.set_font('Ar', '', 9.5)
        pdf.set_text_color(*TEAL)
        pdf.cell(4, 4.6, chr(8226), 0, 0)
        pdf.set_font('Ar', 'B', 9.5)
        pdf.set_text_color(*TEXT_HEAD)
        pdf.write(4.6, bold + ' ')
        pdf.set_font('Ar', '', 9.5)
        pdf.set_text_color(*TEXT_BODY)
        pdf.multi_cell(pw - 9, 4.6, rest, 0, 'L')
        pdf.ln(0.8)

    # Render sections
    for title, content_type, content in SECTIONS:
        sec(title)
        if content_type == 'para':
            para(content)
        elif content_type == 'bullets':
            intro = SECTION_INTROS.get(title)
            if intro:
                para(intro)
            for bold_text, rest_text in content:
                bul(bold_text, rest_text)

    # ═══════════════════════════════════════
    # PAGE 2
    # ═══════════════════════════════════════
    pdf.add_page()

    # White top bar with logo
    pdf.set_fill_color(*WHITE)
    pdf.rect(0, 0, pdf.w, 14, 'F')
    pdf.image(LOGO, M, 3, 40)

    pdf.set_xy(pdf.w - 70, 4)
    pdf.set_font('Ar', 'B', 7.5)
    pdf.set_text_color(*TERRACOTTA)
    pdf.cell(52, 4, 'INDUSTRY INSIGHTS', 0, 0, 'R')
    pdf.set_fill_color(*TERRACOTTA)
    pdf.rect(pdf.w - 70, 9, 52, 0.6, 'F')

    # Navy banner
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 14, pdf.w, 16, 'F')

    pdf.set_xy(M, 16)
    pdf.set_font('Geo', 'B', 15)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 8, PAGE2_TITLE, 0, 1)

    pdf.set_y(33)
    pdf.set_font('Ar', 'I', 9)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.multi_cell(pw, 4.5, PAGE2_SUBTITLE, 0, 'L')
    pdf.ln(3)

    # Two-column role cards
    col_w = (pw - 5) / 2
    lx = M
    rx = M + col_w + 5
    sy = pdf.get_y()

    def role_card(x, y, title, items, color):
        pdf.set_fill_color(*color)
        pdf.rect(x, y, 2.5, 7, 'F')
        pdf.set_fill_color(*BG_CARD)
        pdf.rect(x + 2.5, y, col_w - 2.5, 7, 'F')
        pdf.set_xy(x + 6, y + 1)
        pdf.set_font('Ar', 'B', 9.5)
        pdf.set_text_color(*NAVY)
        pdf.cell(col_w - 10, 5, title, 0, 1)
        iy = y + 9
        for item in items:
            pdf.set_xy(x + 4, iy)
            pdf.set_font('Ar', '', 8.5)
            pdf.set_text_color(*color)
            pdf.cell(3.5, 4, chr(8226), 0, 0)
            pdf.set_text_color(*TEXT_BODY)
            pdf.multi_cell(col_w - 9, 4, item, 0, 'L')
            iy = pdf.get_y() + 1.5
        return iy

    # Left column
    left_y = sy
    for i, (title, items, color) in enumerate(ROLE_CARDS_LEFT):
        if i > 0:
            left_y += 2
        left_y = role_card(lx, left_y, title, items, color)

    # Right column
    right_y = sy
    for i, (title, items, color) in enumerate(ROLE_CARDS_RIGHT):
        if i > 0:
            right_y += 2
        right_y = role_card(rx, right_y, title, items, color)

    # Closing contact card
    card_y = max(left_y, right_y) + 4
    card_h = 30

    pdf.set_fill_color(*BG_WARM)
    pdf.rect(M, card_y, pw, card_h, 'F')
    pdf.set_fill_color(*TERRACOTTA)
    pdf.rect(M, card_y, 3, card_h, 'F')

    # Message left
    pdf.set_xy(M + 7, card_y + 3)
    pdf.set_font('Geo', 'I', 10.5)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(pw * 0.48, 5.5, CLOSING_MESSAGE, 0, 'L')

    # Logo + contact right
    cx = M + pw * 0.54
    pdf.image(LOGO, cx, card_y + 3, 30)

    pdf.set_xy(cx, card_y + 11)
    pdf.set_font('Ar', 'B', 10.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(60, 5, CONTACT_NAME, 0, 2, 'L')

    pdf.set_font('Ar', '', 9.5)
    pdf.set_text_color(*TEXT_BODY)
    pdf.cell(60, 4.2, CONTACT_EMAIL, 0, 2, 'L')
    pdf.cell(60, 4.2, CONTACT_PHONE, 0, 2, 'L')

    pdf.set_font('Ar', 'B', 9.5)
    pdf.set_text_color(*TEAL)
    pdf.cell(60, 4.2, CONTACT_WEB, 0, 2, 'L')

    # Save
    pdf.output(OUTPUT_PATH)
    return OUTPUT_PATH


if __name__ == '__main__':
    path = build()
    sz = os.path.getsize(path)
    with open(path, 'rb') as f:
        data = f.read()
    pages = data.count(b'/Type /Page') - data.count(b'/Type /Pages')
    print(f'Generated: {path}')
    print(f'Pages: {pages}  |  Size: {sz/1024:.0f} KB')
    if pages > 2:
        print('WARNING: Exceeds 2 pages!')
    else:
        print('OK: Fits in 2 pages.')
