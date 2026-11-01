import SwiftUI
import UniformTypeIdentifiers
import UIKit

private let canvasColor = Color(red: 0.035, green: 0.071, blue: 0.086)
private let panelColor = Color(red: 0.063, green: 0.114, blue: 0.133)
private let lineColor = Color(red: 0.16, green: 0.25, blue: 0.28)
private let aquaColor = Color(red: 0.63, green: 1.0, blue: 0.945)
private let amberColor = Color(red: 1.0, green: 0.824, blue: 0.54)

/// Explicit pressed/disabled states remain legible independently of the global tint.
private struct NodeLiftButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var enabled
    var primary = false
    var destructive = false
    func makeBody(configuration: Configuration) -> some View {
        let accent = destructive ? Color(red: 1, green: 0.66, blue: 0.66) : aquaColor
        let fill = !enabled ? Color(red: 0.10, green: 0.15, blue: 0.18) : configuration.isPressed ? Color(red: 0.24, green: 0.44, blue: 0.43) : primary ? aquaColor : panelColor
        configuration.label
            .font(.subheadline.weight(.semibold))
            .foregroundStyle(!enabled ? Color(red: 0.62, green: 0.70, blue: 0.74) : configuration.isPressed ? Color.white : primary ? canvasColor : accent)
            .padding(.horizontal, 14).padding(.vertical, 12).frame(minHeight: 50)
            .background(fill, in: RoundedRectangle(cornerRadius: 11))
            .overlay(RoundedRectangle(cornerRadius: 11).stroke(enabled ? accent.opacity(configuration.isPressed ? 1 : 0.65) : lineColor, lineWidth: configuration.isPressed ? 2 : 1))
            .contentShape(RoundedRectangle(cornerRadius: 11))
            .scaleEffect(configuration.isPressed && enabled ? 0.98 : 1)
    }
}

@MainActor @main struct NodeLiftApp: App {
    @StateObject private var model = NodeModel()
    @Environment(\.scenePhase) private var phase

    init() {
        Diagnostics.shared.start()
        UpdateMonitor.shared.start()
    }

    var body: some Scene {
        WindowGroup {
            ContentView(model: model)
                .preferredColorScheme(.dark)
                .environment(\.locale, Locale(identifier: model.language))
                .task { if phase == .active { Diagnostics.shared.setActive(true) } }
                .onChange(of: phase) { _, value in
                    if value == .active {
                        Diagnostics.shared.setActive(true)
                        UpdateMonitor.shared.onResume()
                    } else if value == .background {
                        Diagnostics.shared.setActive(false)
                        model.pause()
                    }
                }
        }
    }
}

/// Native rendering of assets/brand/nodelift-mark.svg, including the original orbit.
private struct NodeLiftMark: View {
    var body: some View {
        Canvas { context, size in
            let scale = min(size.width, size.height) / 64
            let transform = CGAffineTransform(scaleX: scale, y: scale)
            var letter = Path()
            letter.move(to: CGPoint(x: 15, y: 48))
            letter.addLine(to: CGPoint(x: 15, y: 17))
            letter.addLine(to: CGPoint(x: 49, y: 47))
            letter.addLine(to: CGPoint(x: 49, y: 16))
            context.stroke(letter.applying(transform), with: .color(aquaColor), style: StrokeStyle(lineWidth: 8 * scale, lineCap: .square, lineJoin: .bevel))
            var orbit = Path()
            orbit.move(to: CGPoint(x: 5, y: 40))
            orbit.addCurve(to: CGPoint(x: 59, y: 26), control1: CGPoint(x: 12, y: 53), control2: CGPoint(x: 52, y: 43))
            context.stroke(orbit.applying(transform), with: .color(Color(red: 233/255, green: 249/255, blue: 252/255)), lineWidth: 2 * scale)
            context.fill(Path(ellipseIn: CGRect(x: 5, y: 39, width: 6, height: 6)).applying(transform), with: .color(Color(red: 233/255, green: 249/255, blue: 252/255)))
            context.fill(Path(ellipseIn: CGRect(x: 52, y: 28, width: 6, height: 6)).applying(transform), with: .color(aquaColor))
        }.accessibilityHidden(true)
    }
}

