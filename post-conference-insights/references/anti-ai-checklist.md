# Anti-AI Detection Checklist

Use this checklist when running the QA/humanization pass. Every item must pass before the
document is considered done.

## Forbidden Words (must be ZERO instances)

Replace these with natural alternatives. They are dead giveaways for AI-generated content.

| Forbidden | Use Instead |
|---|---|
| leverage | use, tap into, put to work |
| streamline | speed up, clean up, simplify |
| robust | strong, solid, reliable |
| comprehensive | complete, full, thorough |
| delve / dive into | look at, get into, explore |
| navigate | deal with, work through, figure out |
| nuanced | specific, detailed, tricky |
| foster | build, create, encourage |
| realm | (remove or restructure) |
| tapestry | (remove) |
| multifaceted | complicated (or restructure) |
| holistic | complete, whole-person (or restructure) |
| pivotal | important, critical, big |
| paradigm | (never use) |
| synergy | (never use) |
| utilize | use |
| facilitate | help, make possible, enable |
| empower | help, let, give the ability to |
| ecosystem | community, market, industry, space |
| cutting-edge | new, latest, modern |
| game-changer | (restructure entirely) |
| transformative / transform | change, reshape, improve |
| seamless / seamlessly | smooth, easy, without friction |
| unlock | open up, get access to, create |
| landscape | market, reality, world, situation |
| It's worth noting | (just state the thing) |
| In today's [x] | (remove, restructure) |
| Moreover / Furthermore / Additionally | And, Also, On top of that, or new sentence |
| However (at sentence start) | But, Still, That said |
| In conclusion | (never use) |
| moving forward | from here, next, going forward |
| at the end of the day | (remove or restructure) |

## Dashes as Punctuation (must be ZERO)

Em dashes (—), en dashes (–), and hyphens used as sentence punctuation must all be replaced:
- Use periods to break sentences
- Use commas
- Use "which" or "and" or "because" or "so" clauses
- Restructure the sentence entirely

**Compound-word hyphens are fine:** AI-powered, one-size-fits-all, mid-size, etc.

## Sentence Pattern Fixes

- Vary sentence length dramatically. Mix 5-word sentences with 25-word ones.
- Break up [Statement]. [Elaboration]. [Statement]. [Elaboration]. patterns.
- Add occasional sentence fragments. Like this one.
- Use contractions everywhere natural (it's, don't, can't, won't, that's, we're, they're)
- Start some sentences with "And" or "But"
- Include 3-4 colloquial phrases ("here's the thing," "look, we get it," "real talk:")
- Remove any sentence that sounds like a thesis statement

## Structural AI Patterns to Fix

- No more than 2 bold phrases per section (AI overuses bold)
- Reduce bulleted lists. Convert at least half to flowing paragraphs.
- Remove "Here's what..." followed by a list pattern
- Vary header styles. Not every section needs the same format.
- Remove "Key takeaway:" or "The bottom line:" framing

## Human Voice Markers to Add

- 1-2 opinions that feel personal ("we thought this panel was the strongest")
- Reference specific moments ("during the Wednesday afternoon session, one operator stood up...")
- Include something informal ("look, we get it")
- Add a personal touch about being at the event ("the coffee conversations were just as good")
- Express honest uncertainty ("we're not 100% sure this trend holds everywhere, but...")

## Subtle AI Patterns to Check

- Too many paragraphs starting with "The" (vary openers)
- "not just X, but Y" pattern used more than once (remove extras)
- "This is not/isn't just about X. It's about Y." pattern (remove if present)
- Every section ending with a pithy one-liner summary (vary endings)
- Every section following the same emotional arc (problem > evidence > implication)
- All paragraphs roughly the same length (vary aggressively)

## Scoring

After all fixes, score the document:
- **Under 15%**: Ship it.
- **15-20%**: Acceptable. One more pass if time allows.
- **Over 20%**: Must iterate. Find the patterns dragging the score up and fix them.

Top signals that a document is human-written:
1. Experiential specificity (physical details from being at the event)
2. Genuine uncertainty and editorial opinion
3. Industry-native vocabulary used without over-explanation
4. Irregular paragraph lengths and sentence rhythms
5. Colloquial language mixed with technical terminology
