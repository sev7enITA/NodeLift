# Showcase publication record

Published 31 October 2026: **https://www.fabriziodegni.com/NodeLift/**.

## Current status

The nine-chapter Italian/English showcase and the 55-entry comparison atlas are live. At **2026-10-31 22:10:44 UTC**, anonymous requests returned HTTP 200 for all **12 files**, with every byte count and SHA-256 matching the frozen publication manifest. The path without a trailing slash resolves to the canonical `/NodeLift/` URL.

The earlier File Manager HTTP 403 was resolved after the owner reopened working access. The reviewed archive was uploaded and extracted outside `public_html`; the new `NodeLift` directory was then moved into `public_html`. There was no existing NodeLift folder to replace. No permissions, security settings, root `.htaccess`, portfolio root files or unrelated project files were changed. FileZilla/FTP was available as the owner's alternative but was not needed.

## Frozen payload and readback

- Source commit: [`659477656bad3de2317032913a0ee11533609d95`](https://github.com/sev7enITA/NodeLift/commit/659477656bad3de2317032913a0ee11533609d95).
- Archive: `NodeLift-showcase-eaa8665678af.zip`, 1,111,197 bytes.
- Archive SHA-256: `8c41f34fdc37385456ce4b1fdc8dcd051436ee756784d38752a940a4af48860d`.
- [Deployment manifest](evidence/showcase-2026-10-31/deployment-manifest.json): all public file sizes and hashes.
- [Anonymous live verification](evidence/showcase-2026-10-31/live-verification.json): all 12 files match; canonical path passes.
- [Source commit CI](https://github.com/sev7enITA/NodeLift/actions/runs/41246259325): passed. CI is not a physical-device performance qualification.

The live browser loaded all 55 entries. Searching `DistAI` produced one result; its complete 18-field dialog and primary-source links opened correctly. Reset restored the atlas; English and Italian navigation switched correctly. All linked local exports were included in the 12-file HTTP/hash verification. The original hero emblem loaded on the public page.

[Live desktop capture](evidence/showcase-2026-10-31/live-desktop.jpg), [live mobile viewport capture](evidence/showcase-2026-10-31/live-mobile.jpg) and [browser verification manifest](evidence/showcase-2026-10-31/browser-verification.json) record the deployed page. Desktop used the normal 1685×950 viewport; mobile used 375×812 and showed no horizontal document overflow. The temporary viewport override was reset after capture. These images were not retouched.

Actual Gemini 4 Argon/Alta design review passed on round 2 after refinements, using fresh desktop, tablet and mobile viewport screenshots. See [SHOWCASE_QA.md](SHOWCASE_QA.md). Browser viewport checks do not establish physical-device qualification. The final rendered Print/PDF output remains visually unverified; the web presentation is the delivered artifact.

## Scoped payload

- Public source: `site/NodeLift/` only.
- Regenerate comparison exports: `python3 scripts/export_comparison.py`.
- Package reviewed files: `python3 scripts/package_showcase.py`.
- The packager records every file's size/SHA-256 and creates an archive containing only the top-level `NodeLift/` folder under ignored `artifacts/showcase/`.
- UI/source checks: [SHOWCASE_QA.md](SHOWCASE_QA.md).

## Repeating a scoped publication

1. Open the File Manager for the existing fabriziodegni.com website. Confirm the target directory; NodeLift now exists and must be preserved before a replacement.
2. Keep the deployment archive and replacement backup outside `public_html`. Extract the reviewed archive to a private staging location, preserve the previous NodeLift folder, then move the new `NodeLift` folder into `public_html`.
3. Do not replace the portfolio root, run the whole-portfolio packager, change root `.htaccess`, or delete unrelated files.
4. Run `python3 scripts/verify_showcase.py`. It anonymously requests every manifest file with cache bypass and checks exact hashes and the `/NodeLift` → `/NodeLift/` canonical path.
5. Reopen the live page and verify narrative, matrix, filtering, one complete project dialog and download links. Update this record with the actual outcome and retain the generated verification report.

Publication evidence is the anonymous public readback and live browser verification, not the archive upload alone. This record qualifies the showcase payload; it does not change the engine's experimental status or establish phone inference speedup.
