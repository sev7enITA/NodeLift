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
                .environment(\.locale, Locale(identifier: model.language))
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

    private func T(_ key: String) -> String { Message(key).resolve(model.language) }

    private var settingsLocked: Bool { model.running || model.importingModel }

    private func card<Content: View>(@ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 16, content: content)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(21)
            .background(panelColor, in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(lineColor, lineWidth: 1))
    }

    private func eyebrow(_ text: String) -> some View {
        Text(T(text)).font(.system(size: 10, weight: .medium, design: .monospaced))
            .tracking(1.2).foregroundStyle(aquaColor)
    }

    private func note(_ text: String) -> some View {
        Text(T(text)).font(.footnote).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 10) {
                NodeLiftMark().stroke(aquaColor, style: StrokeStyle(lineWidth: 3.5, lineCap: .square, lineJoin: .bevel))
                    .frame(width: 35, height: 35).accessibilityHidden(true)
                Text("NodeLift").font(.system(size: 27, weight: .semibold)).tracking(-1)
                Text("/").font(.system(size: 27, weight: .light)).foregroundStyle(aquaColor).padding(.leading, -8)
                Spacer()
                Text("0.2.2").font(.system(size: 11, design: .monospaced)).foregroundStyle(.secondary)
            }
            Picker(T("Language"), selection: $model.language) {
                Text("English").tag("en")
                Text("简体中文").tag("zh-Hans")
            }.tint(aquaColor).accessibilityIdentifier("language-picker")
            eyebrow(T("LOCAL INTELLIGENCE NETWORK"))
            Text(T("Your device.\nA new role."))
                .font(.system(size: 32, weight: .medium)).tracking(-1.3).lineSpacing(-2)
                .padding(.top, 9)
            note(T("Connect your computer. Measure resources. Choose when to contribute computing power."))
        }.padding(.bottom, 4)
    }

    private var sessionCard: some View {
        card {
            HStack {
                Label(model.running ? T("SESSION ACTIVE") : T("SESSION PAUSED"), systemImage: model.running ? "circle.fill" : "circle")
                    .font(.system(size: 10, weight: .medium, design: .monospaced)).foregroundStyle(aquaColor)
                Spacer()
                Text(T("LOCAL")).font(.system(size: 9, design: .monospaced))
                    .padding(.horizontal, 7).padding(.vertical, 4)
                    .overlay(RoundedRectangle(cornerRadius: 4).stroke(lineColor))
            }
            Text(model.status.resolve(model.language)).font(.title3.weight(.medium)).accessibilityIdentifier("session-status")
            if !model.telemetry.key.isEmpty {
                Text(model.telemetry.resolve(model.language)).font(.system(size: 12, design: .monospaced))
                    .foregroundStyle(.secondary).lineSpacing(4)
            }
            HStack(spacing: 10) {
                if model.hasSavedSession {
                    Button { model.connect(newTicket: false) } label: {
                        Label(T("Resume"), systemImage: "play.fill").frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent).tint(aquaColor).foregroundStyle(canvasColor)
                    .disabled(settingsLocked)
                }
                Button { model.pause() } label: {
                    Label(T("Pause"), systemImage: "pause.fill").frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered).tint(aquaColor).disabled(!model.running)
            }
            Label(T("Foreground only"), systemImage: "iphone")
                .font(.footnote.weight(.medium)).foregroundStyle(aquaColor)
            note(T("Keep NodeLift open while working. Locking the screen or moving to the background pauses the session."))
        }
    }

    private var engineCard: some View {
        card {
            eyebrow(T("01 / DRAFT ENGINE"))
            HStack(alignment: .firstTextBaseline) {
                Text(T("Native draft")).font(.title3.weight(.semibold))
                Spacer()
                Text(T("EXPERIMENTAL")).font(.system(size: 9, design: .monospaced)).foregroundStyle(amberColor)
            }
            Text(model.engineStatus.resolve(model.language)).font(.subheadline).foregroundStyle(aquaColor)
                .accessibilityIdentifier("engine-status").fixedSize(horizontal: false, vertical: true)
            Toggle(isOn: $model.engineEnabled) {
                VStack(alignment: .leading, spacing: 5) {
                    Text(T("Allow LLM proposals")).font(.subheadline.weight(.semibold))
                    Text(T("Your paired Mac can send context to the draft. The main model on your Mac verifies the proposals."))
                        .font(.footnote).foregroundStyle(.secondary)
                }
            }.tint(aquaColor).disabled(model.importingModel)
                .onChange(of: model.engineEnabled) { _, _ in
                    // A changed consent stops existing work; resumption is deliberate.
                    if model.running { model.pause() }
                }
            note(T("Changing permission pauses an active session. Resume when you want to participate."))
            Divider().overlay(lineColor)
            Button { importError = nil; showModelImporter = true } label: {
                Label(model.importingModel ? T("Importing…") : T("Import GGUF draft"), systemImage: "square.and.arrow.down")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered).tint(aquaColor).disabled(settingsLocked)
            if model.importingModel {
                ProgressView().tint(aquaColor).frame(maxWidth: .infinity)
                    .accessibilityLabel(T("Importing model"))
            }
            if let importError {
                Text(T(importError)).font(.footnote).foregroundStyle(amberColor)
                    .accessibilityIdentifier("model-import-error")
            }
            note(T("In Files, choose the same GGUF draft configured on your Mac, up to 1 GiB. The file is imported and verified on this device."))
            if settingsLocked {
                Label(T("Pause to import or change resources."), systemImage: "lock")
                    .font(.footnote).foregroundStyle(.secondary)
            }
            VStack(alignment: .leading, spacing: 17) {
                VStack(alignment: .leading, spacing: 8) {
                    Text(T("Compute backend")).font(.subheadline.weight(.medium))
                    Picker(T("Compute backend"), selection: $model.engineMetal) {
                        Text(T("Metal · GPU")).tag(true)
                        Text("CPU").tag(false)
                    }.pickerStyle(.segmented).disabled(settingsLocked)
                }
                Stepper(value: $model.engineThreads, in: 1...8) {
                    HStack {
                        Text(T("CPU threads")).font(.subheadline)
                        Spacer()
                        Text("\(model.engineThreads)").font(.system(.body, design: .monospaced)).foregroundStyle(aquaColor)
                    }
                }.disabled(settingsLocked)
                Picker(T("Context tokens"), selection: $model.engineContext) {
                    ForEach([512, 1024, 2048, 4096], id: \.self) { value in
                        Text("\(value)").tag(value)
                    }
                }.tint(aquaColor).disabled(settingsLocked)
            }
            note(T("A larger context needs more memory. Compare Metal and CPU on this device; neither is assumed faster."))
        }
    }

    private var limitsCard: some View {
        card {
            eyebrow(T("02 / NODE LIMITS"))
            Text(T("You stay in control")).font(.title3.weight(.semibold))
            HStack {
                Text(T("Minimum battery for drafting")).font(.subheadline)
                Spacer()
                Text("\(Int(model.minimumBattery))%")
                    .font(.system(.title3, design: .monospaced)).foregroundStyle(aquaColor)
            }
            Slider(value: $model.minimumBattery, in: 20...70, step: 1)
                .tint(aquaColor).accessibilityLabel(T("Minimum battery for drafting"))
                .accessibilityValue(Message("{0} percent",Int(model.minimumBattery)).resolve(model.language))
            note(T("Below this threshold the node accepts no new LLM work. The engine also checks thermal status and available memory."))
            HStack(alignment: .top, spacing: 11) {
                Image(systemName: "thermometer.medium").foregroundStyle(aquaColor)
                note(T("Drafting requires nominal thermal status. Reported resources are not RAM already shared with your computer."))
            }
        }
    }

    private var pairingCard: some View {
        card {
            DisclosureGroup(isExpanded: $pairingExpanded) {
                VStack(alignment: .leading, spacing: 15) {
                    note(T("Choose “Add device” in the Mac dashboard and paste the complete invitation here. It is single-use and valid for 5 minutes."))
                    TextEditor(text: $model.ticketText).font(.system(size: 12, design: .monospaced))
                        .frame(height: 90).scrollContentBackground(.hidden).padding(8)
                        .background(canvasColor, in: RoundedRectangle(cornerRadius: 7))
                        .accessibilityLabel(T("NodeLift invitation")).autocorrectionDisabled()
                        .textInputAutocapitalization(.never).disabled(settingsLocked)
                    Button { model.connect(newTicket: true) } label: {
                        Text(T("Pair and activate node")).frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent).tint(aquaColor).foregroundStyle(canvasColor)
                    .disabled(settingsLocked || model.ticketText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    if model.hasSavedSession {
                        Divider().overlay(lineColor)
                        Button(T("Forget computer"), role: .destructive) { model.forget() }
                            .buttonStyle(.bordered).disabled(model.importingModel)
                    }
                }.padding(.top, 15)
            } label: {
                VStack(alignment: .leading, spacing: 4) {
                    Text(T("Computer pairing")).font(.subheadline.weight(.semibold))
                    Text(model.hasSavedSession ? T("Session saved on this device") : T("Connect your first computer"))
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
                    eyebrow(T("03 / LAST RESULT"))
                    Text(model.lastResult.resolve(model.language)).foregroundStyle(aquaColor).font(.subheadline)
                        .accessibilityIdentifier("last-result")
                    note(T("Synthetic CPU tests do not indicate tokens/s. Draft proposal time is not the speed of a complete LLM response."))
                }
                HStack(alignment: .top, spacing: 11) {
                    Image(systemName: "testtube.2").foregroundStyle(amberColor)
                    VStack(alignment: .leading, spacing: 6) {
                        Text(T("Experimental build · 0.2.2")).font(.footnote.weight(.semibold)).foregroundStyle(amberColor)
                        Text(T("This iOS build has not been verified on a physical iPhone. Phone-assisted LLM acceleration has not been demonstrated."))
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                }.padding(.vertical, 8)
                Text(T("NodeLift / Your next upgrade is already in your hands.\nNo cloud account required."))
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
                    importError = "Pause the session before importing a model."
                    return
                }
                guard url.pathExtension.lowercased() == "gguf" else {
                    importError = "Choose a .gguf file no larger than 1 GiB."
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
