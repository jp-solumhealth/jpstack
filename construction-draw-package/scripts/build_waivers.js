#!/usr/bin/env node
// Florida ch. 713 lien waivers from a deal config. One letter + one appendix per
// property, itemised so the payer can see exactly what is being released.
//
//   node build_waivers.js --deal rbi-ocala --out /abs/path/waivers.docx
//   node build_waivers.js --deal rbi-ocala --exclude-unpaid    # release only paid work
//   node build_waivers.js --deal rbi-ocala --form final        # final, not progress
//   node build_waivers.js --deal rbi-ocala --unexecuted        # leave dates blank too
//
// Execution fields: the signatory's own signature line and the three notarial fields
// are ALWAYS left blank. A notary must complete their jurat personally (FS 117.05);
// pre-filling it for them is the one thing this script will not do.

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, PageBreak, ShadingType,
} = require("docx");

// ------------------------------------------------------------------------ args
const argv = process.argv.slice(2);
const arg = (k, d) => {
  const i = argv.indexOf(`--${k}`);
  return i === -1 ? d : argv[i + 1];
};
const flag = (k) => argv.includes(`--${k}`);

const dealName = arg("deal", "rbi-ocala");
const cfgPath = path.join(__dirname, "..", "deals", `${dealName}.json`);
if (!fs.existsSync(cfgPath)) {
  console.error(`no deal config at ${cfgPath}`);
  process.exit(1);
}
const cfg = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
const outPath = arg("out", path.join(process.cwd(), `${dealName}-lien-waivers.docx`));
const excludeUnpaid = flag("exclude-unpaid");
const unexecuted = flag("unexecuted");
const form = arg("form", cfg.waiver.form || "progress");

const FORM_TITLE = {
  progress: "PROGRESS PAYMENT  WAIVER AND RELEASE OF LIEN",
  final: "FINAL PAYMENT  WAIVER AND RELEASE OF LIEN",
}[form];
if (!FORM_TITLE) {
  console.error(`--form must be progress or final, got ${form}`);
  process.exit(1);
}

// ----------------------------------------------------------------- primitives
const FONT = "Times New Roman";
const CONTENT_W = 9360;              // Letter 12240 - 1440*2 margins
const COL_ITEM = 6600, COL_AMT = 2760;
const money = (n) =>
  "$" + Number(n).toLocaleString("en-US", { minimumFractionDigits: 2,
                                            maximumFractionDigits: 2 });
const r2 = (n) => Math.round((n + Number.EPSILON) * 100) / 100;

const P = (children, opts = {}) => new Paragraph({ children, ...opts });
const T = (text, opts = {}) => new TextRun({ text, font: FONT, size: 24, ...opts });
const blank = (n) => "_".repeat(n);
// Apple Pages drops w:jc and w:spacing from a docx-js file but honours an empty
// paragraph, so all vertical space is explicit and all text is left aligned.
const gap = (n = 1) => Array.from({ length: n }, () => new Paragraph({ children: [T("")] }));
const sectionLabel = (t) => P([T(t, { bold: true, size: 20, color: "666666" })]);
const docTitle = (t) => P([T(t, { bold: true, underline: {} })]);

function cell(text, { bold = false, w = COL_ITEM, shade = null, indent = false } = {}) {
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: shade ? { type: ShadingType.CLEAR, fill: shade } : undefined,
    margins: { top: 30, bottom: 30, left: 120, right: 120 },
    children: [P([T(text, { bold, size: 22 })],
      { indent: indent ? { left: 240 } : undefined })],
  });
}
const row = (label, amount, o = {}) => new TableRow({
  children: [
    cell(label, { bold: o.bold, indent: o.indent, shade: o.shade }),
    cell(amount === null ? "" : money(amount),
      { bold: o.bold, w: COL_AMT, shade: o.shade }),
  ],
});
const headerRow = (a, b) => new TableRow({
  tableHeader: true,
  children: [cell(a, { bold: true, shade: "D9D9D9" }),
             cell(b, { bold: true, w: COL_AMT, shade: "D9D9D9" })],
});

// ------------------------------------------------------------------ the numbers
const FULL = cfg.waiver.full_activities.map(String);
const PARTIAL = cfg.waiver.partial_activities || {};
const PCT = cfg.commission_pct;

