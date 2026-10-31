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

The separate design evaluator captured actual in-app-browser views at 1440×1000, 768×1024 and 375×812. Captures cover the desktop chapters, tablet hero/atlas and mobile hero, architecture, evidence/chart, atlas and project detail. The evaluator reported no root horizontal overflow at 1440 and 375 pixels and observed mobile-dialog opening and Escape closing. These viewport checks do not constitute physical-device testing.

The final external design disposition and any requested refinements are tracked separately by the orchestrator. No final external approval is asserted in this checkpoint.

## Targeted review refinements

The first actual Gemini 4 Argon / Alta design review passed the rubric with required refinements. The independent evaluator adjudicated its findings; the implementation preserved the visual direction and applied the accepted changes:

- Meaningful labels/status use a 10–11 px floor; mobile research values and dialog text use approximately 13 px. Several changed text/background pairs were calculated at 7.4:1–11.0:1 contrast. This is not an exhaustive contrast audit.
- Opaque masthead, adjusted return connection, backed diagram captions and a centered output arrow reduce visual collisions.
- Tablet print access remains visible. The DOM contains all four architecture descriptions for print, independent of the selected interactive step; schematic print surfaces use white fills.
- Deck controls start with explicit pressed state, preserve commanded chapter indices through intermediate smooth-scroll frames and restore focus to the current chapter heading on exit.
- Category/provenance/tag control labels are localized while canonical research text and stored codes remain unchanged. The page explains that tags do not establish physical-device qualification.
- The table includes a visible continuation fade, keyboard horizontal scrolling and evidence as the fourth column. Pagination returns to the filters beneath the header. Hero and closing resources provide evidence/atlas shortcuts.

Post-change browser observations confirmed rapid right/right/right/left navigation ending at chapter 03; Escape focused the architecture heading without a footer jump. Mixed Italian/English anchor history restored the correct language, control labels and search placeholder on back/forward. Keyboard ArrowRight moved the matrix 40 px. Pagination left the filters below the opaque header. The four print descriptions were present in the DOM. Updated MindSpore, LiteRT-LM and ExecuTorch dialogs matched their final canonical fields and source URLs.

The follow-up external visual disposition is pending at this checkpoint. Earlier viewport captures are not presented as post-refinement screenshots. Native PDF preview remains unqualified; no second blocking print attempt was made after the refinements.

## Snapshot

- Dataset SHA-256: `d3f3d69319b5947e91aaddd8c32b7b81a131073a6337457ed8b037c7172d769e`
- Showcase JavaScript SHA-256 after targeted refinements: `b6c356c8eb926a3b56404438bcceeac9c9b6872a9b3e95ee2814e3374d610672`
- Detailed functional observations were retained in the task's review artifacts.

No speedup, environmental saving, engine improvement or production-readiness claim follows from these UI checks.
