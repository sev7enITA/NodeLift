# NodeLift localization

The control room and Android/iOS companions use **English by default**, independent of browser or system language. Choose **Language → 简体中文** for Simplified Chinese or **Language → Italiano** for Italian. The explicit choice is saved locally per browser/device. No account or translation service is needed. Traditional Chinese is not included in this release.

Mobile version: **0.2.4, build 6**. Update the Android APK over the existing same-key installation to retain pairing. The unsigned iOS app requires Apple signing and provisioning before installation. The HarmonyOS candidate has the same language selection in source; it remains uncompiled and unqualified on a physical device. LM Studio's SDK-owned configuration schema and developer CLI diagnostics remain in their existing languages. The public showcase has its own three-language catalog, described below.

## Public showcase: 1 November 2026

The website defaults to **English**, including its source HTML and no-JavaScript presentation. The selector order is **EN → 中文 (Simplified Chinese) → IT**. Browser/OS language does not override the default. An explicit visitor selection is saved locally; a `?lang=en`, `?lang=zh-Hans` or `?lang=it` URL takes precedence over that preference. Unknown language codes fall back to English. `zh` and `zh-CN` links resolve to `zh-Hans`.

The 303-message Chinese catalog in `site/NodeLift/assets/site-locales.js` covers the narrative, downloads, credits, accessibility labels, architecture steps, atlas controls, project-field labels, errors, pagination and presentation controls. Italian translations remain in explicit HTML attributes and dynamic message pairs. English is readable before scripts load. Chinese uses local CJK font fallbacks without downloading a font package. Title, description, document language and social locale metadata update with the selection; alternate-language links are declared in the HTML.

The atlas's research entries, original evidence, model/project names and downloadable research files retain their canonical English content in every language. The interface explicitly explains this, including in Chinese. Switching language preserves search/filter state and an open project; generated share links include the chosen language. This website change does not change the mobile applications or their release version.

The 0.2.4 companion build includes the device-graph catalog additions and 55 new shared messages for About, References and manual update discovery. Version and build values come from installed package metadata.

## Behavior

- Dashboard labels, controls, validation messages, run states, measurements, pairing instructions, dates and accessibility labels follow the selected language. The API key panel closes and clears its in-memory access data on a language change.
- Android includes the active-node notification and channel name. Changing language rebuilds the screen while retaining its invitation in memory; it does not start, stop or reconnect a worker. Engine preferences retain their values.
- iOS resolves stored messages and their arguments when rendering. The picker does not pause the active session or alter consent. Local network permission descriptions have English, Simplified Chinese and Italian resources; OS-owned permission dialogs follow OS policy.
- Prompt text, model output, model/device names, API fields and protocol identifiers remain unchanged. Unknown external/native diagnostics remain verbatim. A small explicit alias table renders known messages from older Italian companions without modifying stored/exported records.

## Catalogs and contribution

`localization/en.json` is the canonical English message catalog, with English source text as the message ID. `localization/zh-Hans.json` and `localization/it.json` each have the same 717 keys, including device-graph, model-library and external-provider messages. Numbered placeholders (`{0}`, `{1}`, ...) support Chinese argument ordering. Nested mobile messages localize telemetry labels while retaining raw numeric/device values. Parameters are substituted once and never treated as markup or translated content.

Edit the canonical catalogs, then run:

```sh
python3 scripts/generate-localization.py
python3 scripts/generate-localization.py --check
node scripts/check-localization.cjs
swiftc apps/ios/NodeLift/Localization.swift apps/ios/NodeLift/ChineseMessages.swift apps/ios/NodeLift/ItalianMessages.swift scripts/check-localization.swift -o /tmp/nodelift-localization-check
/tmp/nodelift-localization-check
```

The generator rejects missing keys, empty translations and placeholder mismatches. It writes the dashboard dictionary/runtime, Android asset, Swift dictionary and ArkTS dictionary. Generated files are committed so app use/build does not require a translation server. CI checks generated-file freshness and the browser formatter. Add future languages explicitly to the pickers and preference validation; unsupported/corrupt preferences currently fall back to English.

