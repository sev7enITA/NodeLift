# Public showcase QA — NodeLift 0.2.1

31 October 2026. This record concerns the static public showcase, not the private control room, engine performance or physical companion qualification. The atlas snapshot contains 55 projects across six categories.

## Functional browser checks

A separate Chrome QA tab exercised the actual JSON-backed interface through the browser UI:

- All 16 individual category, ecosystem/provenance and capability-tag options returned the exact dataset counts.
- All 144 combinations of six categories, four provenances and six explicit tags returned the exact intersection counts, including empty intersections.
- Search by project, multiple terms, deliberate no-result input and both reset controls behaved correctly.
- Six pages exposed all 55 project names in dataset order, without duplicates; forward/back navigation and reset to the first page passed.
- All 55 project dialogs were opened. Each displayed all 18 descriptive fields and exactly the canonical source labels and URLs.
- An English direct link restored category/tag filters and opened InferRing. Keyboard focus stayed in the modal; Escape closed it while retaining the five matching results.
- The table exposes nine column headers with column scope and named project row headers with row scope. This is a semantic inspection, not a complete screen-reader certification.
- Italian/English switching, architecture steps, presentation navigation and Escape exit were observed. The deck starts at chapter 01.

JavaScript syntax, unique IDs, DOM references, anchors, JSON-LD and local dependencies passed static checks. All nine linked local assets/downloads resolved and matched their on-disk bytes. No external script, font, image service or tracking dependency is required.

## Print scope and recovery

The print appendix builder was exercised independently with the real dataset: 55 projects, 18 fields per project and exact source URLs. Idempotent cleanup and the print-media guard passed focused logic checks.

Native print-preview automation did not complete reliably in either Chrome or the evaluator's in-app browser. The print request prepared the full table but blocked automation; Escape targeted at page content did not establish a completed print/cancel lifecycle. The implementer closed only its own QA tab. No rendered PDF, page count or final print layout is claimed as verified.

Recovery now listens for afterprint, leaving print media, restored window focus/pageshow, the next page pointer action and return from the print call. These paths restore filtered pagination and remove the temporary appendix. The original filter values are retained.

## Independent viewport observations

The first-round evaluator captured actual in-app-browser views at 1440×1000, 768×1024 and 375×812. Captures covered the desktop chapters, tablet hero/atlas and mobile hero, architecture, evidence/chart, atlas and project detail. These were followed by the authoritative post-refinement captures listed below. Viewport checks do not constitute physical-device testing.

## Targeted review refinements

The first actual Gemini 4 Argon / Alta design review passed the rubric with required refinements. The independent evaluator adjudicated its findings; the implementation preserved the visual direction and applied the accepted changes:

- Meaningful labels/status use a 10–11 px floor; mobile research values and dialog text use approximately 13 px. Several changed text/background pairs were calculated at 7.4:1–11.0:1 contrast. This is not an exhaustive contrast audit.
- Opaque masthead, adjusted return connection, backed diagram captions and a centered output arrow reduce visual collisions.
- Tablet print access remains visible. The DOM contains all four architecture descriptions for print, independent of the selected interactive step; schematic print surfaces use white fills.
- Deck controls start with explicit pressed state, preserve commanded chapter indices through intermediate smooth-scroll frames and restore focus to the current chapter heading on exit.
- Category/provenance/tag control labels are localized while canonical research text and stored codes remain unchanged. The page explains that tags do not establish physical-device qualification.
- The table includes a visible continuation fade, keyboard horizontal scrolling and evidence as the fourth column. Pagination returns to the filters beneath the header. Hero and closing resources provide evidence/atlas shortcuts.

Post-change browser observations confirmed rapid right/right/right/left navigation ending at chapter 03; Escape focused the architecture heading without a footer jump. Mixed Italian/English anchor history restored the correct language, control labels and search placeholder on back/forward. Keyboard ArrowRight moved the matrix 40 px. Pagination left the filters below the opaque header. The four print descriptions were present in the DOM. Updated MindSpore, LiteRT-LM and ExecuTorch dialogs matched their final canonical fields and source URLs.

## Final external disposition

**Round 2: PASS.** The actual Google Gemini follow-up used the observed **Argon / Alta (Gemini 4)** selector and completed with: “PASS — No mandatory web-publication fixes remain.” The separate evaluator accepted that disposition and scored design, originality, craft and functionality at **2/3 each**. The provider's perfect scores were not adopted as evidence of flawless execution.

The reviewer received the current public source/QA bundle and eight newly captured screenshots. It reviewed those attachments and supporting QA; it did not execute the site or test physical phones. The all-project/filter checks above remain implementation-agent observations, not tests performed by Gemini.

Authoritative round-2 captures:

- Desktop, 1440×1000: hero, architecture and atlas.
- Tablet, 768×1024: architecture.
- Mobile, 375×812: hero, chart, atlas and project detail.

These were explicit document-clip captures matching the observed CSS viewports. Earlier exploratory captures that scaled the browser canvas were superseded. Some document clips cropped the fixed header's upper edge; separate DOM readback confirmed top zero, no transform and opaque RGB(7,18,23). No image retouching or reconstruction was used. The evaluator also checked mobile-dialog Escape behavior, tablet print-control visibility and DOM containment.

The evaluator found no mandatory web-publication fix and requested no third design round. Two optional polish items remain: a decorative tablet grid extended the document by 7 px without clipping content, and the compact print summary omits the fourth evidence column while the complete appendix retains it. Native PDF rendering/pagination remains **unverified** and outside the web-release verdict. No further blocking print attempt was made after the refinements.

## Final snapshot and review provenance

Current public source SHA-256 values:

- `site/NodeLift/index.html`: `8cd73f729e72116fef310d77a9cc69442a7b0da7adf29a0b27777a9ad424d174`
- `site/NodeLift/assets/showcase.css`: `4125213947b807639d86d4f37fcf4600b1919c748eab64cdff2dce75da932748`
- `site/NodeLift/assets/showcase.js`: `b6c356c8eb926a3b56404438bcceeac9c9b6872a9b3e95ee2814e3374d610672`
- `site/NodeLift/data/comparison.json`: `d3f3d69319b5947e91aaddd8c32b7b81a131073a6337457ed8b037c7172d769e`

External-review artifact identities (completed 31 October 2026):

- Submitted public source/QA bundle `review-source-2.txt`: `d33b42e678f341dd15b0fb79c22b875e7976a104ca2cbba98c83a4c7a667fb4d`.
- Completed response `gemini-showcase-review-2.txt`: `29237d69a9c6948d056404e55dd7278a87757ab9aed247da1e5de2540cce4485`.
- Attachment manifest `external-review-provenance-2.json`: `d3c56a1eb69af305e57b45f0932ac3e2a8b270b2844b6b4ba78a9ca268c8116a`. It records the source bundle and eight screenshot hashes.
- Detailed functional observations and exact review artifacts were retained by the orchestrator. Private model conversation URLs are intentionally excluded.

No speedup, environmental saving, engine improvement or production-readiness claim follows from these UI checks.
