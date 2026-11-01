# Showcase publication record

Published 31 October 2026: **https://www.fabriziodegni.com/NodeLift/**.

## English default and Simplified Chinese — 1 November 2026

The public showcase now opens in English by default, with language controls ordered **EN → 中文 → IT**. Simplified Chinese covers 303 messages, including narrative, architecture steps, downloads, credits, accessibility labels and dynamic atlas controls. Explicit visitor choices persist; a language in the URL takes precedence. English is also the source HTML/no-JavaScript default. Research entries and evidence downloads retain their canonical English text, as explained in each UI language. See [localization behavior](LOCALIZATION.md#public-showcase--1-november-2026).

Three existing files matched their previous hashes and were backed up before replacement; the new Chinese catalog was added. Four files were published through certificate-verified FTPS, with temporary uploads read back before rename. [Anonymous public verification](evidence/showcase-languages-2026-11-01/live-verification.json) confirms that all **15 public files** match the [frozen manifest](evidence/showcase-languages-2026-11-01/deployment-manifest.json), including the unchanged research/download files. The canonical `/NodeLift/` path returns HTTP 200.

Chrome verified all three languages on the public site, the EN/中文/IT control order and all 55 atlas entries loading. Local browser checks covered first-visit English, saved Italian, an English URL overriding that preference, Chinese filtering and all 18 project-detail labels, and filter preservation during switching. DOM layout checks found no horizontal document overflow at 375 CSS pixels in English/Chinese or at 768 pixels in English after bounding the decorative hero grid. The temporary viewport override was reset. These are browser checks, not physical-mobile tests or independent linguistic review. [Validation record](evidence/showcase-languages-2026-11-01/validation.json) · [Unmodified live Chinese screenshot](evidence/showcase-languages-2026-11-01/live-chinese.png).

## Companion 0.2.4 and in-app About — 1 November 2026

The portal download section now points to companion **0.2.4/build 6**: Android APK, unsigned iOS IPA and compiled `.app` ZIP. About & References, runtime installed version, Fabrizio Degni attribution, official project links, technical references and manual release discovery are included in the desktop and companion sources. [About behavior and qualification](ABOUT_AND_UPDATES.md).

Three existing portal files were backed up after matching the previous published manifest, then replaced through certificate-verified FTPS with readback before rename. [Anonymous HTTP verification](evidence/about-2026-11-01/portal-readback.json) confirms all **14 public files** match the [frozen payload](evidence/about-2026-11-01/deployment-manifest.json). Chrome confirmed the public 0.2.4 links. [Release verification](evidence/about-2026-11-01/release-readback.json) checked all five release assets and the tag's source identity.

Native HarmonyOS/NEXT remains uncompiled. The owner reported completing Huawei login and explicitly postponed SDK acquisition/build because the Mac lacks sufficient free disk space. No SDK download was started. The public guide records this deferral; no HAP is advertised as available.

## Mobile downloads update — 1 November 2026

The ten-chapter showcase now exposes `/NodeLift/#downloads` in its main navigation. It links to companion 0.2.3 Android APK, unsigned iOS IPA and compiled `.app` ZIP, plus the installation guide and SHA-256 inventory. APK-compatible HarmonyOS is explicitly an unverified compatibility trial. Native HarmonyOS/NEXT still has no compiled HAP; SDK acquisition requires Huawei sign-in in the inspected environment.

The IPA is a container change only: all app-file bytes match the existing published iOS ZIP. The original release packages and build manifest were preserved; the IPA and its packaging manifest were added as supplementary assets. [Release readback](evidence/mobile-downloads-2026-11-01/release-readback.json) verified all five assets against GitHub digests and local packages.

Four scoped portal files were uploaded over certificate-verified FTPS using the owner's existing hosting profile. Before replacing the two existing files, their remote bytes were saved locally and matched the previous repository versions. Temporary uploads were read back before rename. [Anonymous HTTP verification](evidence/mobile-downloads-2026-11-01/portal-readback.json) confirms all **14 public files** match the [frozen manifest](evidence/mobile-downloads-2026-11-01/deployment-manifest.json), with the canonical `/NodeLift/` path intact.

Browser checks confirmed Italian/English download labels and URLs, the explicit unsigned-iOS and unavailable-HAP states, and no horizontal document overflow at 390 CSS pixels. The deployed page was read back in Chrome. These are publication/UI checks, not device installation or inference tests. See [installation requirements](MOBILE_DOWNLOADS.md).

## Initial publication — 31 October 2026

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
