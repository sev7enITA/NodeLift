# NodeLift — comparison methodology

Source freeze: **31 October 2026**. Dataset version: **1**. Curator: Fabrizio Degni / NodeLift project. The evidence snapshot remains unchanged by later documentation translations or companion releases.

## Scope

55 selected entries: 16 distributed systems, 17 runtimes, 6 serving platforms, 5 mobile apps, 2 local references and 9 research works. The matrix applies uniform descriptive criteria rather than arbitrary competitive scores. It is a broad inventory, not a promise to include every project or certify a universal winner.

Research started from DistAI and NodeLift's checked bibliography, expanded related-project links, and searched mobile/distributed implementations, native runtimes and recent research. Western, Asian and international projects are included. Duplicative chat-only frontends, generic model catalogs, training-only networks and forks without relevant differences are excluded. An accessible source and relevant technical connection are minimum requirements.

**Not every row is a direct alternative.** A kernel, app, paper and server platform are not interchangeable; category stays visible in filters. Abstracts/READMEs are authors' statements and do not by themselves establish reproducibility on our phones.

## Geography without assumptions

The ecosystem field records documented organization/collaboration provenance: western, asia, international or unverified. Nationality/ethnicity is not inferred from names, alphabets or pseudonyms. Multinational work is not forced into a binary category. Provenance assigns no technical advantage.

## Comparison dimensions

Each entry includes name, category, provenance, status, license, architecture, hosts, Android/iOS, actual mobile-compute role, capacity beyond one device, single-chat effect, transport, APIs/integrations, security, evidence level, limitations, NodeLift lesson, revision, check date and sources.

- **Mobile compute:** on-device inference, distinct from displaying remote answers. An available SDK is not a qualified companion.
- **Capacity:** partitioned weights across devices, distinct from local RAM/disk use, whole-request routing or a small remote draft.
- **Single chat:** total/inter-token latency of one generation. Not inferred from aggregate throughput, prefill, an isolated kernel or model size fitting memory.
- **Android/iOS:** distinguishes source, build, distributed app, physical demonstration and NodeLift qualification. Filter tags indicate documented relevance, not certification.
- **Transport:** documented actual path. Wi-Fi, USB cable, USB networking, Ethernet and RDMA are not synonyms; a connector does not guarantee an IP rate.
- **API:** observed/documented compatibility, distinct from an official internal plugin. NodeLift 0.2.1 is not an internal Ollama backend; its LM Studio SDK handler was tested, the complete plugin runtime was not.
- **Security:** stated mechanisms or explicit limits. No competitor penetration testing was performed. Local does not automatically mean encrypted or safe against peers.
- **License:** informational identification at the examined revision. Dependencies, weights and distributions may have different terms. No legal compatibility determination. GitHub NOASSERTION does not prove absence of a license.

## Evidence and numbers

External performance is attributed to its authors, not reproduced on NodeLift's testbed. Physical hardware, emulation, simulation, theoretical analysis, compilation and document inspection are explicitly distinguished.

Do not directly compare tokens/s from different models, prompts, quantization, hardware or metrics. “Up to” is not typical performance. GitHub stars, downloads and marketing do not establish correctness or maturity.

For this snapshot, NodeLift's public reference is experimental 0.2.1. The 60 frozen runs are local on M3 Max, Qwen2.5 1.5B target/0.5B draft, maximum 64 tokens, six prompts and two repetitions per arm. All 48 paired token comparisons agree, but median speedups remain 0.425–0.719×: **no acceleration demonstrated**. The emulated TLS node and physical Xiaomi network pilot are separate evidence. Distributed inference speed on a physical phone remains unqualified.

## Revisions and aliases

45 repositories are recorded in source-inventory.json with immutable Git commits; 44 are standalone entries. Pooled was previously SwarmLLM: Pendia/SwarmLLM-P2P-AI is a historical source for that family, not another competitor. Nakshatra has Petals Git ancestry but documents its own current architecture and is described separately. The Ollama Cluster fork is separate from upstream. PowerInfer-2 research differs from desktop PowerInfer code. LiteRT-LM/Gallery and MLC/WebLLM share families but cover different layers.

Paper revisions are explicit; unversioned webpages remain mutable. Custom licenses/documentation inconsistencies are flagged, not resolved by assumption. Missing data means **not documented in examined sources**, not impossible or certainly absent.

## Reproduction and corrections

JSON is canonical for the 55 entries; CSV and Markdown export identical fields. Technical descriptions remain English across the showcase languages to prevent divergent inventories. The current site's narrative/controls support default English, Simplified Chinese and Italian. Sources and commits appear in each entry; the repository contains the inventory/export generator.

Report corrections through [GitHub Issues](https://github.com/sev7enITA/NodeLift/issues), with a primary source, revision, device and exact execution path. A documentation correction does not replace a benchmark.
