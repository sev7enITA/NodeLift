# Troubleshooting

Run `python3 scripts/doctor.py` for a read-only setup report. `--json` emits machine-readable results; `--strict` makes missing required build tools fail the command. It does not load models, run inference, install software, inspect credentials or establish device readiness.

| Symptom | Check / next action |
|---|---|
| Add device or engine controls unavailable | Open the local dashboard on the Mac and select **Restore local session**. This also handles a key expired by a host restart. If an older page is still open, reload it first. `scripts/open-dashboard.command` remains available as a fallback. Phone installation and enrollment are separate. |
| Same phone appears twice | Update the host and Android/iOS companion to 0.2.8, retaining app data. New QR enrollment reuses the installation identity. Legacy duplicates require owner-confirmed consolidation; matching names alone are insufficient. See [device identity](https://github.com/sev7enITA/NodeLift/blob/main/docs/DEVICE_IDENTITY.md). |
| Invitation rejected | Generate a new complete invitation. It expires after five minutes and is single-use. |
| Node paired but offline | Keep the companion running, resume it and confirm both devices use the intended private network. Check lifecycle and battery/thermal status. |
| Paired but no LLM node ready | Pairing is separate from inference. Import/download the exact configured draft and wait for the engine-ready status. |
| Native library absent | Run the locked native build and rerun diagnostics. A file existing is not proof that it can load. |
| SHA-256 mismatch | Do not use the incomplete/mismatched file. Retry the transfer from the intended model revision. |
| Import succeeds but load fails | Header acceptance does not guarantee runtime architecture, memory or tokenizer compatibility. Start with the documented control pair. |
| Phone path slower | Keep the host baseline; record proposal, transfer, verification and rejected-work costs. A larger draft block is not automatically faster. |
| Local API cannot connect | Check that the model server is running on this computer, its loopback port and `/v1` endpoint. A container’s loopback is different from the host’s. |
| iOS ZIP will not install | It is unsigned. Sign/provision with Xcode; there is no public TestFlight build. |

If unresolved, open a [bug report](https://github.com/sev7enITA/NodeLift/issues/new/choose) with public reproduction steps and version/OS information. For credentials or security-sensitive details, use the [security reporting guidance](https://github.com/sev7enITA/NodeLift/blob/main/SECURITY.md).
