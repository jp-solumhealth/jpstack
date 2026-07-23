export const meta = {
  name: 'position-debate',
  description: 'Per-position BULL vs BEAR adversarial debate: parallel agents gather analyst price targets + consensus, argue, a judge assigns scenario probabilities and a probability-weighted expected return, then a HOLD/TRIM/SELL/ADD/DOUBLE_DOWN call — synthesized into a portfolio action plan.',
  phases: [
    { title: 'Bull & Bear research' },
    { title: 'Judge & weight' },
    { title: 'Synthesize plan' },
  ],
}

// ---- structured output schemas ----
const CASE_SCHEMA = {
  type: 'object',
  properties: {
    ticker: { type: 'string' },
    stance: { type: 'string', enum: ['bull', 'bear'] },
    currentPrice: { type: 'number', description: '0 if not found' },
    priceTarget12m: { type: 'number' },
    impliedReturnPct: { type: 'number' },
    thesis: { type: 'string' },
    keyPoints: { type: 'array', items: { type: 'string' } },
    analystTargets: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          bank: { type: 'string' }, rating: { type: 'string' },
          target: { type: 'number' }, date: { type: 'string' },
        },
        required: ['bank'],
      },
    },
    consensus: { type: 'string', description: 'consensus rating/target + how sourced; [ESTIMATE] if unverified' },
    keyRisksToOwnView: { type: 'array', items: { type: 'string' } },
    sources: { type: 'array', items: { type: 'string' } },
  },
  required: ['ticker', 'stance', 'priceTarget12m', 'thesis', 'keyPoints', 'consensus'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    ticker: { type: 'string' },
    pBull: { type: 'number' }, pBase: { type: 'number' }, pBear: { type: 'number' },
    bullReturnPct: { type: 'number' }, baseReturnPct: { type: 'number' }, bearReturnPct: { type: 'number' },
    evReturnPct: { type: 'number' },
    recommendation: { type: 'string', enum: ['DOUBLE_DOWN', 'ADD', 'HOLD', 'TRIM', 'SELL'] },
    conviction: { type: 'string', enum: ['LOW', 'MEDIUM', 'HIGH'] },
    debateSummary: { type: 'string', description: "bull's best rebuttal to bear, and bear's best rebuttal to bull" },
    rationale: { type: 'string' },
    sizingNote: { type: 'string', description: 'concrete current→target weight' },
  },
  required: ['ticker', 'pBull', 'pBase', 'pBear', 'evReturnPct', 'recommendation', 'conviction', 'rationale'],
}

const PLAN_SCHEMA = {
  type: 'object',
  properties: {
    actions: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          ticker: { type: 'string' }, action: { type: 'string' },
          currentWeightPct: { type: 'number' }, targetWeightPct: { type: 'number' },
          reason: { type: 'string' },
        },
        required: ['ticker', 'action', 'reason'],
      },
    },
    orderOfOperations: { type: 'array', items: { type: 'string' } },
    cashAndCoreBuild: { type: 'string' },
    portfolioNotes: { type: 'string' },
    topRisks: { type: 'array', items: { type: 'string' } },
  },
  required: ['actions', 'portfolioNotes'],
}

// ---- inputs (args may arrive as an object OR a JSON string) ----
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
A = A || {}
const positions = A.positions || []
const ctx = A.context || ''
const today = A.today || 'today'
if (!positions.length) { log('No positions in args.positions — nothing to debate.'); return { error: 'no positions' } }
log(`Debating ${positions.length}: ${positions.map(p => p.ticker).join(', ')}`)

