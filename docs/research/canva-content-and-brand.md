# What content and brand assets does the Canva presentation already provide?

Research for issue #3. Question: what can a new English, Apple-style product landing site (audience: municipalities and utilities) reuse from the Smart Beam Canva deck, and what is missing?

## Sources and access

| Source | How it was read | Access |
|---|---|---|
| Canva deck `https://canva.link/xd7wuplr4kh79ne` → design `DAHBtGrvjT4`, title "Hackathon Uni 2 - Sister SmartBeam", 11 slides at 1920×1080 | Canva MCP (`resolve-shortlink`, then `read-design` for metadata, text content, presenter notes and page thumbnails) | Full text and thumbnails. Read-only. The design was not edited, copied or commented on. |
| `README.md` (repo root, `main` @ 77079eb) | Read directly | Full |
| `docs/agents/team.md` | Read directly | Full |
| `core/static/core/favicon.png` | Read directly, pixels sampled | Full |

**What I could not get:**
- **Exact font names and exact colour hex values.** These only come from structured element data, and that needs an editing transaction (`open_transaction`). I skipped it to keep the work read-only. The hex values below come from sampling pixels in the 596×335 thumbnails, so treat them as approximate (±a few units, and gradients are sampled at their ends).
- **Image asset IDs, licences and originals.** `get-assets` needs element IDs, which also come from the transaction path. So I don't know if the photos are Canva stock (licence limits) or uploads.
- **Presenter notes.** All 11 slides have empty notes, so there is no hidden script.

## The deck, slide by slide

All slide text is in **Italian**. Every slide except 3 has the SIS.TER logo top-left.

| # | Slide | Content (translated summary) |
|---|---|---|
| 1 | Cover | "SMARTBEAM" wordmark. SIS.TER logo ("Connecting Knowledge"). Team: Benassi Matteo, Cavallini Lorenzo, Trentin Simone. "Challenge #1", "Hackaton 02/2026". |
| 2 | Pitch agenda | "Predictive maintenance system for public lighting. From MVP validation on **2,500 simulated nodes in Rome** to economic and operational impact." Agenda: 01 Project introduction, 02 Core business & MVP architecture, 03 Live demo: predictive dashboard, 04 Next features. |
| 3 | Challenge brief | Screenshot of the SIS-TER Srl SB brief "Challenge n°1 – Previsione guasti". **Context:** reactive vs scheduled maintenance, and how scheduled maintenance cuts cost and disruption. **Objectives:** failure-prediction algorithm from maintenance history plus physical features; monitoring dashboard with fault tracking/reporting; priority scale to schedule work across the year. **Data:** a CSV of street-light fixtures with activity period and fault/intervention records. |
| 4 | "Il paradigma predittivo" (label: MVP validation) | **Today, reactive maintenance:** fix-after-failure, logistical inefficiency, unpredictable operating costs. **Solution, machine learning:** analyse maintenance history, predict failure date and probability, optimise resources ahead of time. Images: Rome street lamp with St Peter's dome, and an abstract neural-network graphic. |
| 5 | "Pipeline predittiva" (MVP architecture) | Three columns. **Data ingestion:** 2,500 simulated nodes (Rome), maintenance history, wear and life-cycle variables. **ML engine:** prediction algorithms, degradation-pattern analysis, continuous training on historical logs. **Predictive output:** estimated failure date, failure probability, sync with dashboard and map. |
| 6 | "Vediamolo all'opera" | Live-demo divider. No screenshots of the web app. |
| 7 | "Prossime features" | Two roadmap cards: **Prescriptive AI & root-cause analysis** and **AI fleet routing & clustering** (details on slides 8 and 9). |
| 8 | Prescriptive AI & root-cause analysis | Root-cause inference (e.g. recurring voltage spikes across a neighbourhood). Next-best-action (example: "Don't just change the lamp, replace the transformer (confidence 92%)"). ROI: removes repeat interventions, "asset life extended by **over 3 years**". |
| 9 | AI fleet routing & clustering | Clusters real faults together with predicted "red-risk" lights in the same area. Auto-generates optimal routes for maintenance vans. ROI: lower fuel and travel-hour costs, higher daily resolution rate. |
| 10 | "Smart routing in azione" (demo) | Mock-up of a mobile technician app on a phone: day cards ("15/3/26: 12 interventi", "Critici: 5 / Preventivi: 7") and a cyan "Genera percorso" button. Copy: unified view of the shift (critical plus preventive jobs), one-click route generation. |
| 11 | "Grazie!" | Same layout as the cover. |

