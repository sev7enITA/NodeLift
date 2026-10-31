import SwiftUI
import UniformTypeIdentifiers

private let canvasColor = Color(red: 0.035, green: 0.071, blue: 0.086)
private let panelColor = Color(red: 0.063, green: 0.114, blue: 0.133)
private let lineColor = Color(red: 0.16, green: 0.25, blue: 0.28)
private let aquaColor = Color(red: 0.63, green: 1.0, blue: 0.945)
private let amberColor = Color(red: 1.0, green: 0.824, blue: 0.54)

@main struct NodeLiftApp: App {
    @StateObject private var model = NodeModel()
    @Environment(\.scenePhase) private var phase

    var body: some Scene {
        WindowGroup {
            ContentView(model: model)
                .preferredColorScheme(.dark)
                .onChange(of: phase) { _, value in
                    if value == .background { model.pause() }
                }
        }
    }
}

/// Small original geometric mark; no external resource or downloaded font required.
private struct NodeLiftMark: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        path.move(to: CGPoint(x: rect.width * 0.22, y: rect.height * 0.77))
        path.addLine(to: CGPoint(x: rect.width * 0.22, y: rect.height * 0.23))
        path.addLine(to: CGPoint(x: rect.width * 0.78, y: rect.height * 0.77))
        path.addLine(to: CGPoint(x: rect.width * 0.78, y: rect.height * 0.23))
        return path
    }
}

struct ContentView: View {
    @ObservedObject var model: NodeModel
    @State private var showModelImporter = false
    @State private var importError: String?
    @State private var pairingExpanded = true

    private var settingsLocked: Bool { model.running || model.importingModel }