// "1 and 2" / "1, 2 and 3" — a list a lawyer would read without stumbling.
const joinList = (xs) => xs.length < 2 ? xs.join("")
  : `${xs.slice(0, -1).join(", ")} and ${xs[xs.length - 1]}`;

function activityValue(p, act) {
  const a = p.ledger[act];
  const factor = PARTIAL[act] !== undefined ? PARTIAL[act] : 1;
  const comm = r2(a.commission * factor);
  return { hard: a.hard, commFull: a.commission, comm, value: r2(a.hard + comm) };
}
function grossTotal(p) {
  return r2([...FULL, ...Object.keys(PARTIAL)]
    .reduce((s, act) => s + activityValue(p, act).value, 0));
}
function consideration(p) {
  return excludeUnpaid ? r2(grossTotal(p) - p.unpaid) : grossTotal(p);
}

// ------------------------------------------------------------------ the release
function letterFor(p) {
  const out = [];
  const covered = [...FULL, ...Object.keys(PARTIAL)].sort();
  const partialList = Object.keys(PARTIAL).sort();

  out.push(sectionLabel(`LETTER ${p.letter}`));
  out.push(docTitle(FORM_TITLE));
  out.push(...gap(1));

  out.push(P([
    T("The undersigned lienor, in consideration of the sum of "),
    T(money(consideration(p)), { bold: true }),
    T(", hereby waives and releases its lien and right to claim a lien for labor, " +
      "services, or materials furnished through "),
    T(cfg.period.from, { bold: true }),
    T(" to "),
    T(cfg.period.to, { bold: true }),
    T(" on the job of "),
    T(cfg.owner, { bold: true }),
    T(" to the following property:"),
  ]));
  out.push(...gap(1));
  out.push(P([T(p.address, { bold: true })]));
  out.push(P([T(`Parcel ID No. ${p.parcel}`, { bold: true })]));
  out.push(P([T(`Marion County Building Permit No. ${p.permit}`)]));
  out.push(...gap(1));

  // The exceptions paragraph is what keeps a partial waiver partial. Without it a
  // signed waiver reads as releasing everything through the date, including work
  // the lienor has not been paid for.
  const fullTxt = FULL.length === 1 ? `Activity ${FULL[0]}`
    : `Activities ${joinList(FULL)}`;
  let exc =
    "This waiver and release does not cover any retention or labor, services, or " +
    `materials furnished after the date specified. Additional exceptions: it is limited to ${fullTxt}`;
  if (partialList.length) {
    exc += `, and to Activity ${partialList.join(" and ")} to the extent completed through ` +
      `${cfg.period.to}`;
  }
  exc += `, each as itemised in Appendix ${p.letter}, attached and incorporated by ` +
    "reference, in the total amount stated above. It does not cover ";
  if (partialList.length) exc += `the balance of Activity ${partialList.join(" and ")}, `;
  const later = cfg.draw.all_activities.map(String)
    .filter((a) => !covered.includes(a));
  // Each remaining activity is named separately — a reader should not have to
  // expand "Activities 4, 5" to know what is excluded.
  if (later.length) exc += later.map((a) => `Activity ${a}`).join(", ") + ", ";
  exc += "change order work, retainage, or anything furnished after that date.";
  if (excludeUnpaid) {
    exc += " It further does not cover any work for which the undersigned has not " +
      "received payment, as deducted in Appendix " + p.letter + ".";
  }
  exc += " It is given by the undersigned lienor only and is not a waiver or release " +
    "by any subcontractor, supplier or materialman.";
  out.push(P([T(exc)]));
  out.push(...gap(1));

  out.push(P([T(unexecuted ? `DATED on ${blank(14)}, 20${blank(6)}.`
                           : `DATED on ${cfg.execution.date}.`)]));
  out.push(...gap(1));

  const c = cfg.contractor;
  out.push(P([T("(Name & address of Lienor)")]));
  out.push(P([T(c.name, { bold: true })]));
  out.push(P([T(c.descriptor)]));
  out.push(P([T(c.address_1)]));
  out.push(P([T(c.address_2)]));
  out.push(P([T(c.license)]));
  out.push(...gap(2));

  // ALWAYS blank — the lienor signs this in the notary's presence.
  out.push(P([T(`By: ${blank(40)}`)]));
  out.push(...gap(1));
  out.push(P([T(`Print name:  ${c.principal}`)]));
  out.push(P([T(unexecuted || !c.principal_title
    ? `Title: ${blank(36)}` : `Title: ${c.principal_title}`)]));
  out.push(...gap(1));

  const jurat = unexecuted
    ? `this ${blank(8)} day of ${blank(16)}, 20${blank(6)}, by `
    : `this ${cfg.execution.day} day of ${cfg.execution.month}, ${cfg.execution.year}, by `;
  out.push(P([
    T(`Sworn to (or affirmed) and subscribed before me ${jurat}`),
    T(c.principal, { bold: true }),
    T(" (name of person making statement)."),
  ]));
  out.push(...gap(2));

  // ALWAYS blank — FS 117.05, the notary completes their own jurat.
  out.push(P([T(blank(52))]));
  out.push(P([T("(Signature of Notary Public — State of Florida)")]));
  out.push(...gap(1));
  out.push(P([T(`Personally Known ${blank(8)}  OR  Produced Identification ${blank(8)}`)]));
  out.push(P([T(`Type of Identification Produced ${blank(26)}`)]));
  out.push(P([new PageBreak()]));
  return out;
}

