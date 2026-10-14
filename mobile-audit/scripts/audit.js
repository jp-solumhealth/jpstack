#!/usr/bin/env node
/**
 * Mobile optimization audit for the Solum Health landing page.
 *
 * Usage:
 *   node audit.js <url> [--json]
 *
 * Renders the page at phone, large-phone and tablet widths with real Chromium
 * and reports measured failures — horizontal scroll, elements past the right
 * edge, touch targets under 44px, and text under 12px.
 *
 * Exits non-zero if any BLOCKING issue is found, so it can gate a deploy.
 */

const { chromium } = require("playwright");

const VIEWPORTS = [
  { w: 375, h: 812, n: "iPhone SE / 13 mini" },
  { w: 390, h: 844, n: "iPhone 14/15" },
  { w: 768, h: 1024, n: "iPad portrait" },
];

const MIN_TAP = 44; // Apple HIG minimum
const MIN_FONT = 12; // below this is hard to read on a phone

async function auditViewport(browser, url, vp) {
  const page = await browser.newPage({
    viewport: { width: vp.w, height: vp.h },
    deviceScaleFactor: 2,
    isMobile: vp.w < 768,
    hasTouch: vp.w < 768,
  });
  await page.goto(url, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(1500);

  const result = await page.evaluate(
    ({ vw, minTap, minFont }) => {
      const de = document.documentElement;
      const out = {
        scrollWidth: de.scrollWidth,
        clientWidth: de.clientWidth,
        overflow: [],
        smallTargets: [],
        smallText: [],
      };

      // An element only counts as an overflow problem if nothing clips it.
      // Carousels and mockups deliberately extend past the viewport inside an
      // overflow:hidden parent — those are by design, not bugs.
      const isClipped = (el) => {
        let a = el.parentElement;
        while (a) {
          const s = getComputedStyle(a);
          if (s.overflow === "hidden" || s.overflowX === "hidden" || s.overflow === "auto" || s.overflowX === "auto") return true;
          a = a.parentElement;
        }
        return false;
      };

      const seen = new Set();
      for (const el of document.querySelectorAll("*")) {
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) continue;
        const st = getComputedStyle(el);
        if (st.visibility === "hidden" || st.display === "none" || st.opacity === "0") continue;

        if (r.right > vw + 1 && st.position !== "fixed" && !isClipped(el)) {
          const cls = typeof el.className === "string" ? el.className.split(" ")[0] : "";
          const key = el.tagName + cls;
          if (!seen.has(key)) {
            seen.add(key);
            out.overflow.push({
              tag: el.tagName,
              cls: typeof el.className === "string" ? el.className.slice(0, 60) : "",
              over: Math.round(r.right - vw),
              width: Math.round(r.width),
            });
          }
        }

        if (["A", "BUTTON"].includes(el.tagName) && st.pointerEvents !== "none") {
          if (r.height > 0 && r.height < minTap) {
            out.smallTargets.push({
              txt: (el.innerText || "").trim().slice(0, 30),
              h: Math.round(r.height),
              w: Math.round(r.width),
            });
          }
        }

        const fs = parseFloat(st.fontSize);
        if (fs && fs < minFont && el.children.length === 0) {
          const txt = (el.innerText || "").trim();
          if (txt.length > 3) out.smallText.push({ txt: txt.slice(0, 30), fs });
        }
      }
      return out;
    },
    { vw: vp.w, minTap: MIN_TAP, minFont: MIN_FONT }
  );

  await page.close();
  return result;
}

(async () => {
  const url = process.argv[2];
  const asJson = process.argv.includes("--json");
  if (!url) {
    console.error("usage: node audit.js <url> [--json]");
    process.exit(2);
  }

  const browser = await chromium.launch();
  const report = {};
  let blocking = 0;

  for (const vp of VIEWPORTS) {
    const r = await auditViewport(browser, url, vp);
    const hScroll = r.scrollWidth > r.clientWidth;
    const uniqTargets = [...new Map(r.smallTargets.map((s) => [s.txt + s.h, s])).values()];
    const uniqText = [...new Map(r.smallText.map((t) => [t.txt + t.fs, t])).values()];

    if (hScroll || r.overflow.length) blocking++;
    report[vp.n] = { hScroll, ...r, smallTargets: uniqTargets, smallText: uniqText };

    if (!asJson) {
      console.log(`\n=== ${vp.n} (${vp.w}px) ===`);
      console.log(
        `  horizontal scroll: ${hScroll ? `YES (+${r.scrollWidth - r.clientWidth}px)  [BLOCKING]` : "no"}`
      );
      console.log(`  unclipped overflow: ${r.overflow.length}${r.overflow.length ? "  [BLOCKING]" : ""}`);
      r.overflow.slice(0, 10).forEach((o) => console.log(`     +${o.over}px  <${o.tag}> .${o.cls}`));
      console.log(`  tap targets under ${MIN_TAP}px: ${uniqTargets.length}`);
      uniqTargets.slice(0, 10).forEach((s) => console.log(`     ${s.h}x${s.w}  "${s.txt}"`));
      console.log(`  text under ${MIN_FONT}px: ${uniqText.length}`);
      uniqText.slice(0, 10).forEach((t) => console.log(`     ${t.fs}px  "${t.txt}"`));
    }
  }

  await browser.close();
  if (asJson) console.log(JSON.stringify(report, null, 2));
  if (blocking) {
    console.error(`\nFAILED: ${blocking} viewport(s) have blocking mobile issues.`);
    process.exit(1);
  }
  console.log("\nPASSED: no blocking mobile issues.");
})();
