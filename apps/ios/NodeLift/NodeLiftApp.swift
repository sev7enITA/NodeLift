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
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
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
            .scaleEffect(configuration.isPressed && enabled && !reduceMotion ? 0.98 : 1)
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

/// Approved showcase emblem; the simplified mark is reserved for small system icons.
private struct NodeLiftMark: View {
    var body: some View {
        Image("NodeLiftEmblem")
            .resizable()
            .scaledToFit()
            .accessibilityHidden(true)
    }
}

struct ContentView: View {
    @ObservedObject var model: NodeModel
    @ObservedObject private var updates = UpdateMonitor.shared
    @State private var incidentNotice = Diagnostics.shared.hasPreviousIncident
    @State private var showModelImporter = false
    @State private var importError: String?
    @State private var pairingExpanded = false
    @State private var manualExpanded = false
    @State private var resourcesExpanded = false
    @State private var selectedTab = 0
    @State private var diagnosticShare: DiagnosticShare?
    @State private var diagnosticFeedback = ""
    @State private var showAbout = false
    @State private var releaseDetails:ReleaseDetails?
    @State private var showScanner = false
    @State private var scannedCode: String?
    @State private var pairingCode: String?
    @State private var pairingIdentity = ""
    @State private var pairingIdentitySpoken = ""
    @State private var requestModelFocus = false
    @AccessibilityFocusState private var modelSetupFocused: Bool
    @State private var confirmPairing = false
    @State private var confirmForget = false

    private func T(_ key: String) -> String { Message(key).resolve(model.language) }

    private var settingsLocked: Bool { model.running || model.importingModel || model.diagnosticRunning }
    private var connectionLabel: String {
        if model.running && (model.contactAgeSeconds ?? 0)>=20 {return T("Connection needs checking")}
        return model.connected ? T("SESSION ACTIVE") : model.running ? T("Connecting…") : model.hasSavedSession ? T("SESSION PAUSED") : T("Not paired")
    }
    private var primaryActionLabel: String {T(!model.hasSavedSession ? "Scan QR" : model.running ? "Pause node" : "Resume session")}
    private func announce(_ value:String) {
        guard UIAccessibility.isVoiceOverRunning, UIApplication.shared.applicationState == .active, !value.isEmpty else {return}
        UIAccessibility.post(notification:.announcement,argument:NSAttributedString(string:value,attributes:[.accessibilitySpeechQueueAnnouncement:true]))
    }