// ---------------------------------------------------------------------- appendix
function appendixFor(p) {
  const out = [];
  const covered = [...FULL, ...Object.keys(PARTIAL)].sort();
  // "TO DATE" signals that a partial activity is included — it is the difference
  // between a schedule of finished work and a snapshot of work in progress.
  const scope = `ACTIVIT${covered.length > 1 ? "IES" : "Y"} ` +
    `${joinList(covered).toUpperCase()}` +
    (Object.keys(PARTIAL).length ? " TO DATE" : "");
  out.push(sectionLabel(`APPENDIX ${p.letter}`));
  out.push(docTitle(`SCHEDULE OF COMPLETED WORK — ${scope}`));
  out.push(...gap(1));
  out.push(P([T(p.address, { bold: true })]));
  out.push(P([T(`Parcel ID No. ${p.parcel}`, { bold: true })]));
  out.push(P([T(`Marion County Building Permit No. ${p.permit}`)]));
  out.push(P([T(`Construction start ${cfg.period.from}. Work complete through ${cfg.period.to}.`)]));
  out.push(...gap(1));
  out.push(P([T(`Attached to and forming part of Letter ${p.letter}.`)]));
  out.push(...gap(1));

  const rows = [headerRow("Work item", "Amount")];
  for (const act of covered) {
    const v = activityValue(p, act);
    const partial = PARTIAL[act] !== undefined;
    const td = partial ? " to date" : "";
    rows.push(row(cfg.activity_labels[act] +
      (partial ? " (work completed to date)" : ""), null,
      { bold: true, shade: "F2F2F2" }));
    for (const [k, amt] of p.ledger[act].items) rows.push(row(k, amt, { indent: true }));
    rows.push(row(`Hard cost subtotal, Activity ${act}${td}`, v.hard, { bold: true }));
    rows.push(row(partial
      ? `General Contractor commission, ${PARTIAL[act] * 100}% of the ${PCT * 100}% ` +
        `(${money(v.commFull)})`
      : `General Contractor commission, ${PCT * 100}% of hard cost`,
      v.comm, { indent: true }));
    rows.push(row(`Activity ${act} completed work value${td}`, v.value, { bold: true }));
  }
  rows.push(row(`TOTAL COMPLETED WORK VALUE, ${scope}`, grossTotal(p),
    { bold: true, shade: "D9D9D9" }));
  if (excludeUnpaid) {
    rows.push(row("Less: work not yet paid to the Contractor", -p.unpaid,
      { bold: true }));
    rows.push(row("AMOUNT RELEASED BY LETTER " + p.letter, consideration(p),
      { bold: true, shade: "D9D9D9" }));
  }

  out.push(new Table({
    columnWidths: [COL_ITEM, COL_AMT],
    width: { size: CONTENT_W, type: WidthType.DXA },
    rows,
  }));
  out.push(...gap(1));

  let note = `The total above is the consideration stated in Letter ${p.letter}. ` +
    `Commission is charged at ${PCT * 100}% of verified hard cost ` +
    `${cfg.commission_authority}`;
  const partialList = Object.keys(PARTIAL);
  if (partialList.length) {
    note += `, taken at ${PARTIAL[partialList[0]] * 100}% on Activity ` +
      `${joinList(partialList)} because that activity is still in progress`;
  }
  note += ". " + cfg.commission_exclusions + " Source: " + cfg.waiver.ledger_source +
    ` as recorded through ${cfg.period.to}.`;
  out.push(P([T(note, { size: 20, italics: true })]));
  out.push(P([new PageBreak()]));
  return out;
}

