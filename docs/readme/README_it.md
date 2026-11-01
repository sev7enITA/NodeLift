# NodeLift — Italiano

**Dai un nuovo ruolo nell’AI locale all’hardware che già possiedi.**

NodeLift è un progetto sperimentale ideato e sviluppato da **Fabrizio Degni**. Un piccolo modello sul telefono può proporre token; il modello principale sul computer li verifica. La RAM dei telefoni non viene ancora sommata a quella del target e non è stato dimostrato uno speedup su telefoni fisici.

L’app usa l’inglese come lingua predefinita. Dal selettore **Language** puoi scegliere **Italiano** o **简体中文**; la scelta viene salvata localmente. Le companion attuali sono **0.2.3 / build 5**; l’host include l’anteprima delle integrazioni 0.3.0.

- [Scarica la versione sperimentale](https://github.com/sev7enITA/NodeLift/releases/tag/v0.2.3): APK Android da laboratorio; build iOS senza firma, da firmare e predisporre prima dell’installazione.
- [Inizia dal computer](../wiki/Quickstart.md), poi aggiungi [Android](../wiki/Android.md) o [iPhone/iPad](../wiki/iOS-and-iPadOS.md).
- [Guida tecnica in italiano](../ENGINE_0_2.md), [lingue e verifiche](../LOCALIZATION.md), [modelli e provider](../wiki/Models-and-providers.md).
- [Wiki](https://github.com/sev7enITA/NodeLift/wiki), [immagini](../GALLERY.md), [vetrina](https://www.fabriziodegni.com/NodeLift/).

Hugging Face e l’importazione diretta gestiscono GGUF completi. OpenRouter è facoltativo, invia i prompt al cloud e può comportare costi. Le API locali di LM Studio/oMLX sono percorsi separati dalle proposte del telefono.

Le prime prove con la piccola coppia di controllo hanno trovato il draft locale più lento del solo target. Pubblicare anche i risultati negativi fa parte del metodo. Una compilazione riuscita o una CI verde non sostituisce il benchmark sul dispositivo.

[English](../../README.md) · [简体中文](README_zh-Hans.md) · [Come contribuire](../../CONTRIBUTING.md)
