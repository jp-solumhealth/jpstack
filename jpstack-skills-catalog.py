#!/usr/bin/env python3
"""Generate jpstack Skills Catalog PDF"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Colors
DARK = HexColor("#1a1a2e")
ACCENT = HexColor("#4361ee")
LIGHT_BG = HexColor("#f0f3ff")
GRAY = HexColor("#6b7280")
WHITE = HexColor("#ffffff")
BORDER = HexColor("#e2e8f0")

# Styles
title_style = ParagraphStyle(
    "Title", fontName="Helvetica-Bold", fontSize=28,
    textColor=DARK, alignment=TA_CENTER, spaceAfter=4
)
subtitle_style = ParagraphStyle(
    "Subtitle", fontName="Helvetica", fontSize=11,
    textColor=GRAY, alignment=TA_CENTER, spaceAfter=20
)
section_style = ParagraphStyle(
    "Section", fontName="Helvetica-Bold", fontSize=14,
    textColor=ACCENT, spaceBefore=16, spaceAfter=8
)
skill_name_style = ParagraphStyle(
    "SkillName", fontName="Helvetica-Bold", fontSize=10.5,
    textColor=DARK, spaceAfter=1
)
skill_desc_style = ParagraphStyle(
    "SkillDesc", fontName="Helvetica", fontSize=9,
    textColor=GRAY, leading=12
)
footer_style = ParagraphStyle(
    "Footer", fontName="Helvetica", fontSize=8,
    textColor=GRAY, alignment=TA_CENTER
)

# Skills data: (emoji, name, description)
sections = [
    ("DAILY OPS & REPORTING", [
        ("\u2615", "Chief of Staff", "Daily CEO morning briefing. Pulls HubSpot, Fireflies & Apollo to surface hot deals, action items, pending responses & priorities."),
        ("\U0001F4CA", "Investor Report", "Monthly investor updates from Google Sheets KPIs & Fireflies calls. Outputs a branded DOCX with metrics, highlights & asks."),
        ("\U0001F50D", "Weekly Retro", "Scores your week across deals, calls, content & outreach. Wins, losses, learnings & next-week priorities in one report."),
        ("\U0001F3AF", "Win-Loss Analysis", "Systematic deal analysis from HubSpot + Fireflies. ICP patterns, root causes, competitor tracking & pipeline hygiene."),
    ]),
    ("SALES EXECUTION", [
        ("\U0001F4B0", "Pricing Coach", "Weekly call coaching. Extracts pricing moments from Fireflies, scores them 1-5 & delivers scripts for next week."),
        ("\U0001F4CB", "Meeting Prep", "Pre-call intel brief from HubSpot, Fireflies & Apollo. Company context, relationship history, deal status & talking points."),
        ("\U0001F4E8", "Meeting Follow-Up", "Post-call automation: follow-up email, HubSpot deal notes & internal debrief with buying signals and objections."),
        ("\U0001F4DD", "SOW Builder", "Generates scoped Statements of Work with ROI. Pulls from Fireflies, HubSpot & Apollo, outputs branded PDF."),
        ("\U0001F4E3", "Sales Enablement", "Creates pitch decks, one-pagers, objection docs & demo scripts tailored to your ICP and sales motion."),
    ]),
    ("CONFERENCES & EVENTS", [
        ("\U0001F3AA", "Conference Prep", "6-phase workflow: extract attendees, classify ICPs, enrich via Apollo, validate emails, upload to Instantly & build agenda."),
        ("\U0001F4F0", "Post-Conference Insights", "Branded 1-2 page recap PDFs with stats, insights & role-based action items. Shareable value-add for prospects."),
        ("\U0001F680", "Post-Conference Follow-Up", "Segments leads HOT/WARM/COOL/COLD, drafts personalized emails, builds sequences & creates HubSpot deals."),
    ]),
    ("PRODUCT & MARKET INTEL", [
        ("\U0001F9E0", "Product Insights", "Sprint planning intel. Aggregates feature requests, bugs & UX friction from calls and notes. RICE-scores everything."),
        ("\U0001F4A1", "PMF Pulse", "7-source intelligence (Fireflies, HubSpot, Reddit, Indeed, Apollo, forums) to surface pain points & PMF indicators."),
    ]),
    ("CONTENT & MARKETING", [
        ("\U0001F426", "X Healthcare Posts", "Viral X posts/threads for Healthcare AI audiences. Operator voice, clear stances, practical implications."),
        ("\U0001F3A0", "LinkedIn Carousel", "Branded 4:5 carousel PDFs (1080x1350px). 8-15 slides with hooks, safe zones & mobile-friendly design."),
        ("\U0001F4DD", "Copywriting", "Marketing copy for any page: homepage, landing, pricing, features. Human tone, no AI jargon."),
        ("\U0001F4AC", "Content Strategy", "Plan what content to create, topic clusters & editorial calendar aligned to your ICP."),
        ("\U0001F4E7", "Cold Email", "B2B cold emails & follow-up sequences. Subject lines, openers, CTAs optimized for replies."),
        ("\U0001F4E9", "Email Sequence", "Drip campaigns, nurture flows & lifecycle emails with timing and segmentation guidance."),
    ]),
    ("WEBSITE & COMPLIANCE", [
        ("\U0001F310", "Site Review", "7-phase SEO + conversion audit with fact-checking. Technical SEO, CRO, intake forms & healthcare checks."),
        ("\U0001F3E5", "Prior Auth Review", "Automates payer review of PA requests. Validates NPI, ICD-10, CMS coverage & generates decisions in <5 min."),
        ("\u2705", "Fact-Check", "Verifies numerical claims before finalizing docs. Classifies each as CONFIRMED, CLOSE, WRONG or UNVERIFIABLE."),
    ]),
    ("BRAND & DESIGN", [
        ("\U0001F3A8", "Solum Health Brand", "Auto-applies brand system (logo, colors, typography) to all Solum content, docs & landing pages."),
        ("\U0001F4C8", "SEO Audit", "Technical SEO, meta tags, on-page issues & ranking diagnostics for any site."),
        ("\U0001F4BB", "Pricing Strategy", "Pricing tiers, packaging, value metrics, Van Westendorp & willingness-to-pay frameworks."),
    ]),
]

def build_pdf():
    output_path = "/Users/juanmontoya/Documents/Claude/Skills/jpstack/jpstack-skills-catalog.pdf"
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.7*inch, rightMargin=0.7*inch,
        topMargin=0.6*inch, bottomMargin=0.6*inch
    )
    story = []

    # Header
    story.append(Spacer(1, 10))
    story.append(Paragraph("jpstack Skills Catalog", title_style))
    story.append(Paragraph("Your AI-powered operating system for running Solum Health", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=10))

    # Count total skills
    total = sum(len(s[1]) for s in sections)
    story.append(Paragraph(
        f"<b>{total} skills</b> across {len(sections)} categories \u2014 all built for founder-led B2B SaaS",
        ParagraphStyle("Count", fontName="Helvetica", fontSize=9.5, textColor=GRAY, alignment=TA_CENTER, spaceAfter=6)
    ))

    for section_name, skills in sections:
        story.append(Spacer(1, 4))
        story.append(Paragraph(section_name, section_style))

        # Build skill rows as a table
        table_data = []
        for emoji, name, desc in skills:
            emoji_p = Paragraph(
                f'<font size="13">{emoji}</font>',
                ParagraphStyle("Emoji", fontSize=13, alignment=TA_CENTER)
            )
            name_p = Paragraph(f"<b>{name}</b>", skill_name_style)
            desc_p = Paragraph(desc, skill_desc_style)

            # Stack name + desc
            inner = Table([[name_p], [desc_p]], colWidths=[5.6*inch])
            inner.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            table_data.append([emoji_p, inner])

        t = Table(table_data, colWidths=[0.45*inch, 5.8*inch])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (0, -1), 4),
            ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDER),
        ]))
        story.append(KeepTogether([t]))

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=8))
    story.append(Paragraph(
        "Solum Health \u2022 getsolum.com \u2022 Built with Claude Code",
        footer_style
    ))

    doc.build(story)
    print(f"PDF saved to {output_path}")

if __name__ == "__main__":
    build_pdf()