// ---------------------------------------------------------------------- assemble
const children = [];
for (const p of cfg.properties) {
  children.push(...letterFor(p));
  children.push(...appendixFor(p));
}
children.pop();   // drop the trailing PageBreak so there is no blank final page

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 24 } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },   // US Letter, not the A4 default
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    children,
  }],
});

// ---------------------------------------------------------------------- selftest
// Guards the invariant that matters: whatever else changes, the signatory's own
// signature line and the three notarial fields must come out blank on every letter.
if (flag("selftest")) {
  Packer.toBuffer(doc).then((buf) => {
    let fails = 0;
    const chk = (cond, label) => {
      console.log(`  ${cond ? "PASS" : "FAIL"}  ${label}`);
      if (!cond) fails++;
    };
    const n = cfg.properties.length;
    console.log("SELFTEST — build_waivers.js\n");
    const expect = { A: 94180.86, B: 94591.10, C: 93830.59 };
    for (const p of cfg.properties) {
      chk(grossTotal(p) === expect[p.letter],
        `Letter ${p.letter} gross ${money(grossTotal(p))}`);
      chk(r2(grossTotal(p) - p.unpaid) ===
          r2({ A: 68535.34, B: 68897.16, C: 68394.36 }[p.letter]),
        `Letter ${p.letter} ex-unpaid ${money(r2(grossTotal(p) - p.unpaid))}`);
    }
    // Inflate the docx and count the execution blanks in the real XML.
    const raw = fs.mkdtempSync(require("os").tmpdir() + "/wv-");
    fs.writeFileSync(raw + "/w.docx", buf);
    const { execSync } = require("child_process");
    const text = execSync(`unzip -p ${raw}/w.docx word/document.xml`,
      { maxBuffer: 1 << 26 }).toString();
    fs.rmSync(raw, { recursive: true, force: true });
    chk((text.match(/By: _{10,}/g) || []).length === n,
      `signature line blank on all ${n} letters`);
    chk((text.match(/Personally Known _{4,}/g) || []).length === n,
      `notary ID selection blank on all ${n} letters`);
    chk((text.match(/Type of Identification Produced _{4,}/g) || []).length === n,
      `notary ID type blank on all ${n} letters`);
    chk((text.match(/DATED on _{4,}/g) || []).length === 0,
      "DATED filled (default execution mode)");
    chk((text.match(/Title: _{4,}/g) || []).length === 0, "Title filled");
    console.log(fails ? `\nRESULT: ${fails} FAILURE(S)` : "\nRESULT: ALL PASS");
    process.exit(fails ? 1 : 0);
  });
} else {
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outPath, buf);
  const tot = cfg.properties.reduce((s, p) => s + consideration(p), 0);
  console.log(`wrote ${outPath}  (${buf.length} bytes)`);
  console.log(`  ${cfg.properties.length} ${form} waivers, releasing ${money(r2(tot))}` +
    (excludeUnpaid ? "  [unpaid work excluded]" : ""));
  for (const p of cfg.properties) {
    console.log(`    Letter ${p.letter}  ${p.address.split(",")[0]}  ` +
      `${money(consideration(p))}`);
  }
  if (!excludeUnpaid) {
    const unpaid = cfg.properties.reduce((s, p) => s + p.unpaid, 0);
    if (unpaid > 0) {
      console.log(`  WARNING: ledger flags ${money(r2(unpaid))} as unpaid across these ` +
        `properties.\n           Confirm payment, or re-run with --exclude-unpaid.`);
    }
  }
});
}
