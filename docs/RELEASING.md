# Releasing NodeLift companions

Every published Android/iOS build must appear in the [repository changelog](../CHANGELOG.md) and [portal release history](https://www.fabriziodegni.com/NodeLift/#changelog). `releases/history.json` is the canonical English source; do not hand-edit generated history. Companion and host-preview versions are separate.

## Prepare and compile

1. Increment Android `versionName`/`versionCode` and iOS `MARKETING_VERSION`/`CURRENT_PROJECT_VERSION`. Add the same version/build as the newest history entry, describing actual changes, validation and limitations. A new distributed binary requires a new build identity; do not replace published assets in place.
2. Before publication, `published_at` may be null while preparing a build. `python3 scripts/release-history.py --check-build` validates version/build identity and substantive release notes; both mobile build scripts run this preflight. Populate the actual UTC publication timestamp when publishing.
3. Compile with `scripts/build-android.sh` and `scripts/build-ios.sh`. Verify packaged version/build, Android signature continuity, native-library hashes and required tests. Record exact source commit, package sizes/SHA-256 and qualification limits in the build manifest.
4. For iOS, an unsigned IPA is a `Payload/NodeLift.app/` packaging of the compiled app, not a signed distribution. Verify file-by-file equivalence with the app ZIP. Do not describe it as directly installable, TestFlight-ready or physically tested without corresponding evidence. Do not download deferred HarmonyOS SDKs as a side effect.

## Publish and synchronize

1. Review the exact staged source; exclude unrelated experiments, credentials, private prompts, weights and signing material. Publish the immutable source tag and assets to the official GitHub prerelease. Preserve existing tags and asset bytes.
2. Read back the release publication time and asset digests. Update canonical history and `site/NodeLift/data/mobile-downloads.json` with the actual version/build, source commit, files and platform status. Update current download links and Wiki entry points.
3. Run `python3 scripts/release-history.py`. It generates `CHANGELOG.md`, portal `data/changelog.md`, `data/changelog.json` and the rendered HTML history. Run `python3 scripts/release-history.py --check`, `python3 scripts/check-docs.py` and the documentation tests. Source/companion UI localizations remain English, Simplified Chinese and Italian; repository prose stays English.
4. Push the release-documentation commit and publish changed Wiki sources separately. CI checks generated freshness and matching Android/iOS/portal version/build. A failed gate must be resolved; a green gate is not proof of website publication or physical-device behavior.
5. Deploy changed portal files using authenticated hosting access. Check the previous deployed hashes, retain backups, upload/read back temporary files, then promote them; stop on concurrent remote changes. Include translated research downloads if changed, generated release history and asset cache-version updates.
6. Read the public HTTPS files back and compare SHA-256 to local content. Check the changelog and downloads in default English, Simplified Chinese and Italian, including a narrow viewport. Publish the deployment manifest/evidence without credentials.
7. Run `python3 scripts/verify-release.py --tag vVERSION --output artifacts/release-VERSION/publication-verification.json`. Record verification separately from native compilation and physical device tests.

## Documentation-only corrections

Do not create a new mobile version or claim a new build for prose corrections. Add a dated documentation/tooling entry, regenerate both changelogs and publish the changed site/Git/Wiki content. Old release tags and original external transcripts remain historical evidence. The current English guides explain that evidence without altering it.

## Required distinction in announcements

State what is compiled, what is signed, what can be installed, what was exercised on a physical device and what performance was measured. Successful compilation, static/model review, CI and emulated-node tests are separate evidence. HarmonyOS/NEXT remains deferred until its native SDK build and device qualification actually happen.