Android offline checks can run on a disposable ARM64 emulator using:

```sh
cd apps/android
./gradlew assembleDebug assembleDebugAndroidTest -PnodeliftTestRunner=dev.nodelift.companion.LocalizationCheck
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb install -r app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk
adb shell am instrument -w dev.nodelift.companion.test/dev.nodelift.companion.LocalizationCheck
```

The test restores its language preference and process locale. It does not pair with a host, request inference or establish phone performance.

## Italian addition: 0.2.3, 1 November 2026

- Added Italian for all 557 shared message IDs across the control room, Android, iOS and HarmonyOS candidate. English remains the new-install default; existing English/Chinese choices remain valid. Unknown preferences fall back to English.
- Catalog key parity, placeholders and generated-file freshness pass for both translations. JavaScript and Swift formatter checks pass for all three languages, including Italian nested telemetry, literal arguments, fallback and preference validation.
- Live Chrome checks passed: all three picker choices, Italian model-library and pairing labels, persisted Italian after reload, no horizontal overflow at the observed desktop width. Switching Chinese/Italian preserved a multilingual prompt containing template-like characters, the output-token setting, selected model, paired-device count and prior generated output. The original prompt/settings and English choice were restored. No new inference was requested.
- Android debug and instrumentation APKs and the unsigned iOS device app compiled as 0.2.3/build 5. Packaged native engine binaries are reused from the existing build and are verified against the 0.2.2 manifest. This is not a native-engine rebuild or a performance qualification.
- No Android device/emulator is currently listed by ADB; instrumentation execution and physical Android/iPhone UI checks remain unverified. No new GLM/Gemini review is claimed for this Italian addition. HarmonyOS remains source-only without an SDK build or HAP.

## Original 0.2.2 verification, 1 November 2026

- All 40 host tests passed. Catalog generation/freshness and JavaScript formatter checks passed, including English default with a Chinese browser locale, persisted selection, blocked storage, unknown messages, reordered placeholders and literal parameter isolation.
- Swift formatter checks passed on macOS: English/Chinese, nested telemetry, fallback, Unicode and parameter isolation. This is not a physical iPhone UI test.
- Live Chrome control room: English and Simplified Chinese, persistence after reload, unchanged multilingual prompt and unapplied thread setting, translated diagnostics/history, unchanged pairing invitation, and API access masking/clearing on language switch. One real host-only 8-token generation completed; its output stayed byte-for-byte unchanged when the interface switched language. This was a functional localization check, not an inference benchmark.
- Android debug APK and unsigned iOS device build compiled. Build caches/project coordination under the iCloud Desktop stalled; builds completed from a temporary local source mirror. The Android build reused the byte-identical ARM64 native library from the published 0.2.1 APK; the iOS build used the existing native framework. No native engine rebuild or new mobile performance claim is implied.
- The Android instrumentation APK compiled. Its offline localization tests could not run: the dedicated emulator remained ADB-offline after both normal and headless cold starts. The emulator was stopped; this is not recorded as a test pass.
- Physical Android/iOS localization, sustained active-worker switching and mobile visual/accessibility testing remain unverified. The Mac locked during native UI inspection. HarmonyOS uses the [documented PersistentStorage/StorageLink pattern](https://developer.huawei.com/consumer/en/doc/harmonyos-faqs-V14/faqs-local-database-management-2-V14), but no HarmonyOS SDK build/device test was available.

GLM 5.3 with Max effort reviewed a selected 15-item terminology sample through its browser UI. Accepted changes include 配套应用 for companion, hardware-lifespan wording, measured-evidence language and 任务委派控制. The thermal-protection wording was retained because the app may pause before overheating; initial ordering was retained because the implementation measures host steps before draft probes. This was a terminology review, not a complete catalog or functional review. Gemini High was unavailable due to the session usage limit, so no Gemini localization review is claimed.