function casePrompt(pos, stance) {
  return `You are a rigorous ${stance.toUpperCase()} equity analyst. Build the strongest HONEST ${stance} case for ${pos.ticker} (${pos.name || ''}), currently ~${pos.weightPct ?? '?'}% of this investor's portfolio. Today is ${today}.
Investor: aggressive, 5-10y horizon, book is heavily AI-infrastructure. CONTEXT: ${ctx}
STEPS:
1. Use WebSearch/WebFetch to find the CURRENT price and RECENT (last ~3 months) analyst PRICE TARGETS from MAJOR banks (Goldman, Morgan Stanley, JPMorgan, BofA, Barclays, UBS, Wells Fargo, Citi, etc.) plus the consensus rating/mean target. Record each target's bank + date. Paid terminals are NOT available — use public web; CITE every source URL+date in 'sources'; tag any unverifiable figure [ESTIMATE]. Do NOT fabricate analyst targets — if you can't find them, say so in 'consensus' and leave analystTargets sparse.
2. Build the strongest ${stance} case: a 12-month price target, implied return % vs current price, 3-6 specific key points, catalysts.
3. List the key risks TO YOUR OWN ${stance} view (be intellectually honest).
Return the schema.`
}

function judgePrompt(pos, bull, bear) {
  return `You are the portfolio manager adjudicating a BULL vs BEAR debate on ${pos.ticker} (~${pos.weightPct ?? '?'}% of the book). Today ${today}. Investor: aggressive, 5-10y, AI-infra-heavy book; single-name cap 10%, AI-theme cap ~35%; currently NO diversifying core. CONTEXT: ${ctx}
BULL: ${JSON.stringify(bull)}
BEAR: ${JSON.stringify(bear)}
DO IN ORDER:
1. ARGUE both ways — state the bull's strongest rebuttal to the bear AND the bear's strongest rebuttal to the bull (put this in debateSummary). Be specific, not generic.
2. Assign 12-month scenario probabilities pBull+pBase+pBear=1.0 and a return % for each scenario vs current price (base = most likely).
3. Compute evReturnPct = pBull*bullReturnPct + pBase*baseReturnPct + pBear*bearReturnPct.
4. Recommendation (DOUBLE_DOWN/ADD/HOLD/TRIM/SELL) + conviction, weighing BOTH the EV/skew AND portfolio fit: if the name is over the 10% single-name cap or piles onto an already-overweight theme, lean TRIM/SELL even with positive EV; if EV is strongly positive AND it's underweight AND conviction is high, ADD/DOUBLE_DOWN.
5. sizingNote: concrete current→target weight.
Be decisive. Return the schema.`
}

phase('Bull & Bear research')
const judged = await pipeline(
  positions,
  (pos) => parallel([
    () => agent(casePrompt(pos, 'bull'), { label: `bull:${pos.ticker}`, phase: 'Bull & Bear research', schema: CASE_SCHEMA }),
    () => agent(casePrompt(pos, 'bear'), { label: `bear:${pos.ticker}`, phase: 'Bull & Bear research', schema: CASE_SCHEMA }),
  ]),
  (cases, pos) => {
    const [bull, bear] = cases || []
    return agent(judgePrompt(pos, bull, bear), { label: `judge:${pos.ticker}`, phase: 'Judge & weight', schema: VERDICT_SCHEMA })
      .then(v => ({ ...v, bull, bear }))
  },
)

const ok = judged.filter(Boolean)
phase('Synthesize plan')
const plan = await agent(
  `You are the PM. Probabilistic bull/bear verdicts for an AI-infra-heavy, aggressively-positioned personal portfolio (single-name cap 10%, AI-theme cap ~35%, currently NO diversifying core). Today ${today}. CONTEXT: ${ctx}
VERDICTS: ${JSON.stringify(ok.map(v => ({ ticker: v.ticker, ev: v.evReturnPct, rec: v.recommendation, conv: v.conviction, pBull: v.pBull, pBase: v.pBase, pBear: v.pBear, sizing: v.sizingNote })))}
Produce a portfolio ACTION PLAN: per-name action with current→target weight; an explicit ORDER OF OPERATIONS (what to trim first — likely the over-cap name); how to fund the missing risk-balanced core; and the top portfolio risks. Decisive and specific. Return the schema.`,
  { label: 'synthesize', phase: 'Synthesize plan', schema: PLAN_SCHEMA },
)

return { generatedFor: positions.map(p => p.ticker), verdicts: ok, plan }
