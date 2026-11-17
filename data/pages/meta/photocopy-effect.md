---
section: Meta
toc: true
toc_depth: 3
date: 22/09/2026
---

# The photocopy effect

_Retired from the live site in the bare-bones pass. Kept here as a build
note, in case future me wants it back — the CSS and the filter markup below
no longer exist in `docs/css/prototype.css` or `data/includes/header.html`._

A few things on this site — the logo mark, the `h1`/`h2` headings, and the
hairline rules that frame the columns — used to be pushed through an SVG
filter before they reached the screen. The filter degraded them the way a
few generations through a photocopier degrades a page: the edges wobbled,
small marks dropped out, ink bled where it survived, and a layer of toner
grain sat over the top.

## Why

I wanted the handful of elements that carried the most weight on the page —
the mark, the headings, the frame lines — to look like they'd come off a
photocopier: ink on paper rather than pixels on glass, handled rather than
rendered. Everything else on the page was drawn clean, straight vector edges
and flat fill, which is what made the contrast work.

## How it works

The effect was one SVG filter, `#f-photocopy`, defined once near the top of
`<body>` in the page header include and referenced from CSS wherever it was
needed. It ran in four stages, each one built from a `feTurbulence` noise
field and a threshold that turned the smooth noise into a hard yes/no mask.

1. **Warp.** A low-frequency turbulence field displaces the whole source graphic by a few pixels with `feDisplacementMap`. This is the page waviness — the sense that the original sheet wasn't sitting flat under the glass.
2. **Dropout.** A second, higher-frequency turbulence field is run through `feColorMatrix` to turn it into a mask: alpha = 14 × R − 2.8, so anything where the noise channel falls below about 0.2 becomes fully transparent. Composited against the warped graphic with `operator="in"`, this eats small chunks out of thin strokes — toner running out.
3. **Bleed.** The eaten result is blurred, then pushed back through another `feColorMatrix` threshold: alpha = 22 × a − 8.8, so the cut lands at 40% alpha. Anything that doesn't keep at least that much opacity through the blur is erased outright, and everything that survives is pushed back towards full black. This is what gives surviving edges their soft, bled-ink look instead of just a blur.
4. **Grain.** A final high-frequency field, thresholded the same way as the dropout stage, punches a fine speckle out of what's left — the toner texture.

### One filter, two resolutions

The bleed stage only works if the blur it depends on actually runs.
Chrome approximates `feGaussianBlur` with box blurs sized in *device*
pixels, and a box size under 1 device pixel is the identity — it does
nothing. A blur radius tuned to look right at 2x (retina) is invisible at
1x, because the same CSS-pixel radius is half the device pixels there.

Rather than one compromise setting, there are two complete filters:
`#f-photocopy`, tuned for high-density screens, and `#f-photocopy-1x`, which
doubles every spatial value (warp scale, blur radius, noise frequency) and
softens the two hard alpha thresholds into gentler ramps, so partial-alpha
pixels stand in for the fine detail a coarser raster can't resolve. A media
query picks between them:

```css
:root {
    --photocopy: url(#f-photocopy-1x);
    --rule-filter: var(--photocopy);
}

@media (min-resolution: 1.5dppx), (-webkit-min-device-pixel-ratio: 1.5) {
    :root {
        --photocopy: url(#f-photocopy);
        --rule-filter: var(--photocopy);
    }
}
```

`--rule-filter` is kept as a separate variable from `--photocopy`, even
though it points at the same thing, because it's also the off switch for
the page rules alone — set it to `none` and the hairlines go back to being
clean lines while the logo and headings keep the effect.

### Where it was applied

Two CSS patterns covered every use on the site.

**Text and the logo** take the filter directly, because a filter on an
element with no children of its own can't drag anything unwanted through
it:

```css
.ink-copy { filter: var(--photocopy); }

h2 { filter: var(--photocopy); /* plus its other type rules */ }
```

**Borders** never take the filter directly, because a filter applies to an
element *and everything inside it* — put it on a box that contains text and
the warp and dropout stages eat the words along with the border. Instead
the border is drawn on a pseudo-element with nothing inside it:

```css
.ink-frame { position: relative; }

.ink-frame::before {
    content: "";
    position: absolute;
    inset: 0;
    border: 4px solid currentColor;
    pointer-events: none;
    filter: var(--photocopy);
}
```

This is the pattern the page's own hairline rules use, just drawn as a
dedicated element (`.rule-h`, and the vertical rules on `.row::before` /
`.row::after`) rather than a pseudo-element on a content box, since those
rules aren't boxes to begin with.

### Two things that catch people out

The filter was defined inside an `<svg>` sitting at the top of `<body>`,
sized `width="0" height="0"` and positioned absolutely so it took up no
space. That `<svg>` had to actually be in the DOM and must not be
`display: none` — some browser engines drop the whole filter graph if its
host isn't rendered, even though nothing about the filter is visible on its
own.

The other trap was alpha. The bleed stage thresholded at 40% opacity
*before* anything else happened to the colour, so anything drawn at less
than full opacity — a translucent rule colour, for instance — could already
be under the cut before the filter even started, and got erased outright
rather than just faded. Whatever fed this filter had to be opaque.
