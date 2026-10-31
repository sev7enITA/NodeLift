# NodeLift HarmonyOS — candidato nativo

Sorgenti ArkTS/ArkUI per Huawei Pura 70 Ultra dichiarato dall'utente con HarmonyOS NEXT 7. **Non compilati, non firmati, non verificati su device.** Nell'ambiente di sviluppo esaminato non è disponibile DevEco Studio/SDK HarmonyOS.

Il candidato implementa associazione HTTPS con CA dedicata e pin SPKI, heartbeat, test rete, pausa in background e revoca lato host. Le credenziali sono solo in memoria. Dichiara `supported_jobs: ["network"]`: il server impedisce di assegnargli test CPU. Non riporta RAM che non abbia misurato. Non carica LLM.

Richiede API 23+ per `HttpRequestOptions.maxRedirects=0`; usa anche `caData` e `certificatePinning`. Il progetto deve essere importato e qualificato con il toolchain Huawei installato, compresa verifica del formato pin, certificate hostname validation, errori di trust e cancellazione. Il codice non disabilita la verifica TLS e non segue redirect.

Fonti primarie consultate:

- [HTTP Network Kit e pinning](https://github.com/openharmony/docs/blob/master/en/application-dev/reference/apis-network-kit/js-apis-http.md)
- [Clock monotono systemDateTime](https://github.com/openharmony/interface_sdk-js/blob/master/api/@ohos.systemDateTime.d.ts)
- [Thermal API](https://github.com/openharmony/docs/blob/master/en/application-dev/reference/apis-basic-services-kit/js-apis-thermal.md)
- [Ambiente ufficiale HarmonyOS](https://developer.huawei.com/consumer/en/harmonyos/develop/)

Questi riferimenti non sostituiscono la compilazione e la prova dell'API level effettivo del telefono. Non è stato prodotto alcun HAP installabile.
