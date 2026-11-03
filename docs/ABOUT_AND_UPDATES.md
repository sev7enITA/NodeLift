# About, references and update discovery

**About & References** identifies Fabrizio Degni as NodeLift's creator, links the project, source, references and licenses, and shows the installed platform version. English is the default, followed by Simplified Chinese and Italian.

| Surface | Version source | Update discovery |
| --- | --- | --- |
| Desktop control room | Authenticated local `/admin/about` | Official releases link; host source preview is separate from companion version |
| Android companion | Android package version and build | Automatic at process launch and weekly while running; explicit Check now |
| iOS / iPadOS companion | App bundle version and build | Automatic at process launch and weekly while running; overdue check on return from suspension; explicit Check now |
| HarmonyOS source candidate | Runtime bundle metadata | Existing manual release link; native SDK build and automatic-check parity remain pending |

## Automatic mobile checks

The companion fetches the small public [mobile release manifest](https://www.fabriziodegni.com/NodeLift/data/mobile-downloads.json) and the matching [changelog](https://www.fabriziodegni.com/NodeLift/data/changelog.json) over HTTPS. Both bounded responses must agree on the release identity and publication date before downloadable details are shown. The experimental release channel includes published NodeLift companion prereleases. Three numeric version components are compared numerically, followed by the build number for the same version. Published build numbers are additionally required to increase across versions. An older manifest clears downloadable details and produces an unavailable check; it cannot trigger a downgrade prompt. A local development build ahead of the public manifest can therefore report unavailable metadata even when the network works. Malformed or oversized responses fail without changing pairing or the engine.

A fresh process checks at launch even if a prior check was recent. A successful check schedules the next check seven days later. Failed due checks retry after one hour while the process runs. The 3 November source correction preserves that backoff after a backward clock adjustment, treating future timestamps individually as unknown. There is one request in flight at a time. The OS may suspend timers, especially on iOS or during Android power saving; the app performs an overdue check when it returns to the foreground. It cannot promise background execution while the OS has suspended or terminated it.

**Check now** is an explicit retry. The UI distinguishes checking, a newer release, no newer release and an unavailable check. Installation is always chosen by the user through the official download route. No APK, IPA or executable is downloaded or installed by the checker. iOS signing requirements still apply.

Checks send a generic app user-agent and no device identifier, pairing token, prompt, model data or diagnostic report. The public server necessarily receives the network request and source IP like any HTTPS website. This is metadata discovery over HTTPS, not a signed automatic installer. A future installer would need separate package authenticity, platform signing and rollback design.

## Diagnostics

**Export diagnostics** and **Clear diagnostics** are separate from updates. Export uses the platform share sheet; no log upload runs automatically. See [wireless support and crash-report limitations](MOBILE_DIAGNOSTICS.md).

Opening a browser or share destination may pause iOS delegated work under its existing foreground lifecycle. Return to NodeLift and resume when ready. Opening About or checking metadata does not alter engine consent or pairing.

## Verification

See [0.2.6 release evidence](evidence/companion-0.2.6/README.md) for automated checks, builds, external-review scope and device limitations. Earlier [About evaluation](evidence/about-2026-11-01/model-review.json) covers the earlier manual-link UI only; it is not evidence of these new automatic checks.

## 3 November assessment

Gemini 4 Argon High completed a scoped static review of About/update sources and a correction follow-up. [Findings and verified fixes](../research/reviewer-resumption-2026-11-03/PRODUCT-REVIEW.md) distinguish source/policy tests from physical UI and published mobile packages. No new APK or IPA was released by this assessment.