## Mapping to the landing-site narrative

| Landing section | In the deck? | In README? | Notes |
|---|---|---|---|
| Problem | Yes (slides 3–4): reactive maintenance, logistical inefficiency, unpredictable costs | Yes (reactive → proactive) | Short. Needs English copy framed for municipalities. |
| Solution | Yes (slides 4–5) | Yes (60-day failure probability plus remaining lifetime) | README is more precise. Use README wording. |
| Features | Partly: the pipeline outputs "dashboard and map" only | **Yes, fully:** interactive risk map, analytics dashboard, explainable AI, PDF reports, field fault reporting, three risk levels | README is the source for shipped features. |
| Roadmap / vision | **Yes:** prescriptive AI, fleet routing, mobile technician app mock-up | No | Only present in the deck. It is **not built**, so the site must label it "coming next". |
| Models | Only generic ("prediction algorithms, degradation patterns") | **Yes:** HistGradientBoostingClassifier (60-day risk, class-balanced) plus XGBoost AFT survival model (remaining life, right-censored), and the four input features | Use README. |
| Results | **No measured results.** Only scale (2,500 simulated nodes) and projected ROI claims | No metrics either | Biggest gap. |
| Team | Full names and hackathon context (SCIoTeM / SIS.TER Challenge #1, 02/2026) | Hackathon name only | Name↔GitHub handle mapping is not stated anywhere (team.md has handles only). |

## Key numbers and claims (with caveats)

| Claim | Source | Status |
|---|---|---|
| 2,500 simulated nodes (Rome) | Deck slides 2, 5, 7 | MVP validation scale. The deck says "simulated". The site should state it that way. |
| Failure probability within **60 days** | README | Implemented. Not in the deck. |
| Risk bands: Optimal < 25%, Warning 25–70%, Critical > 70% | README | Implemented. Not in the deck. |
| Asset life extended by "+3 years" / "over 3 years" | Deck slides 7, 8 | **Projection for an unbuilt feature**, with no supporting data. Risky in front of a municipal audience. Omit, or mark clearly as a target. |
| "Confidence: 92%" | Deck slide 8 | An **illustrative example** of AI output, not a model metric. Do not present it as accuracy. |
| Cuts fuel and travel-hour costs, higher daily resolution rate | Deck slide 9 | Qualitative only, and for an unbuilt feature. |

There are no model evaluation metrics (AUC, precision/recall, C-index, MAE on remaining life) in either the deck or the README.

## Brand assets

### Logo
- **No Smart Beam logo in the deck.** "SMARTBEAM" appears only as large typeset text (a heavy sans in a navy-to-periwinkle gradient).
- The only logo in the deck is **SIS.TER** ("Connecting Knowledge"), the challenge sponsor/organiser. It is a third-party mark and **must not** be used as Smart Beam branding.
- **Candidate from the repo:** `core/static/core/favicon.png` (697×697 RGBA). It shows a street lamp with a warm glow and a gear-and-wrench, on a navy circle (≈ `#0F274D`), with steel-blue and amber accents. It is an illustration, not a vector wordmark. For an Apple-style site it would need an SVG redraw or simplification.

### Colour palette (approximate, sampled from thumbnails)

| Role | Hex (≈) | Where |
|---|---|---|
| Deep navy (gradient start, headline top) | `#0F1A50` / `#1A245D` | Content panels, headline tops |
| Indigo mid | `#2F3778` / `#42478E` | Headline gradient middle |
| Periwinkle (gradient end) | `#5A5EAF` / `#6A6CC2` | Headline bottoms, panel bottoms |
| Ice background | `#E8F3F6` | Main slide background |
| Sky tint | `#CAE7FA` / `#D3EBF9` | Soft light-blue background shards |
| White | `#FFFFFF` | Cards, pills |
| Cyan accent | `#41E9FB` | Phone mock-up highlight and button (slide 10) |
| Near-black device | `#15141D` | Phone mock-up |
| SIS.TER blue / magenta | `#133B74` / `#BE1557` | Sponsor logo only. Not Smart Beam brand. |
| Favicon navy | `#0F274D` | Repo favicon |

Overall look: a light, airy ice-blue background with navy→periwinkle gradients and rounded pill buttons. That fits an Apple-style site well. Risk colours (green/amber/red) come only from the README emoji and are not defined as brand colours.

### Fonts
Not confirmed (see access limits). Visually:
- Headlines are a heavy, tightly tracked uppercase grotesk.
- Body text is a light neo-grotesk.
- Slide 3 (the sponsor's brief) uses a different serif/sans. It is a screenshot.

There is no licensed font file or name to reuse. An Apple-style site would normally use the system stack (SF Pro via `-apple-system`) or Inter anyway.

### Images and illustrations

| Image | Slide | Reusable? |
|---|---|---|
| Night photo of a street lamp with St Peter's dome, Rome | 4 | Probably Canva stock. Licence unknown. Very Rome-specific. |
| Abstract blue neural-network graphic | 4 | Probably Canva stock. Generic "AI" cliché. |
| Phone mock-up of the technician routing app | 10 | A Smart Beam design idea. Useful as a roadmap visual, but it is a low-res mock-up of an **unbuilt** feature. |
| Screenshot of the SIS-TER challenge brief | 3 | Not reusable (third-party document). |
| Soft geometric light-blue background shards | all | Decorative. Easy to recreate in CSS. |

There are **no screenshots of the actual web app** (map, dashboard, asset detail, PDF report). The demo was live.

## What exists vs what is missing

**Exists (reusable):**
- Problem → solution framing (reactive → predictive), in Italian.
- A three-step pipeline story (data ingestion → ML engine → predictive output).
- A roadmap/vision with two well-described next features and a mobile mock-up.
- The "2,500 simulated nodes (Rome)" validation scale.
- Team full names and the hackathon context.
- A coherent visual direction: ice-blue plus navy→periwinkle gradient, pill UI, bold uppercase headlines.
- From the README: the precise feature list, risk bands, 60-day horizon, model descriptions and tech stack.
- From the repo: a lamp/gear favicon that could serve as a logo mark.

**Missing:**
1. English copy. The deck is entirely Italian, so the landing text must be written, using the README for technical accuracy.
2. A proper Smart Beam logo (vector wordmark plus mark). Only the raster favicon exists.
3. Confirmed brand tokens: exact hex values and font names. There is no brand kit, only sampled values.
4. Measured results: model metrics, backtests, or before/after operational numbers. The "+3 years" and "92%" figures are unsupported projections or examples.
5. Product screenshots or visuals of the real app (map, dashboard, asset page, PDF).
6. Rights-cleared imagery. The deck photos have unknown licences.
7. Audience-specific content for municipalities/utilities: pricing or pilot offer, data requirements and integration, privacy/GDPR, a contact/CTA, and case studies or testimonials.
8. Team roles and photos, and the mapping of deck names to GitHub handles (itsmrma, cavallinilorenzo, TrentoElProgrammatores).
9. A clear split on the site between **shipped** features (README) and **vision** features (deck slides 7–10).
