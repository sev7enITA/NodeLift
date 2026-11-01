# Development and workflows

The repository separates fast source checks, documentation checks and optional native build verification. Read each workflow’s scope before interpreting a green result.

| Workflow | Trigger | What it establishes |
|---|---|---|
| Source checks | Push / pull request | Python contracts on 3.12/3.14, DistAI evidence consistency, generated localization freshness, LM Studio adapter and browser formatter tests |
| Documentation checks | Push / pull request | English documentation regression checks, local Markdown/image targets, release/build/history consistency, wiki completeness and diagnostic tests |
| Release verification | Manual tag selection | Published asset sizes and SHA-256 match the published manifest and GitHub digests; no package execution |
| Native build check | Manual | Locked native core compiles on a hosted macOS runner; no physical phone or speed claim |

The release verifier does not certify a signing identity or execute an APK. Mobile packages still require platform builds, same-key Android signing checks and explicit qualification records. iOS signing secrets are never part of this repository.

```sh
PYTHONPATH=host python3 -m unittest discover -s host/tests -v
python3 scripts/generate-localization.py --check
node scripts/check-localization.cjs
python3 scripts/release-history.py --check
python3 scripts/check-docs.py
python3 -m unittest discover -s scripts/tests -v
```

For native real-weight checks, first build the library and obtain the control weights, then use `scripts/check-native.py` and `scripts/check-remote-loopback.py`. The latter emulates a node over local TLS; it does not test a physical phone.

Wiki sources live in `docs/wiki`. To publish, clone the existing `NodeLift.wiki.git` repository, copy the Markdown files, review the diff, commit and push its default branch. Wiki publication is deliberately not hidden inside source CI.

[Contributor guide](https://github.com/sev7enITA/NodeLift/blob/main/CONTRIBUTING.md) · [Actions](https://github.com/sev7enITA/NodeLift/actions) · [REA engineering lessons](https://github.com/sev7enITA/NodeLift/blob/main/research/rea-2026-11-01/ASSESSMENT.md)

All authored repository documentation and Wiki pages are maintained in English. See the [release process](https://github.com/sev7enITA/NodeLift/blob/main/docs/RELEASING.md): every published Android/iOS build needs canonical release notes and verified portal/GitHub publication.
