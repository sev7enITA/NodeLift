# Pre-measurement template correction

The first small-model smoke test stopped before inference because the pinned official 1.7B tokenizer ignores `enable_thinking=False`, whereas the 0.6B and 14B tokenizer templates append the empty thinking block. Vocabulary mappings agree. This is a tokenizer-template difference, not a measured quality difference.

Before any screening or validation execution, fix one shared request serialization using the pinned official 0.6B tokenizer with `enable_thinking=False`. Encode the exact same text with every target/draft tokenizer and require identical IDs. Both target-only and speculative requests receive this same canonical prefix. Do not silently compare differently serialized prompts. Record native-template differences and canonical-template identity in the manifest. This supersedes the original requirement that every repository's native template output already be identical, while preserving identical actual inference inputs.

The failed smoke log remains retained. No screening result informed this change.
