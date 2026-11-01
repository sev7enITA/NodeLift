# Backend controls: 2 November 2026

The desktop execution selector changed backend, but its Provider model list had no nearby catalog-loading action. Catalog refresh and credentials lived in a separate collapsed panel with an independent backend selector. A local server configured on port 8000 also failed while the running LM Studio instance listened on port 1234.

The fix adds Load backend models, Configure selected backend, inline readiness and backend-scoped errors. The execution selection owns catalog requests, and configuration opens the matching access form with focus on URL or key. Native target/draft controls and the applied native configuration are not presented as the external provider configuration. Provider-model change events immediately refresh Run readiness. Main/draft explanations identify inventory provenance, compatibility limits and optional draft usage. Host inspector availability now invalidates its cached rendering when the engine status changes.

Focused model-library regression tests cover duplicate requests, polling during catalog loading, empty catalogs, failures/retry, backend mismatch, configuration focus routing state, and missing cloud credentials. Existing controls, graph and localization suites passed. The local browser loaded the actual OpenRouter catalog, selected a model and displayed rates without sending cloud generation. It also reproduced the wrong-port local error, configured the existing LM Studio server and completed a text request returning OK.

The first 16-token local request completed without visible content; the 128-token-budget request returned OK with 34 provider-reported completion tokens. These are functional checks, not a timing comparison: loading, model state and budgets differ. [Sanitized receipt](browser-checks.json).

Provider configuration remains session-only. This host/UI update does not rebuild or change the published 0.2.9 mobile packages. No mobile inference or acceleration is established.
