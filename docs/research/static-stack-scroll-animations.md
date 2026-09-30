# Which static stack best supports Apple-style scroll animations?

Research for [#2](https://github.com/cavallinilorenzo/street-lighting-predictive-maintenance/issues/2). Date: 2026-09-30.

Context: a single-page, static, English product landing site ("Smart Beam") in `site/`. It deploys to GitHub Pages through a GitHub Action and is served under `/street-lighting-predictive-maintenance/`. It needs sticky sections, parallax, image-sequence/scrubbed animations, reveal-on-scroll, good performance and reduced-motion support.

## Recommendation

- **Stack: Astro (static output, `site/` subfolder).**
- **Animation:** GSAP + ScrollTrigger drives the pinned, scrubbed and image-sequence sections. Plain CSS handles simple reveals and parallax (`position: sticky`, with native scroll-driven animations only as progressive enhancement). Leave Lenis out for now; it can be added later.
- **Reduced motion:** put every scroll effect behind `prefers-reduced-motion: no-preference` (`gsap.matchMedia()` in JS, `@media` in CSS). Users who prefer reduced motion get the static page, which stays fully readable.

## Findings

### Browser support of native CSS scroll-driven animations (today)

- `animation-timeline` (`scroll()` / `view()`) and `view-timeline` work in Chrome/Edge 115+ and Safari/iOS Safari 26+. **Firefox is "preview" only, not shipped in a release.** Source: MDN browser-compat-data, [`css/properties/animation-timeline.json`](https://github.com/mdn/browser-compat-data/blob/main/css/properties/animation-timeline.json), [`view-timeline.json`](https://github.com/mdn/browser-compat-data/blob/main/css/properties/view-timeline.json).
- The web-features entry `scroll-driven-animations` is **`baseline: false`** (Chrome 115, Safari 26, no Firefox). Source: [web-platform-dx/web-features `scroll-driven-animations.yml`](https://github.com/web-platform-dx/web-features/blob/main/features/scroll-driven-animations.yml).
- A caniuse page summary claimed Firefox 160 support. The raw BCD data above, which caniuse uses, does not confirm it, so treat Firefox as unsupported.
- For the model itself (`scroll()`, `view()`, `animation-range`) and the recommended `@supports` guard, see [MDN, CSS scroll-driven animations](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_scroll-driven_animations).
- Implication: native CSS works for **decorative, optional** effects (fade/slide reveals, subtle parallax) wrapped in `@supports (animation-timeline: view())`, and Firefox users simply see static content. It is **not** safe as the only engine for pinned or scrubbed sequences that carry the story.

### Animation libraries

| Library | Version (npm) | License | Fit |
|---|---|---|---|
| GSAP + ScrollTrigger | 3.15.0 | "Standard 'no charge' license" (not OSI open source) | Best for pin + scrub + snap + image sequences; works in all browsers |
| Motion (vanilla `scroll()`) | 13.4.6 | MIT | Lighter; uses native ScrollTimeline when possible; pinning via `position: sticky` |
| Lenis | 1.3.26 | MIT | Smooth scrolling only, not an animation engine |

- **GSAP licensing:** since 2025-04-30, all of GSAP is free for commercial use under the Standard "no charge" license, backed by Webflow. That includes the formerly paid plugins (ScrollTrigger, SplitText, MorphSVG). The only restriction is that it can't be used in no-code visual animation tools that compete with Webflow. Sources: [gsap.com/licensing](https://gsap.com/licensing/), [gsap.com/standard-license](https://gsap.com/standard-license), npm `gsap` license field. This is no problem for a marketing site, but note the license is proprietary, not MIT.
- **ScrollTrigger:** offers `pin` (with a pin-spacer), `scrub` (numeric smoothing, e.g. `scrub: 0.5`) and `snap` (to labels or increments). Current docs are v3.15. An image sequence is a scrubbed tween of a frame index drawn to a `<canvas>`. Source: [ScrollTrigger docs](https://gsap.com/docs/v3/Plugins/ScrollTrigger/). Responsive and reduced-motion conditions go through [`gsap.matchMedia()`](https://gsap.com/docs/v3/GSAP/gsap.matchMedia()).
- **Motion `scroll()`:** about 5.1 kB. It uses the ScrollTimeline API "where possible for optimal hardware-accelerated performance" and recommends pinning with `position: sticky`. Source: [motion.dev/docs/scroll](https://motion.dev/docs/scroll). It is MIT and supports vanilla JS, React and Vue ([motiondivision/motion](https://github.com/motiondivision/motion)). It is a valid lighter alternative if GSAP's non-OSI license is a concern, but it has fewer built-in tools for pinning, snapping and timeline orchestration.
- **Lenis:** MIT, integrates with ScrollTrigger (drive Lenis `raf` from the GSAP ticker and turn off lag smoothing), and respects `prefers-reduced-motion` by default. Caveats: CSS scroll-snap needs a plugin, nested scroll needs configuration, and Safari is capped at 60 fps. Source: [darkroomengineering/lenis](https://github.com/darkroomengineering/lenis). Apple's own site does not take over native scrolling, so Lenis is optional polish. Add it only if the scrubbed sections feel jittery.

### Stack options

**Astro (recommended)**
- Static output is the default. For project pages, the official GitHub Pages guide sets `site: 'https://cavallinilorenzo.github.io'` and `base: '/street-lighting-predictive-maintenance'`. Source: [Astro, Deploy to GitHub Pages](https://docs.astro.build/en/guides/deploy/github/).
- The official action `withastro/action@v6` has a `path` input for a project in a subfolder (here `site`), plus `node-version` (default 24), `package-manager` and `build-cmd`. It pairs with `actions/deploy-pages`. Source: [withastro/action](https://github.com/withastro/action). Commit the lockfile.
- Image optimization is built in and runs at build time (`<Image>`/`<Picture>` from `astro:assets`). It produces AVIF/WebP and responsive `srcset`/`sizes`, sets `loading="lazy"` and `decoding="async"` by default, and adds width/height to prevent CLS. No server is needed. Source: [Astro, Images](https://docs.astro.build/en/guides/images/). This matters a lot here because the site is full of screenshots and mockups.
- Astro ships no JS by default. GSAP is loaded only through a `<script>` in the components that need it. Components and layouts help organize a page with many sections. Current version: 7.3.5 (npm).
- Base path: assets imported through Astro and `import.meta.env.BASE_URL` resolve correctly. Hand-written absolute URLs (`/img/x.png`) must be prefixed with the base.

**Plain HTML/CSS/JS (optionally with Vite)**
- It can run with no tooling at all: GitHub Pages can publish a folder directly via `actions/upload-pages-artifact` with `path: site`. The base path is not a problem if all URLs are relative.
- It gives up build-time image optimization (AVIF/WebP and `srcset` must be done by hand), components/partials, and bundling of GSAP (CDN or a vendored file instead). Adding Vite (`base` option; [Vite static deploy guide](https://vite.dev/guide/static-deploy#github-pages)) closes part of the gap, but at that tooling cost Astro gives more.

**Next.js static export**
- `output: 'export'` produces `out/`, and GitHub Pages is supported through an official template. Source: [Next.js, Static exports](https://nextjs.org/docs/app/guides/static-exports) (v16.3.7).
- The default `next/image` optimization is **not supported** in static export: it needs a custom loader, an external service, or `unoptimized`. `basePath` must also be configured. React hydration adds a runtime to a page that is almost entirely static content. The scroll animations would still be written imperatively (GSAP/Motion in `useEffect`), so React adds weight without making them easier. Only worth it if the team specifically wants React.

### Reduced motion

- `prefers-reduced-motion` has been Baseline widely available since January 2020. MDN recommends replacing motion with gentler alternatives (such as opacity changes) instead of just removing the feedback. Source: [MDN, prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion).
- Pattern:
  - Build the page so the no-JS / reduced-motion state is the complete, readable layout.
  - Register ScrollTrigger pins and scrubs only inside `gsap.matchMedia({ "(prefers-reduced-motion: no-preference)": ... })`.
  - Wrap CSS scroll-driven rules in both `@supports (animation-timeline: view())` and `@media (prefers-reduced-motion: no-preference)`.
  - For image sequences under reduced motion, show one representative frame (a poster).

## Trade-offs summary

- **Astro + GSAP:** the most capable option with the best image pipeline. Costs a Node build step and an animation license that is free but not OSI open source.
- **Native CSS only:** no JS and runs off the main thread, but Firefox doesn't support it (not Baseline) and it can't reliably coordinate pins, scrubs and sequences.
- **Motion instead of GSAP:** MIT, smaller and uses native acceleration, but has fewer tools for complex pinned timelines.
- **Next export:** the heaviest runtime and the weakest static image support, with no benefit for this page.