    private func card<Content: View>(@ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 16, content: content)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(21)
            .background(panelColor, in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(lineColor, lineWidth: 1))
    }

    private func eyebrow(_ text: String) -> some View {
        Text(text).font(.system(size: 10, weight: .medium, design: .monospaced))
            .tracking(1.2).foregroundStyle(aquaColor)
    }

    private func note(_ text: String) -> some View {
        Text(text).font(.footnote).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 10) {
                NodeLiftMark().stroke(aquaColor, style: StrokeStyle(lineWidth: 3.5, lineCap: .square, lineJoin: .bevel))
                    .frame(width: 35, height: 35).accessibilityHidden(true)
                Text("NodeLift").font(.system(size: 27, weight: .semibold)).tracking(-1)
                Text("/").font(.system(size: 27, weight: .light)).foregroundStyle(aquaColor).padding(.leading, -8)
                Spacer()
                Text("0.2.1").font(.system(size: 11, design: .monospaced)).foregroundStyle(.secondary)
            }
            eyebrow("LOCAL INTELLIGENCE NETWORK")
            Text("Il tuo dispositivo.\nUn nuovo ruolo.")
                .font(.system(size: 32, weight: .medium)).tracking(-1.3).lineSpacing(-2)
                .padding(.top, 9)
            note("Collega il computer. Misura le risorse. Scegli quando contribuire al calcolo.")
        }.padding(.bottom, 4)
    }

    private var sessionCard: some View {
        card {
            HStack {
                Label(model.running ? "SESSIONE ATTIVA" : "SESSIONE IN PAUSA", systemImage: model.running ? "circle.fill" : "circle")
                    .font(.system(size: 10, weight: .medium, design: .monospaced)).foregroundStyle(aquaColor)
                Spacer()
                Text("LOCALE").font(.system(size: 9, design: .monospaced))
                    .padding(.horizontal, 7).padding(.vertical, 4)
                    .overlay(RoundedRectangle(cornerRadius: 4).stroke(lineColor))
            }
            Text(model.status).font(.title3.weight(.medium)).accessibilityIdentifier("session-status")
            if !model.telemetry.isEmpty {
                Text(model.telemetry).font(.system(size: 12, design: .monospaced))
                    .foregroundStyle(.secondary).lineSpacing(4)
            }
            HStack(spacing: 10) {
                if model.hasSavedSession {
                    Button { model.connect(newTicket: false) } label: {
                        Label("Riprendi", systemImage: "play.fill").frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent).tint(aquaColor).foregroundStyle(canvasColor)
                    .disabled(settingsLocked)
                }
                Button { model.pause() } label: {
                    Label("Pausa", systemImage: "pause.fill").frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered).tint(aquaColor).disabled(!model.running)
            }
            Label("Solo in primo piano", systemImage: "iphone")
                .font(.footnote.weight(.medium)).foregroundStyle(aquaColor)
            note("Tieni aperta NodeLift durante il lavoro. Il blocco schermo o il passaggio in background mette in pausa la sessione.")
        }
    }

    private var engineCard: some View {
        card {
            eyebrow("01 / MOTORE DI PROPOSTA")
            HStack(alignment: .firstTextBaseline) {
                Text("Draft nativo").font(.title3.weight(.semibold))
                Spacer()
                Text("SPERIMENTALE").font(.system(size: 9, design: .monospaced)).foregroundStyle(amberColor)
            }
            Text(model.engineStatus).font(.subheadline).foregroundStyle(aquaColor)
                .accessibilityIdentifier("engine-status").fixedSize(horizontal: false, vertical: true)
            Toggle(isOn: $model.engineEnabled) {
                VStack(alignment: .leading, spacing: 5) {
                    Text("Consenti proposte LLM").font(.subheadline.weight(.semibold))
                    Text("Il Mac associato può inviare il contesto al draft. Il modello principale sul Mac verifica le proposte.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
            }.tint(aquaColor).disabled(model.importingModel)
                .onChange(of: model.engineEnabled) { _, _ in
                    // A changed consent stops existing work; resumption is deliberate.
                    if model.running { model.pause() }
                }
            note("Cambiare il consenso mette in pausa una sessione attiva. Riprendi quando vuoi partecipare.")
            Divider().overlay(lineColor)
            Button { importError = nil; showModelImporter = true } label: {
                Label(model.importingModel ? "Importazione in corso…" : "Importa draft GGUF", systemImage: "square.and.arrow.down")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered).tint(aquaColor).disabled(settingsLocked)
            if model.importingModel {
                ProgressView().tint(aquaColor).frame(maxWidth: .infinity)
                    .accessibilityLabel("Importazione del modello in corso")
            }
            if let importError {
                Text(importError).font(.footnote).foregroundStyle(amberColor)
                    .accessibilityIdentifier("model-import-error")
            }
            note("Scegli da File lo stesso draft GGUF configurato sul Mac, fino a 1 GiB. Il file viene importato e verificato sul dispositivo.")
            if settingsLocked {
                Label("Metti in pausa per importare o cambiare risorse.", systemImage: "lock")
                    .font(.footnote).foregroundStyle(.secondary)
            }
            VStack(alignment: .leading, spacing: 17) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Backend di calcolo").font(.subheadline.weight(.medium))
                    Picker("Backend di calcolo", selection: $model.engineMetal) {
                        Text("Metal · GPU").tag(true)
                        Text("CPU").tag(false)
                    }.pickerStyle(.segmented).disabled(settingsLocked)
                }
                Stepper(value: $model.engineThreads, in: 1...8) {
                    HStack {
                        Text("Thread CPU").font(.subheadline)
                        Spacer()
                        Text("\(model.engineThreads)").font(.system(.body, design: .monospaced)).foregroundStyle(aquaColor)
                    }
                }.disabled(settingsLocked)
                Picker("Token di contesto", selection: $model.engineContext) {
                    ForEach([512, 1024, 2048, 4096], id: \.self) { value in
                        Text("\(value)").tag(value)
                    }
                }.tint(aquaColor).disabled(settingsLocked)
            }
            note("Un contesto più ampio richiede più memoria. Metal e CPU vanno confrontati sul dispositivo; nessun vantaggio è presunto.")
        }
    }

    private var limitsCard: some View {
        card {
            eyebrow("02 / LIMITI DEL NODO")
            Text("Il controllo resta tuo").font(.title3.weight(.semibold))
            HStack {
                Text("Batteria minima per il draft").font(.subheadline)
                Spacer()
                Text("\(Int(model.minimumBattery))%")
                    .font(.system(.title3, design: .monospaced)).foregroundStyle(aquaColor)
            }
            Slider(value: $model.minimumBattery, in: 20...70, step: 1)
                .tint(aquaColor).accessibilityLabel("Batteria minima per il draft")
                .accessibilityValue("\(Int(model.minimumBattery)) per cento")
            note("Sotto questa soglia il nodo non accetta nuove proposte LLM. Il motore controlla anche stato termico e margine di memoria.")
            HStack(alignment: .top, spacing: 11) {
                Image(systemName: "thermometer.medium").foregroundStyle(aquaColor)
                note("Il draft richiede uno stato termico nominale. Le risorse rilevate non sono RAM già condivisa con il computer.")
            }
        }
    }

    private var pairingCard: some View {
        card {
            DisclosureGroup(isExpanded: $pairingExpanded) {
                VStack(alignment: .leading, spacing: 15) {
                    note("Nella dashboard del Mac scegli “Aggiungi dispositivo” e incolla qui l’invito completo. È monouso e valido per 5 minuti.")
                    TextEditor(text: $model.ticketText).font(.system(size: 12, design: .monospaced))
                        .frame(height: 90).scrollContentBackground(.hidden).padding(8)
                        .background(canvasColor, in: RoundedRectangle(cornerRadius: 7))
                        .accessibilityLabel("Invito NodeLift").autocorrectionDisabled()
                        .textInputAutocapitalization(.never).disabled(settingsLocked)
                    Button { model.connect(newTicket: true) } label: {
                        Text("Associa e attiva nodo").frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent).tint(aquaColor).foregroundStyle(canvasColor)
                    .disabled(settingsLocked || model.ticketText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    if model.hasSavedSession {
                        Divider().overlay(lineColor)
                        Button("Dimentica computer", role: .destructive) { model.forget() }
                            .buttonStyle(.bordered).disabled(model.importingModel)
                    }
                }.padding(.top, 15)
            } label: {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Associazione al computer").font(.subheadline.weight(.semibold))
                    Text(model.hasSavedSession ? "Sessione salvata sul dispositivo" : "Collega il tuo primo computer")
                        .font(.footnote).foregroundStyle(.secondary)
                }
            }.tint(aquaColor)
        }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 19) {
                header
                sessionCard
                engineCard
                limitsCard
                pairingCard
                card {
                    eyebrow("03 / ULTIMO RISULTATO")
                    Text(model.lastResult).foregroundStyle(aquaColor).font(.subheadline)
                        .accessibilityIdentifier("last-result")
                    note("I test CPU sintetici non indicano token/s. Il tempo di una proposta draft non è la velocità dell’intera risposta LLM.")
                }
                HStack(alignment: .top, spacing: 11) {
                    Image(systemName: "testtube.2").foregroundStyle(amberColor)
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Build sperimentale · 0.2.1").font(.footnote.weight(.semibold)).foregroundStyle(amberColor)
                        Text("Questa build iOS non è ancora verificata su un iPhone fisico. Non è dimostrata un’accelerazione LLM con il telefono.")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                }.padding(.vertical, 8)
                Text("NodeLift / Il prossimo upgrade è già nelle tue mani.\nNessun account cloud richiesto.")
                    .font(.caption).foregroundStyle(.secondary).lineSpacing(4).padding(.top, 5)
            }.padding(22).frame(maxWidth: 700)
        }
        .frame(maxWidth: .infinity).background(canvasColor)
        .onAppear { pairingExpanded = !model.hasSavedSession }
        .fileImporter(isPresented: $showModelImporter, allowedContentTypes: [.data], allowsMultipleSelection: false) { result in
            switch result {
            case .success(let urls):
                guard let url = urls.first else { return }
                guard !settingsLocked else {
                    importError = "Metti in pausa la sessione prima di importare un modello."
                    return
                }
                guard url.pathExtension.lowercased() == "gguf" else {
                    importError = "Scegli un file con estensione .gguf, fino a 1 GiB."
                    return
                }
                importError = nil
                model.importDraft(url)
            case .failure(let error):
                importError = error.localizedDescription
            }
        }
    }
}