struct ContentView: View {
    @ObservedObject var model: NodeModel
    @ObservedObject private var updates = UpdateMonitor.shared
    @State private var incidentNotice = Diagnostics.shared.hasPreviousIncident
    @State private var showModelImporter = false
    @State private var importError: String?
    @State private var pairingExpanded = true
    @State private var showAbout = false
    @State private var showScanner = false
    @State private var scannedCode: String?
    @State private var pairingCode: String?
    @State private var pairingIdentity = ""
    @State private var confirmPairing = false
    @State private var confirmForget = false

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
                NodeLiftMark()
                    .frame(width: 35, height: 35).accessibilityHidden(true)
                Text("NodeLift").font(.system(size: 27, weight: .semibold)).tracking(-1)
                Text("/").font(.system(size: 27, weight: .light)).foregroundStyle(aquaColor).padding(.leading, -8)
                Spacer()
                Text(CompanionBuild.version).font(.system(size: 11, design: .monospaced)).foregroundStyle(.secondary)
            }
            Button { showAbout = true } label: {
                Label(T("About & References"), systemImage: "info.circle")
                    .font(.subheadline).frame(minHeight: 44)
            }.tint(aquaColor).accessibilityIdentifier("open-about")
            if updates.available {
                Text(updates.message.resolve(model.language)).font(.footnote.weight(.semibold))
                    .foregroundStyle(amberColor).accessibilityIdentifier("update-notice")
            }
            if incidentNotice {
                Text(T("A previous interruption was recorded. Export diagnostics from About & References."))
                    .font(.footnote).foregroundStyle(amberColor).accessibilityIdentifier("diagnostic-notice")
            }
            Picker(T("Language"), selection: $model.language) {
                Text("English").tag("en")
                Text("简体中文").tag("zh-Hans")
                Text("Italiano").tag("it")
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
                Label(model.connected ? T("SESSION ACTIVE") : model.running ? T("Connecting…") : T("SESSION PAUSED"), systemImage: model.connected ? "circle.fill" : model.running ? "arrow.triangle.2.circlepath" : "circle")
                    .font(.system(size: 10, weight: .medium, design: .monospaced)).foregroundStyle(aquaColor)
                Spacer()
                Text(T("LOCAL")).font(.system(size: 9, design: .monospaced))
                    .padding(.horizontal, 7).padding(.vertical, 4)
                    .overlay(RoundedRectangle(cornerRadius: 4).stroke(lineColor))
            }
            HStack {
                if model.running && !model.connected { ProgressView().tint(aquaColor).accessibilityLabel(T("Connecting…")) }
                Text(model.status.resolve(model.language)).font(.title3.weight(.medium)).accessibilityIdentifier("session-status")
            }
            if !model.telemetry.key.isEmpty {
                Text(model.telemetry.resolve(model.language)).font(.system(size: 12, design: .monospaced))
                    .foregroundStyle(.secondary).lineSpacing(4)
            }
            HStack(spacing: 10) {
                if model.hasSavedSession {
                    Button { model.connect(newTicket: false) } label: {
                        Label(model.connected ? T("✓ Session active") : model.running ? T("Connecting…") : T("Resume"), systemImage: model.connected ? "checkmark.circle" : "play.fill").frame(maxWidth: .infinity)
                    }
                    .buttonStyle(NodeLiftButtonStyle(primary: true))
                    .disabled(settingsLocked)
                }
                Button { model.pause() } label: {
                    Label(T("Pause"), systemImage: "pause.fill").frame(maxWidth: .infinity)
                }
                .buttonStyle(NodeLiftButtonStyle()).disabled(!model.running)
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
                    Text(T(model.engineEnabled ? "LLM proposals · ON" : "LLM proposals · OFF")).font(.subheadline.weight(.semibold))
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
            .buttonStyle(NodeLiftButtonStyle()).disabled(settingsLocked)
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
                    note(T("Choose Add device on your computer, then scan its QR code. Keep both devices on the same local network or phone hotspot."))
                    Button { showScanner = true } label: {
                        Label(T("Scan QR"), systemImage: "qrcode.viewfinder").frame(maxWidth: .infinity)
                    }.buttonStyle(NodeLiftButtonStyle(primary: true)).disabled(settingsLocked)
                    Text(T("Manual pairing")).font(.footnote).foregroundStyle(.secondary)
                    TextEditor(text: $model.ticketText).font(.system(size: 12, design: .monospaced))
                        .frame(height: 90).scrollContentBackground(.hidden).padding(8)
                        .background(canvasColor, in: RoundedRectangle(cornerRadius: 7))
                        .accessibilityLabel(T("NodeLift invitation")).autocorrectionDisabled()
                        .textInputAutocapitalization(.never).disabled(settingsLocked)
                    Button { model.connect(newTicket: true) } label: {
                        Text(T("Pair and activate node")).frame(maxWidth: .infinity)
                    }
                    .buttonStyle(NodeLiftButtonStyle(primary: true))
                    .disabled(settingsLocked || model.ticketText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    if model.hasSavedSession {
                        Divider().overlay(lineColor)
                        Button(T("Forget computer"), role: .destructive) { confirmForget = true }
                            .buttonStyle(NodeLiftButtonStyle(destructive: true)).disabled(settingsLocked)
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

    private func acceptPairingCode(_ value: String) {
        guard !settingsLocked else { model.status = "Pause the node before pairing another computer."; return }
        do {
            let ticket = try Ticket.decodeInvitation(value)
            pairingCode = value
            pairingIdentity = Message("Computer: {0} · Identity: {1}", URLComponents(string: ticket.url)?.host ?? ticket.url, String(ticket.sha256.prefix(16))).resolve(model.language)
            confirmPairing = true
        } catch { model.status = Message(error.localizedDescription) }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 19) {
                header
                sessionCard
                pairingCard
                engineCard
                limitsCard
                card {
                    eyebrow(T("03 / LAST RESULT"))
                    Text(model.lastResult.resolve(model.language)).foregroundStyle(aquaColor).font(.subheadline)
                        .accessibilityIdentifier("last-result")
                    note(T("Synthetic CPU tests do not indicate tokens/s. Draft proposal time is not the speed of a complete LLM response."))
                }
                HStack(alignment: .top, spacing: 11) {
                    Image(systemName: "testtube.2").foregroundStyle(amberColor)
                    VStack(alignment: .leading, spacing: 6) {
                        Text(T("Experimental companion")).font(.footnote.weight(.semibold)).foregroundStyle(amberColor)
                        Text(CompanionBuild.description(model.language)).font(.caption).foregroundStyle(.secondary)
                        Text(T("This iOS build has not been verified on a physical iPhone. Phone-assisted LLM acceleration has not been demonstrated."))
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                }.padding(.vertical, 8)
                Text(T("NodeLift / Your next upgrade is already in your hands.\nNo cloud account required."))
                    .font(.caption).foregroundStyle(.secondary).lineSpacing(4).padding(.top, 5)
            }.padding(22).frame(maxWidth: 700)
        }
        .frame(maxWidth: .infinity).background(canvasColor)
        .onAppear { pairingExpanded = !model.hasSavedSession; incidentNotice = Diagnostics.shared.hasPreviousIncident }
        .sheet(isPresented: $showAbout, onDismiss: { incidentNotice = Diagnostics.shared.hasPreviousIncident }) { AboutView(language: model.language) }
        .sheet(isPresented: $showScanner, onDismiss: {
            if let value = scannedCode { scannedCode = nil; acceptPairingCode(value) }
        }) {
            NavigationStack {
                QRScanner(language: model.language, onCode: { value in scannedCode = value; showScanner = false }, onError: { message in model.status = Message(message); showScanner = false })
                    .overlay(alignment: .bottom) { Text(T("Point the camera at the QR code on your computer.")).padding().background(.black.opacity(0.7)).foregroundStyle(.white) }
                    .navigationTitle(T("Scan QR"))
                    .toolbar { ToolbarItem(placement: .cancellationAction) { Button(T("Cancel")) { showScanner = false } } }
            }
        }
        .onOpenURL { url in acceptPairingCode(url.absoluteString) }
        .alert(T("Forget computer"), isPresented: $confirmForget) {
            Button(T("Cancel"), role: .cancel) {}
            Button(T("Forget computer"), role: .destructive) { if !settingsLocked { model.forget() } }
        } message: { Text(T("Remove the saved pairing from this phone? To revoke its server access too, use Revoke on the computer.")) }
        .alert(T("Pair your computer"), isPresented: $confirmPairing) {
            Button(T("Cancel"), role: .cancel) { pairingCode = nil }
            Button(T("Pair and activate node")) {
                if let value = pairingCode, !settingsLocked { model.ticketText = value; model.connect(newTicket: true) }
                pairingCode = nil
            }
        } message: { Text(pairingIdentity) }
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


private enum CompanionBuild {
    static var version: String { Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "-" }
    static var build: String { Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "-" }
    static func description(_ language: String) -> String {
        Message("Version {0} · build {1}", version, build).resolve(language)
    }
}

private struct AboutView: View {
    let language: String
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL
    @State private var linkError = false
    @ObservedObject private var updates = UpdateMonitor.shared
    @State private var diagnosticFeedback = ""
    @State private var diagnosticFailed = false
    @State private var preparingExport = false
    @State private var confirmClear = false
    @State private var diagnosticShare: DiagnosticShare?
    @State private var previousIncident = Diagnostics.shared.hasPreviousIncident
    private func T(_ key: String) -> String { Message(key).resolve(language) }

    private func section<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(T(title)).font(.headline).foregroundStyle(.primary)
            content()
        }
        .frame(maxWidth: .infinity, alignment: .leading).padding(20)
        .background(panelColor, in: RoundedRectangle(cornerRadius: 14))
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(lineColor, lineWidth: 1))
    }

    private func note(_ key: String) -> some View {
        Text(T(key)).font(.footnote).foregroundStyle(.secondary)
            .fixedSize(horizontal: false, vertical: true)
    }

    private func link(_ label: String, _ value: String) -> some View {
        Button {
            guard let url = URL(string: value) else { linkError = true; return }
            linkError = false
            openURL(url) { accepted in linkError = !accepted }
        } label: {
            HStack(alignment: .firstTextBaseline, spacing: 12) {
                Text(T(label)).multilineTextAlignment(.leading).fixedSize(horizontal: false, vertical: true)
                Spacer(minLength: 0)
                Image(systemName: "arrow.up.right").accessibilityHidden(true)
            }.font(.subheadline).frame(minHeight: 44)
                .frame(maxWidth: .infinity, alignment: .leading).contentShape(Rectangle())
        }.buttonStyle(.plain).foregroundStyle(aquaColor)
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    HStack(spacing: 12) {
                        NodeLiftMark()
                            .frame(width: 38, height: 38).accessibilityHidden(true)
                        VStack(alignment: .leading, spacing: 6) {
                            Text("NodeLift").font(.largeTitle.weight(.semibold))
                            Text(CompanionBuild.description(language)).font(.caption.monospaced()).foregroundStyle(aquaColor)
                        }
                    }.padding(.vertical, 8)
                    note("Experimental companion")
                    section("Created by Fabrizio Degni") {
                        note("Original concept, research direction and development.")
                        link("Author website", "https://www.fabriziodegni.com/")
                        link("LinkedIn", "https://www.linkedin.com/in/fdegni/")
                    }
                    section("Updates") {
                        note("NodeLift checks the official version metadata at launch and weekly while running. If the system suspends the app, an overdue check runs when you return. Installation is always your choice.")
                        HStack(alignment: .top, spacing: 10) {
                            if updates.checking { ProgressView().tint(aquaColor) }
                            Text(updates.message.resolve(language)).font(.subheadline).foregroundStyle(aquaColor)
                                .accessibilityIdentifier("update-status")
                        }
                        Button { updates.check(manual: true) } label: {
                            Label(T(updates.checking ? "Checking for updates…" : "Check now"), systemImage: "arrow.clockwise")
                                .frame(maxWidth: .infinity)
                        }.buttonStyle(NodeLiftButtonStyle()).disabled(updates.checking)
                            .accessibilityIdentifier("check-updates")
                        link("Check releases on GitHub", "https://github.com/sev7enITA/NodeLift/releases")
                        link("Official downloads & installation", "https://www.fabriziodegni.com/NodeLift/#downloads")
                    }
                    section("Diagnostics") {
                        note("A bounded seven-day log stays on this device. It records app and OS versions, technical events and limited error details. Pairing credentials, QR codes and prompt contents are excluded. Nothing is uploaded automatically.")
                        note("After an error or interruption, export a report and choose where to save or share it. Some native crashes and system shutdowns may leave no complete report.")
                        if previousIncident {
                            Text(T("A previous interruption was recorded. Export diagnostics from About & References."))
                                .font(.footnote).foregroundStyle(amberColor)
                        }
                        Button {
                            preparingExport = true
                            diagnosticFailed = false
                            do {
                                diagnosticShare = DiagnosticShare(url: try Diagnostics.shared.export())
                                diagnosticFeedback = "Diagnostic report prepared. Choose where to save or share it."
                            } catch {
                                diagnosticFeedback = "Unable to export diagnostics. Try again."
                                diagnosticFailed = true
                            }
                            preparingExport = false
                        } label: {
                            Label(T("Export diagnostics"), systemImage: "square.and.arrow.up").frame(maxWidth: .infinity)
                        }.buttonStyle(NodeLiftButtonStyle()).disabled(preparingExport)
                            .accessibilityIdentifier("export-diagnostics")
                        Button { confirmClear = true } label: {
                            Label(T("Clear diagnostics"), systemImage: "trash").frame(maxWidth: .infinity)
                        }.buttonStyle(NodeLiftButtonStyle(destructive: true)).disabled(preparingExport)
                            .accessibilityIdentifier("clear-diagnostics")
                        if !diagnosticFeedback.isEmpty {
                            Text(T(diagnosticFeedback)).font(.footnote).foregroundStyle(diagnosticFailed ? amberColor : aquaColor)
                                .accessibilityIdentifier("diagnostic-feedback")
                        }
                    }
                    section("Project & author") {
                        link("Source repository", "https://github.com/sev7enITA/NodeLift")
                        link("Project website", "https://www.fabriziodegni.com/NodeLift/")
                    }
                    section("References & licenses") {
                        link("Architecture & technical documentation", "https://github.com/sev7enITA/NodeLift/blob/main/docs/ARCHITECTURE.md")
                        link("Research & comparison atlas", "https://github.com/sev7enITA/NodeLift/blob/main/research/comparison-2026-10-31/README.md")
                        link("Third-party acknowledgements", "https://github.com/sev7enITA/NodeLift/blob/main/THIRD_PARTY_NOTICES.md")
                        link("MIT license · original NodeLift code", "https://github.com/sev7enITA/NodeLift/blob/main/LICENSE")
                        note("Dependencies and model weights retain their own licenses and authorship.")
                    }
                    if linkError {
                        Text(T("Unable to open this link. Open the official website in your browser."))
                            .font(.footnote).foregroundStyle(amberColor).accessibilityIdentifier("about-link-error")
                    }
                    note("Capacity sharding is not implemented. Physical-phone inference speedup remains unproven.")
                    note("Links open in your browser. NodeLift does not attach pairing keys, model data or diagnostics.")
                    note("Opening a browser may pause this node. Return to NodeLift and resume when ready.")
                    Text("© 2026 Fabrizio Degni").font(.caption).foregroundStyle(.secondary)
                }.padding(22).frame(maxWidth: 700)
            }.frame(maxWidth: .infinity).background(canvasColor)
                .navigationTitle(T("About & References")).navigationBarTitleDisplayMode(.inline)
                .toolbar { ToolbarItem(placement: .confirmationAction) { Button(T("Close")) { dismiss() }.tint(aquaColor) } }
        }.preferredColorScheme(.dark)
            .sheet(item: $diagnosticShare) { item in DiagnosticShareSheet(url: item.url) }
            .alert(T("Clear diagnostics"), isPresented: $confirmClear) {
                Button(T("Cancel"), role: .cancel) {}
                Button(T("Clear diagnostics"), role: .destructive) {
                    let cleared = Diagnostics.shared.clear()
                    if cleared { previousIncident = Diagnostics.shared.hasPreviousIncident }
                    diagnosticFeedback = cleared ? "Local diagnostic history cleared." : "Unable to clear diagnostics. Try again."
                    diagnosticFailed = !cleared
                }
            } message: {
                Text(T("Delete the local diagnostic history? Previously exported copies are not affected."))
            }
    }
}

private struct DiagnosticShare: Identifiable {
    let id = UUID()
    let url: URL
}

private struct DiagnosticShareSheet: UIViewControllerRepresentable {
    let url: URL
    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: [url], applicationActivities: nil)
    }
    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}

