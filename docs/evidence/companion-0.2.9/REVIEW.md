# Companion 0.2.9 review and evidence

## External review

An actual Gemini browser session was configured as **4 Argon, High effort** after its temporary usage limit reset. Gemini reviewed the described native information architecture, state transitions, automatic assessment and KPI boundaries. It did not inspect phone screenshots or execute the application. The requested model was not silently replaced with Flash-Lite.

The review supported separating Home, Activity and Settings, then prioritized three improvements: expose automatic assessment and deferral on Home with accessible pause, announce discrete state changes without narrating every elapsed second, and improve fingerprint readout and model-setup focus routing. These recommendations informed the release implementation.

Gemini's suggestion that described control sizes and scalable fonts establish WCAG AA compliance was rejected. Code properties, successful compilation and a model review do not establish physical accessibility conformance. Its session-boundary test wording was also narrowed: a new session is inferred on the next authenticated contact after a gap, not merely when a timer crosses 20 seconds. Phone pause cancels the local worker; host-side jobs can remain pending until their existing deadlines, so instantaneous remote cancellation is not claimed.

The final Gemini response assessed the described architecture as internally consistent within its declared scope. This is a textual review opinion, not an independent execution result. Physical networking, mobile inference and accessibility qualification remain open.

## Source review and local validation

A separate source review found three defects before packaging: Home scanner reentry, a paired-computer address captured only during construction, and an overly broad TTFT label. All were corrected. A final source pass also identified cancelled-task state updates and a desktop/mobile fingerprint-length mismatch; session-generation guards and full grouped fingerprints address those findings. Focused regression checks cover scanner-busy policy and timing-scope distinctions.

The isolated desktop browser verified host role/IP/session display, automatic assessment completion through a TLS/HTTP fixture, explicit reassessment, English/Italian/Simplified Chinese rendering and bounded inspector layout. The fixture is labeled synthetic and its samples do not constitute a physical device benchmark. The desktop UI was visually inspected; native phone UI was not.

Android and iOS use existing native inference libraries. This release changes companion interaction, freshness reporting and assessment visibility, not the LLM kernel. Test and build totals are recorded in [validation.json](validation.json). [Assessment fixture receipt](assessment-wire.json) records its restricted scope.

## Physical checks still required

1. Rapid scanner activation, QR/manual identity-confirmation parity and address refresh after pairing.
2. New-device network/CPU assessment, visible phases and pause during transfer; distinguish local cancellation from eventual host timeout.
3. Battery, thermal and host-busy deferral with an explicit visible reason.
4. A response gap exceeding 20 seconds, stale indication and subsequent authenticated recovery/session split.
5. TalkBack/VoiceOver, Voice Access/Voice Control and keyboard/switch focus across tabs, setup, primary-action transitions and diagnostic export.
6. Maximum font size and reduced motion in English, Simplified Chinese and Italian, including fingerprint confirmation and long status strings.

Stable physical mobile inference, measured speedup, capacity sharding and energy efficiency remain unqualified. The prior Xiaomi network timeouts are not declared fixed by this UI release.
