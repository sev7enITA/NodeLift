# Showcase publication record

Prepared 31 October 2026. Target: **https://www.fabriziodegni.com/NodeLift/**.

## Current status

The showcase and the 55-entry comparison atlas are prepared locally. Publication is pending access to the website's existing Hostinger File Manager: opening `public_html` returned an access-denied page and HTTP 403, including after a fresh ordinary hPanel/File Manager session. An anonymous check of the intended public path still returned HTTP 404. No remote upload, extraction, permission change or root-site modification was performed in this attempt.

The owner has been asked to reopen/check the existing File Manager access. Authorization to publish was already provided; the unresolved requirement is working hosting access, not another approval to publish.

## Scoped payload

- Public source: `site/NodeLift/` only.
- Regenerate comparison exports: `python3 scripts/export_comparison.py`.
- Package reviewed files: `python3 scripts/package_showcase.py`.
- The packager records every file's size/SHA-256 and creates an archive containing only the top-level `NodeLift/` folder under ignored `artifacts/showcase/`.
- UI/source checks: [SHOWCASE_QA.md](SHOWCASE_QA.md).

## Publication procedure once access works

1. Open the File Manager for the existing fabriziodegni.com website. Confirm the target directory and whether NodeLift already exists.
2. Keep the deployment archive and any replacement backup outside `public_html`. For a first deployment, extract the archive to a private staging location and move its `NodeLift` folder into `public_html`. If a NodeLift folder has appeared since this attempt, preserve it before replacement.
3. Do not replace the portfolio root, run the whole-portfolio packager, change root `.htaccess`, or delete unrelated files.
4. Run `python3 scripts/verify_showcase.py`. It anonymously requests every manifest file with cache bypass and checks exact hashes and the `/NodeLift` → `/NodeLift/` canonical path.
5. Reopen the live page and verify narrative, matrix, filtering, one complete project dialog and download links. Update this record with the actual outcome and retain the generated verification report.

The intended URL is not proof of publication. A successful archive upload alone is not proof that the page is live or matches the reviewed files.
