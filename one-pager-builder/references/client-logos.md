# Client Logos

Solum client logos pulled from getsolum.com. Use in the "Trusted By" strip to build trust. Always match 6–7 logos to the prospect's vertical.

Download into `<output-folder>/client-logos/`. Chrome handles AVIF natively.

## Vertical → logo picks

### PT / Rehab prospects
Lead with Rise PT (direct peer). Then compatible therapy brands.
- `rise-pt.avif` — Rise Physical Therapy (PT, multi-location)
- `bespoke.avif` — Bespoke Treatments (PT)
- `golden-hand.avif` — Golden Hand Therapy (hand therapy)
- `akp.avif` — Always Keep Progressing (multi-therapy)
- `brighter-strides.avif` — Brighter Strides (pediatric therapy)
- `hi5-aba.avif` — Hi5 ABA (scale proof)
- `slea.avif` — SLEA Therapies (multi-therapy)

### ABA / BH prospects
Lead with large ABA names.
- `hi5-aba.avif` — Hi5 ABA
- `golden-steps.avif` — Golden Steps ABA
- `blossom.avif` — Blossom ABA Therapy
- `my-team-aba.avif` — My Team ABA
- `supportive-care.avif` — Supportive Care ABA
- `by-your-side.avif` — By Your Side AC
- `sky-care.avif` — Sky Care ABA

### Speech / OT / multi-therapy prospects
- `slea.avif` — SLEA Therapies
- `cbs.avif` — CBS Therapy
- `brighter-strides.avif` — Brighter Strides
- `akp.avif` — Always Keep Progressing
- `bespoke.avif` — Bespoke Treatments

## URLs (CDN)

All hosted at `https://cdn.prod.website-files.com/66ccf770fcc17846279d79cd/`.

```
6945c1bab53542e20f2b56c9_Rise-Physical-Therapy-NWA-solum.avif   rise-pt.avif
6945c1b9c56999a9c717f891_bespoke-treatments-solum.avif         bespoke.avif
6945c1b95c02869be18de9f3_golden-ghand-therapy-solum.avif       golden-hand.avif
6945c1b91432a333a24a074f_always-keep-progressing-solum.avif    akp.avif
6945c1ba5963fb8867602d17_brighter-strides-solum.avif           brighter-strides.avif
6945c1b925fc43ab7aa4b040_hi5-aba-solum.avif                    hi5-aba.avif
6945c1baef54ee49dcefd0a0_slea-therapies-solum.avif             slea.avif
6945c1ba30d52893f5cc4ad1_golden-steps-aba-solum.avif           golden-steps.avif
6945c1b9d8fe62fe943804cc_Blossom-ABA-Therapy-solum.avif        blossom.avif
6945c1b91be018e7643f23b9_My-Team-ABA-solum.avif                my-team-aba.avif
6945c1ba0af943e105a80c4a_supportive-care-aba-solum-1.avif      supportive-care.avif
6945c1b9d4dfc5320cd3c6af_by-your-side-ac-solum.avif            by-your-side.avif
6945c1b9176cf26e9ca2b364_cbs-therapy-solum.avif                cbs.avif
6945c1bbbf5cc74986e908fc_sky-care-aba-solum.avif               sky-care.avif
```

## Fresh fetch

If the CDN paths change, re-run discovery:

```bash
B=~/.claude/skills/gstack/browse/dist/browse
$B goto https://getsolum.com
$B js "Array.from(document.querySelectorAll('img')).map(i=>({alt:i.alt,src:i.src})).filter(i=>i.alt && i.alt.includes('Solum Health'))"
```

## SolumHealth wordmark

Copy into output folder as `logo-solumhealth-dark.svg`:
```
/Users/juanmontoya/Documents/Claude/landing-page/logo-solumhealth-dark.svg
```

For navy-background variants, use:
```
/Users/juanmontoya/Documents/Claude/landing-page/logo-solumhealth-white.svg
```

## Display style

Grayscale + slight transparency so logos read as supporting evidence, not as a partner showcase:

```css
.trust .logos img {
  height: 26px;
  width: auto;
  max-width: 90px;
  object-fit: contain;
  filter: grayscale(100%) opacity(0.78);
}
```
