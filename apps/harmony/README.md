# NodeLift HarmonyOS — native candidate

ArkTS/ArkUI sources for the Huawei Pura 70 Ultra reported by the owner as running HarmonyOS NEXT 7. **Not compiled, signed or tested on a device.** DevEco Studio/HarmonyOS SDK was unavailable in the inspected development environment; native compilation remains deferred due to limited disk space.

The candidate implements HTTPS pairing with a dedicated CA and SPKI pin, heartbeat, network tests, background pause and host-side revocation. Credentials remain in memory only. It declares `supported_jobs: ["network"]`: the server prevents CPU-test assignments. It does not report unmeasured RAM and does not load an LLM.

API 23+ is required for `HttpRequestOptions.maxRedirects=0`; the code also uses `caData` and `certificatePinning`. Import and qualify the project with the Huawei toolchain, including pin format, certificate hostname validation, trust failures and cancellation. The code does not disable TLS verification or follow redirects.

Primary references consulted:

- [HTTP Network Kit and pinning](https://github.com/openharmony/docs/blob/master/en/application-dev/reference/apis-network-kit/js-apis-http.md)
- [Monotonic systemDateTime clock](https://github.com/openharmony/interface_sdk-js/blob/master/api/@ohos.systemDateTime.d.ts)
- [Thermal API](https://github.com/openharmony/docs/blob/master/en/application-dev/reference/apis-basic-services-kit/js-apis-thermal.md)
- [Official HarmonyOS development environment](https://developer.huawei.com/consumer/en/harmonyos/develop/)

These references do not replace compilation and testing against the phone's actual API level. No installable HAP has been produced.
