# JNI Unicode boundary correction

## Observation and attribution

Codex reproduced this defect before receiving any Qwen answer. It is therefore an independent finding, not a discovery attributed to Qwen. The original JNI source is retained in `native-boundary.prompt.txt`. The separate `jni-fix-audit` packet explicitly discloses the known issue and candidate patch.

JNI `GetStringUTFChars` produces Modified UTF-8. The native JSON parser expects standard UTF-8. A literal supplementary character, such as an emoji, is encoded differently and causes a valid JSON request to be rejected. The equivalent ASCII JSON escape succeeds. See the [JNI specification](https://docs.oracle.com/en/java/javase/25/docs/specs/jni/functions.html) and [Android JNI guidance](https://developer.android.com/ndk/guides/jni-tips).

## Correction

The adapter reads Java UTF-16 code units, combines valid surrogate pairs and emits standard UTF-8. It rejects malformed pairs and literal NUL before the NUL-terminated C ABI. Escaped JSON NUL remains valid. RAII releases Java characters and native response storage on every exit, including allocation exceptions. The output adapter retains `NewStringUTF` because `nl_call` serializes ASCII JSON with `ensure_ascii=true`.

## Verification and limits

The real JNI bridge was compiled and loaded by JDK 25 on macOS, linked to the existing NodeLift native library without model weights. Fifteen cases cover ASCII, accents, Chinese, combining characters, emoji, supplementary CJK, the maximum Unicode scalar, escaped emoji/NUL, literal NUL, malformed surrogate sequences and null input. All candidate cases passed. The same source also compiled into an Android ARM64 object with NDK 27.1.12297006.

The expected successful result is `no model loaded`, proving that valid JSON reaches the native operation instead of failing Unicode parsing. This is not a phone inference test. The existing worker normally sends numeric token IDs and a fixed internal model path; this reproduction does not explain the observed physical-phone timeouts. The correction is source-only until a new companion package is built and qualified. Published build 16 is unchanged.

```sh
python3 scripts/check-jni-unicode.py \
  --output artifacts/jni-unicode-check.json
```

Use `--android-compiler /absolute/path/to/aarch64-linux-android26-clang++` to include the Android compilation check. Read [the original observation](independent-observation.json), [before-fix output](jni-unicode-before.txt) and [candidate results](jni-unicode-candidate.json).