    private func card<Content: View>(@ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 16, content: content)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(21)
            .background(panelColor, in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(lineColor, lineWidth: 1))
    }

    private func eyebrow(_ text: String) -> some View {
        Text(T(text)).font(.caption.weight(.semibold))
            .tracking(1.2).foregroundStyle(aquaColor)
    }

    private func note(_ text: String) -> some View {
        Text(T(text)).font(.footnote).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 12) {
                NodeLiftMark().frame(width: 44, height: 44)
                Text("NodeLift").font(.largeTitle.weight(.semibold))
            }
            Text(T("Your phone, ready to help")).font(.headline).foregroundStyle(.secondary)
            if updates.available {
                Text(updates.message.resolve(model.language)).font(.subheadline)
                    .foregroundStyle(amberColor).accessibilityIdentifier("update-notice")
                Button(T("View release notes & download")) { releaseDetails=updates.details }
                    .buttonStyle(NodeLiftButtonStyle()).disabled(updates.checking || updates.details == nil)
            }
            if incidentNotice {
                Button { selectedTab = 1 } label: {
                    Label(T("A previous interruption was recorded. Export diagnostics from About & References."), systemImage: "exclamationmark.triangle")
                        .font(.subheadline).fixedSize(horizontal: false, vertical: true)
                }.buttonStyle(NodeLiftButtonStyle()).accessibilityIdentifier("diagnostic-notice")
            }
        }
    }

    private var sessionCard: some View {
        card {
            Text(T("Computer connection")).font(.headline).accessibilityAddTraits(.isHeader)
            Label(connectionLabel, systemImage: model.connected ? "checkmark.circle" : model.running ? "arrow.triangle.2.circlepath" : "circle")
                .font(.headline).foregroundStyle(model.connected ? aquaColor : model.running ? amberColor : Color.secondary)
            HStack(alignment: .top) {
                if model.running && !model.connected { ProgressView().tint(aquaColor).accessibilityLabel(T("Connecting…")) }
                Text(model.running && (model.contactAgeSeconds ?? 0)>=20 ? T("Waiting for a recent response from the computer") : model.status.resolve(model.language)).font(.body).accessibilityIdentifier("session-status")
                    .fixedSize(horizontal: false, vertical: true)
            }
            Text(model.contactAgeSeconds.map { Message("Last response: {0} s ago",$0).resolve(model.language) } ?? T("No response yet")).font(.subheadline).foregroundStyle(.secondary)
            if !model.assessmentStatus.key.isEmpty {
                Label(model.assessmentStatus.resolve(model.language),systemImage:model.diagnosticRunning ? "waveform.path.ecg" : "info.circle")
                    .font(.body).foregroundStyle(amberColor).fixedSize(horizontal:false,vertical:true)
                    .accessibilityIdentifier("assessment-status")
            }
            Label(T("Foreground only"), systemImage: "iphone").font(.subheadline).foregroundStyle(aquaColor)
            note("Keep NodeLift open while working. Locking the screen or moving to the background pauses the session.")
        }
    }

    private var draftSummary: some View {
        card {
            Text(T("Draft model")).font(.headline).accessibilityAddTraits(.isHeader)
            Text(model.engineStatus.resolve(model.language)).font(.body).foregroundStyle(aquaColor)
                .fixedSize(horizontal: false, vertical: true)
            Label(T(model.engineEnabled ? "LLM proposals · ON" : "LLM proposals · OFF"), systemImage: model.engineEnabled ? "checkmark.shield" : "pause.circle")
                .font(.subheadline)
            note("Draft readiness is separate from measured contribution. See the computer for assessment and accepted tokens.")
            Button { modelSetupFocused = false; requestModelFocus = true; selectedTab = 2 } label: {
                Label(T("Set up draft"),systemImage:"slider.horizontal.3").frame(maxWidth:.infinity)
            }.buttonStyle(NodeLiftButtonStyle()).disabled(model.diagnosticRunning)
        }
    }

    private var homePage: some View {
        page {
            header
            sessionCard
            if !model.hasSavedSession {
                note("Start by pairing this phone with your computer.")
                Button { showScanner = true } label: {
                    Label(T("Scan QR"),systemImage:"qrcode.viewfinder").frame(maxWidth:.infinity)
                }.buttonStyle(NodeLiftButtonStyle(primary:true)).disabled(settingsLocked)
            } else if model.running {
                Button { model.pause() } label: {
                    Label(T("Pause node"),systemImage:"pause.fill").frame(maxWidth:.infinity)
                }.buttonStyle(NodeLiftButtonStyle(primary:true))
            } else {
                note("Your pairing is saved. Resume to make this phone available.")
                Button { model.connect(newTicket:false) } label: {
                    Label(T("Resume session"),systemImage:"play.fill").frame(maxWidth:.infinity)
                }.buttonStyle(NodeLiftButtonStyle(primary:true)).disabled(settingsLocked)
            }
            if model.hasSavedSession { draftSummary }
            note("You choose when this phone contributes. RAM is not pooled automatically.")
        }
    }

    private var activityPage: some View {
        page {
            Text(T("Activity")).font(.largeTitle.weight(.semibold)).accessibilityAddTraits(.isHeader)
            Text(T("Measurements and support")).font(.headline).foregroundStyle(.secondary)
            card {
                Text(T("Last measurement")).font(.headline)
                Text(model.lastResult.resolve(model.language)).foregroundStyle(aquaColor).font(.body)
                    .accessibilityIdentifier("last-result").fixedSize(horizontal:false,vertical:true)
                note("Synthetic CPU tests do not indicate tokens/s. Draft proposal time is not the speed of a complete LLM response.")
            }
            card {
                Text(T("Device details")).font(.headline)
                Text(model.telemetry.resolve(model.language)).font(.body).foregroundStyle(.secondary)
                    .fixedSize(horizontal:false,vertical:true)
            }
            Button {
                do {
                    diagnosticShare=DiagnosticShare(url:try Diagnostics.shared.export())
                    diagnosticFeedback="Diagnostic report prepared. Choose where to save or share it."
                } catch { diagnosticFeedback="Unable to export diagnostics. Try again." }
            } label: {
                Label(T("Export diagnostics"),systemImage:"square.and.arrow.up").frame(maxWidth:.infinity)
            }.buttonStyle(NodeLiftButtonStyle()).accessibilityIdentifier("activity-export-diagnostics")
            if !diagnosticFeedback.isEmpty { Text(T(diagnosticFeedback)).font(.subheadline).foregroundStyle(aquaColor) }
            note("Logs stay on this phone until you choose to share them.")
        }
    }

    private var settingsPage: some View {
        ScrollViewReader { proxy in
        page {
            Text(T("Settings")).font(.largeTitle.weight(.semibold)).accessibilityAddTraits(.isHeader)
            Picker(T("Language"),selection:$model.language) {
                Text("English").tag("en");Text("简体中文").tag("zh-Hans");Text("Italiano").tag("it")
            }.frame(minHeight:44).tint(aquaColor).accessibilityIdentifier("language-picker")
            Button { showAbout=true } label: {
                Label(T("About & References"),systemImage:"info.circle").frame(maxWidth:.infinity)
            }.buttonStyle(NodeLiftButtonStyle()).accessibilityIdentifier("open-about")
            engineCard.id("model-setup")
            limitsCard
            pairingCard
            Text(CompanionBuild.description(model.language)).font(.caption).foregroundStyle(.secondary)
            note("Experimental companion")
            note("Capacity sharding is not implemented. Physical-phone inference speedup remains unproven.")
        }.task(id:requestModelFocus) {
            guard requestModelFocus else {return}
            await Task.yield()
            proxy.scrollTo("model-setup",anchor:.top)
            modelSetupFocused=true
            requestModelFocus=false
        }
        }
    }

    private func page<Content:View>(@ViewBuilder content:()->Content)->some View {
        ScrollView {
            VStack(alignment:.leading,spacing:18,content:content).padding(20).frame(maxWidth:700)
        }.frame(maxWidth:.infinity).background(canvasColor)
    }

    private var engineCard: some View {
        card {
            eyebrow(T("01 / DRAFT ENGINE"))
            HStack(alignment: .firstTextBaseline) {
                Text(T("Draft model")).font(.title3.weight(.semibold)).accessibilityAddTraits(.isHeader).accessibilityFocused($modelSetupFocused)
                Spacer()
                Text(T("EXPERIMENTAL")).font(.caption.monospaced()).foregroundStyle(amberColor)
            }
            Text(model.engineStatus.resolve(model.language)).font(.subheadline).foregroundStyle(aquaColor)
                .accessibilityIdentifier("engine-status").fixedSize(horizontal: false, vertical: true)
            Toggle(isOn: $model.engineEnabled) {
                VStack(alignment: .leading, spacing: 5) {
                    Text(T(model.engineEnabled ? "LLM proposals · ON" : "LLM proposals · OFF")).font(.subheadline.weight(.semibold))
                    Text(T("Your paired Mac can send context to the draft. The main model on your Mac verifies the proposals."))
                        .font(.footnote).foregroundStyle(.secondary)
                }
            }.tint(aquaColor).disabled(model.importingModel || model.diagnosticRunning)
                .onChange(of: model.engineEnabled) { _, _ in
                    // A changed consent stops existing work; resumption is deliberate.
                    if model.running { model.pause() }
                }
            note(T("Changing permission pauses an active session. Resume when you want to participate."))
            Divider().overlay(lineColor)
            Button { model.downloadDraft() } label: {
                Label(T("Download draft from Mac and enable"), systemImage: "arrow.down.circle")
                    .frame(maxWidth: .infinity)
            }.buttonStyle(NodeLiftButtonStyle(primary: true))
                .disabled(!model.hasSavedSession || model.importingModel || model.diagnosticRunning)
                .accessibilityIdentifier("download-draft")
            if model.hasTransferredDraft {
                Button(T("Use transferred draft and enable")) { model.downloadDraft(useTransferred: true) }
                    .buttonStyle(NodeLiftButtonStyle())
                    .disabled(!model.hasSavedSession || model.importingModel || model.diagnosticRunning)
                    .accessibilityIdentifier("use-transferred-draft")
            }
            note(T("The session pauses during setup. The draft is verified against your paired Mac. Resume after verification and keep the app open."))
            Button { importError = nil; showModelImporter = true } label: {
                Label(model.importingModel ? T("Importing…") : T("Import GGUF draft"), systemImage: "square.and.arrow.down")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(NodeLiftButtonStyle()).disabled(settingsLocked)
            if model.importingModel {
              if model.downloadingDraft {
                ProgressView(value: model.downloadProgress).tint(aquaColor).frame(maxWidth: .infinity)
                    .accessibilityLabel(T("Importing model"))
                Button(T("Cancel draft transfer")) { model.cancelDraftTransfer() }
                    .buttonStyle(NodeLiftButtonStyle())
              } else {
                ProgressView().tint(aquaColor).accessibilityLabel(T("Importing model"))
              }
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
            DisclosureGroup(T("Resource limits"),isExpanded:$resourcesExpanded) {
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
                }.frame(minHeight:44).disabled(settingsLocked)
                Picker(T("Context tokens"), selection: $model.engineContext) {
                    ForEach([512, 1024, 2048, 4096], id: \.self) { value in
                        Text("\(value)").tag(value)
                    }
                }.tint(aquaColor).disabled(settingsLocked)
            }
            }.tint(aquaColor)
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
                .frame(minHeight:44)
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
                    DisclosureGroup(T("Manual pairing"),isExpanded:$manualExpanded) {
                    TextEditor(text: $model.ticketText).font(.body.monospaced())
                        .frame(height: 90).scrollContentBackground(.hidden).padding(8)
                        .background(canvasColor, in: RoundedRectangle(cornerRadius: 7))
                        .accessibilityLabel(T("NodeLift invitation")).autocorrectionDisabled()
                        .textInputAutocapitalization(.never).disabled(settingsLocked)
                    Button { acceptPairingCode(model.ticketText) } label: {
                        Text(T("Pair and activate node")).frame(maxWidth: .infinity)
                    }
                    .buttonStyle(NodeLiftButtonStyle(primary: true))
                    .disabled(settingsLocked || model.ticketText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }.tint(aquaColor)
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
            let computer=URLComponents(string:ticket.url)?.host ?? ticket.url
            let characters=Array(ticket.sha256)
            let fingerprint=stride(from:0,to:characters.count,by:4).map {String(characters[$0..<min($0+4,characters.count)])}.joined(separator:" ")
            pairingIdentity=Message("Computer: {0} · Identity: {1}",computer,"\n"+fingerprint).resolve(model.language)
            pairingIdentitySpoken=Message("Computer: {0} · Identity: {1}",computer,characters.map(String.init).joined(separator:" ")).resolve(model.language)
            confirmPairing = true
        } catch { model.status = Message(error.localizedDescription) }
    }

    var body: some View {
        TabView(selection:$selectedTab) {
            homePage.tabItem { Label(T("Home"),systemImage:"house") }.tag(0)
            activityPage.tabItem { Label(T("Activity"),systemImage:"waveform.path.ecg") }.tag(1)
            settingsPage.tabItem { Label(T("Settings"),systemImage:"gearshape") }.tag(2)
        }.tint(aquaColor)
        .onChange(of:connectionLabel) {_,value in announce(value)}
        .onChange(of:model.assessmentStatus.resolve(model.language)) {_,value in announce(value)}
        .onChange(of:primaryActionLabel) {_,value in announce(value)}
        .sheet(item:$diagnosticShare) { item in DiagnosticShareSheet(url:item.url) }
        .onAppear { incidentNotice = Diagnostics.shared.hasPreviousIncident }
        .sheet(item: $releaseDetails) { ReleaseNotesView(details:$0,language:model.language) }
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
                if let value = pairingCode, !settingsLocked { model.ticketText = value; selectedTab = 0; model.connect(newTicket: true) }
                pairingCode = nil
            }
        } message: { Text(pairingIdentity).accessibilityLabel(pairingIdentitySpoken) }
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
    @State private var releaseDetails:ReleaseDetails?
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
                        Button(T("View release notes & download")) { releaseDetails=updates.details }
                            .buttonStyle(NodeLiftButtonStyle()).disabled(updates.checking || updates.details == nil)
                            .accessibilityIdentifier("view-release-notes")
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
                .sheet(item: $releaseDetails) { ReleaseNotesView(details:$0,language:language) }
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



