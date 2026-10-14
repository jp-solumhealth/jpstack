# Client Logos

Use your own customers' logos in the "Trusted By" strip. Always match 6 to 7 logos to the prospect's vertical, and only name customers who have given permission.

Keep the list itself (vertical, customer, logo URL) in a private file, e.g. `~/.claude/private/client-logos.md`, not in this public repo.

Download into `<output-folder>/client-logos/`. Chrome handles AVIF natively.

## Vertical → logo picks

Group your customers by vertical (e.g. PT / Rehab, ABA / BH, Speech / OT) and lead with the closest peer to the prospect, then compatible brands.

## Fresh fetch

If your logos live on your website, list them with the gstack browser:

```bash
B=~/.claude/skills/gstack/browse/dist/browse
$B goto https://your-site.com
$B js "Array.from(document.querySelectorAll('img')).map(i=>({alt:i.alt,src:i.src}))"
```

## Wordmark

Copy your dark and white wordmark SVGs into the output folder as `logo-dark.svg` / `logo-white.svg`.

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
