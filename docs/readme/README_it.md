# NodeLift — Italiano

**Dai un nuovo ruolo nell’AI locale all’hardware che già possiedi.**

[![Licenza MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg)](../../LICENSE)
[![Vetrina del progetto](https://img.shields.io/badge/Showcase-Live-146c6a.svg)](https://www.fabriziodegni.com/NodeLift/)
[![Companion 0.2.4 prerelease](https://img.shields.io/badge/Companion-0.2.4%20prerelease-b45309.svg)](https://github.com/sev7enITA/NodeLift/releases/tag/v0.2.4)
[![Host 0.3.0 anteprima](https://img.shields.io/badge/Host-0.3.0%20preview-b45309.svg)](../../docs/INTEGRATIONS.md)

[![Controlli del codice](https://github.com/sev7enITA/NodeLift/actions/workflows/checks.yml/badge.svg?branch=main)](https://github.com/sev7enITA/NodeLift/actions/workflows/checks.yml)
[![Controlli della documentazione](https://github.com/sev7enITA/NodeLift/actions/workflows/documentation.yml/badge.svg?branch=main)](https://github.com/sev7enITA/NodeLift/actions/workflows/documentation.yml)
[![Compilazione nativa](https://github.com/sev7enITA/NodeLift/actions/workflows/native-build.yml/badge.svg?branch=main)](https://github.com/sev7enITA/NodeLift/actions/workflows/native-build.yml)
[![Verifica della release](https://github.com/sev7enITA/NodeLift/actions/workflows/release-verification.yml/badge.svg?branch=main)](https://github.com/sev7enITA/NodeLift/actions/workflows/release-verification.yml)

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776ab.svg)](../../docs/wiki/Quickstart.md)
[![C++17](https://img.shields.io/badge/C%2B%2B-17-00599c.svg)](../../native/CMakeLists.txt)
[![llama.cpp a revisione fissata](https://img.shields.io/badge/llama.cpp-pinned-146c6a.svg)](../../native/llama.lock)
[![UI: inglese, cinese semplificato, italiano](https://img.shields.io/badge/UI-EN%20%7C%20zh--Hans%20%7C%20IT-146c6a.svg)](../../docs/LOCALIZATION.md)

I badge di codice e documentazione seguono `main`; compilazione nativa e verifica della release mostrano l’ultima esecuzione manuale.

NodeLift è un progetto sperimentale ideato e sviluppato da **Fabrizio Degni**, con l’obiettivo di rendere RAM e calcolo dei dispositivi locali disponibili alle interfacce AI utilizzate ogni giorno. Il servizio di esecuzione condiviso è il cuore del prodotto; la GUI gestisce le risorse e gli adattatori collegano le applicazioni. [Direzione e roadmap](../ROADMAP.md).

Oggi un piccolo modello sul telefono può proporre token che il modello principale sul computer verifica. La distribuzione di parti del modello per aumentare la capacità di memoria resta da implementare; lo speedup su telefoni fisici deve ancora essere dimostrato.

L’app usa l’inglese come lingua predefinita. Dal selettore **Language** puoi scegliere **Italiano** o **简体中文**; la scelta viene salvata localmente. Le companion attuali sono **0.2.4 / build 6**; l’host include l’anteprima delle integrazioni 0.3.0.

- [Scarica la versione sperimentale](https://github.com/sev7enITA/NodeLift/releases/tag/v0.2.4): APK Android da laboratorio; build iOS senza firma, da firmare e predisporre prima dell’installazione.
- [Inizia dal computer](../wiki/Quickstart.md), poi aggiungi [Android](../wiki/Android.md) o [iPhone/iPad](../wiki/iOS-and-iPadOS.md).
- [Guida tecnica in italiano](../ENGINE_0_2.md), [lingue e verifiche](../LOCALIZATION.md), [modelli e provider](../wiki/Models-and-providers.md).
- [Wiki](https://github.com/sev7enITA/NodeLift/wiki), [immagini](../GALLERY.md), [vetrina](https://www.fabriziodegni.com/NodeLift/).
- [Grafo dei dispositivi e interpretazione del contributo](../DEVICE-GRAPH.md): hardware, dati storici e quota delle proposte mobili accettate, separati da utilizzo del calcolo e accelerazione.

Hugging Face e l’importazione diretta gestiscono GGUF completi. OpenRouter è facoltativo, invia i prompt al cloud e può comportare costi. Le API locali di LM Studio/oMLX sono percorsi separati dalle proposte del telefono.

Le prime prove con la piccola coppia di controllo hanno trovato il draft locale più lento del solo target. Pubblicare anche i risultati negativi fa parte del metodo. Una compilazione riuscita o una CI verde non sostituisce il benchmark sul dispositivo.

[English](../../README.md) · [简体中文](README_zh-Hans.md) · [Come contribuire](../../CONTRIBUTING.md)

**Informazioni e riferimenti:** autore, versione installata, siti ufficiali, fonti tecniche e verifica manuale delle release sono disponibili nella control room e nelle companion. [Guida](../ABOUT_AND_UPDATES.md).