private struct ReleaseNotesView:View {
    let details:ReleaseDetails
    let language:String
    @ObservedObject private var updates=UpdateMonitor.shared
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL
    @State private var linkError=false
    private var valid:Bool { !updates.checking && updates.details?.id==details.id }
    private func T(_ key:String)->String {Message(key).resolve(language)}
    private func heading(_ key:String)->some View {Text(T(key)).font(.title3.weight(.semibold)).accessibilityAddTraits(.isHeader)}
    var body:some View {
        NavigationStack {
            ScrollView {
                VStack(alignment:.leading,spacing:16) {
                    Text(Message("Version {0} · build {1}",details.release.version,details.release.build).resolve(language)).font(.headline).foregroundStyle(aquaColor)
                    Text(T("Published (UTC)")+": "+details.date).font(.subheadline)
                    Text(details.title).font(.title2.weight(.semibold))
                    Text(T("Release notes are published in English.")).font(.footnote).foregroundStyle(.secondary)
                    ForEach(Array(details.changes.enumerated()),id:\.offset){_,value in Text("• "+value).fixedSize(horizontal:false,vertical:true)}
                    heading("Validation");Text(details.validation)
                    heading("Limitations");Text(details.limitations)
                    heading("Download details");Text(details.artifact).font(.subheadline.monospaced())
                    Text(Message("Artifact size: {0} bytes",details.bytes).resolve(language))
                    Text("SHA-256\n"+details.sha256).font(.footnote.monospaced()).textSelection(.enabled)
                    Text(T("This hash is published metadata. NodeLift does not verify the downloaded file when your browser downloads it.")).font(.footnote)
                    Text(T("This IPA is unsigned. Download it to your Mac, then sign and provision it for your iPhone with Xcode. A browser download cannot install it. No automatic installation is available."))
                    Button(T("Download unsigned IPA in browser")) {
                        guard valid else{return}
                        linkError=false;openURL(details.url){accepted in linkError = !accepted}
                    }.buttonStyle(NodeLiftButtonStyle()).disabled(!valid).accessibilityIdentifier("download-release")
                    if !valid {Text(T("Release details need a new check. Close this view and choose Check now.")).foregroundStyle(amberColor)}
                    if linkError {Text(T("Unable to open this link. Open the official website in your browser.")).foregroundStyle(amberColor)}
                }.frame(maxWidth:.infinity,alignment:.leading).padding(20)
            }.background(canvasColor).navigationTitle(T("Release notes")).navigationBarTitleDisplayMode(.inline)
                .toolbar{ToolbarItem(placement:.confirmationAction){Button(T("Close")){dismiss()}}}
        }.preferredColorScheme(.dark)
    }
}
