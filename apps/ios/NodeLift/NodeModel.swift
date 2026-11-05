import Foundation
import UIKit
import Network
import os
import CryptoKit

@MainActor final class NodeModel: ObservableObject {
    @Published var language = AppLanguage.normalize(UserDefaults.standard.string(forKey: "nodelift-language")) {
        didSet { UserDefaults.standard.set(AppLanguage.normalize(language), forKey: "nodelift-language") }
    }
    @Published var status: Message = "Ready to pair"
    @Published var running = false
    @Published private var transportConnected = false
    var connected: Bool {
        get { transportConnected && (contactAgeSeconds.map { $0 < 20 } ?? false) }
        set { transportConnected=newValue }
    }
    var contactAgeSeconds: Int? { client?.contactAgeSeconds }
    @Published private(set) var connectionTick = 0
    private var freshnessTimer: Timer?
    @Published var assessmentStatus: Message = ""
    @Published var diagnosticRunning = false
    @Published var lastResult: Message = "No measurements yet"
    @Published var telemetry: Message = ""
    @Published var hasSavedSession = Vault.load() != nil
    @Published var ticketText = ""
    @Published var engineEnabled = false
    @Published var engineStatus: Message = "Import the GGUF draft selected on your Mac"
    @Published var engineThreads = 4
    @Published var engineContext = 2048
    @Published var engineMetal = true
    @Published var minimumBattery = 25.0
    @Published var importingModel = false
    @Published var downloadProgress = 0.0
    @Published private(set) var downloadingDraft = false
    private var modelTransfer: Task<Void, Never>?
    private var transferID = UUID()
    var transferredDraftURL: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("NodeLift-draft.gguf")
    }
    var hasTransferredDraft: Bool { FileManager.default.fileExists(atPath: transferredDraftURL.path) }
    private var draft: NativeDraft?
    private var draftSHA = ""
    private var draftFingerprint = ""
    private var task: Task<Void, Never>?
    private var client: NodeClient?
    private var generation = UUID()
    private var transport = "not detected"
    private var thermalObserver: NSObjectProtocol?
    private let monitor = NWPathMonitor()

    init() {
        UIDevice.current.isBatteryMonitoringEnabled = true
        freshnessTimer=Timer.scheduledTimer(withTimeInterval:1,repeats:true) { [weak self] _ in
            Task { @MainActor in self?.connectionTick += 1 }
        }
        monitor.pathUpdateHandler = { [weak self] path in
            let name = path.usesInterfaceType(.wifi) ? "Wi-Fi / hotspot" : path.usesInterfaceType(.wiredEthernet) ? "Ethernet / USB" : path.usesInterfaceType(.cellular) ? "cellular" : "other"
            Task { @MainActor in self?.transport = name }
        }
        monitor.start(queue: DispatchQueue(label:"dev.nodelift.network"))
        thermalObserver=NotificationCenter.default.addObserver(forName:ProcessInfo.thermalStateDidChangeNotification,object:nil,queue:.main) { [weak self] _ in
            Task { @MainActor in
                guard let self, !self.permitsDraft else {return}
                Diagnostics.shared.record(.thermalPause);self.draft?.cancel();self.engineStatus="Thermal pause · let the device cool down"
            }
        }
        _ = capabilities()
    }
    deinit {freshnessTimer?.invalidate();if let thermalObserver {NotificationCenter.default.removeObserver(thermalObserver)}}
    private func updateAssessment(_ value:[String:Any]?) {
        let key:String
        switch value?["phase"] as? String {
        case "network":key="Assessment: checking the connection"
        case "cpu":key="Assessment: calibrating the CPU"
        case "pending":key="Assessment queued by your computer"
        case "deferred":
            switch value?["reason"] as? String {
            case "low_battery":key="Assessment waiting: battery below 20%"
            case "thermal":key="Assessment waiting: let the device cool down"
            case "host_busy":key="Assessment waiting: your computer is busy"
            default:key="Assessment waiting: another diagnostic is running"
            }
        case "completed":key="Basic checks finished. LLM usefulness still needs testing."
        case "failed":key="Assessment incomplete. Check Activity and the desktop results."
        case "unsupported":key="Automatic diagnostics are not supported by this companion."
        default:key=""
        }
        assessmentStatus=Message(key)
    }
    func capabilities() -> [String: Any] {
        let info = ProcessInfo.processInfo
        let thermal: String
        switch info.thermalState { case .nominal: thermal="nominal"; case .fair: thermal="fair"; case .serious: thermal="serious"; case .critical: thermal="critical"; @unknown default: thermal="unknown" }
        let available = os_proc_available_memory()
        var system = utsname(); uname(&system)
        let machine = withUnsafePointer(to:&system.machine) { pointer in pointer.withMemoryRebound(to:CChar.self, capacity:1) { String(cString:$0) } }
        #if targetEnvironment(simulator)
        let osName = "iOS Simulator \(UIDevice.current.systemVersion): NOT physical device"
        #else
        let osName = "\(UIDevice.current.systemName) \(UIDevice.current.systemVersion)"
        #endif
        telemetry = Message("{0}\n{1}\n{2}", machine,
            Message("Physical RAM: {0} GiB · process headroom: {1} GiB", String(format:"%.1f",Double(info.physicalMemory)/1073741824),String(format:"%.1f",Double(available)/1073741824)),
            Message("{0} · thermal: {1}",Message(transport),Message(thermal)))
        var value:[String:Any] = ["model":machine,"os":osName,"app_version":Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "unknown","physical_memory_bytes":info.physicalMemory,"available_memory_bytes":available,"cpu_cores":info.activeProcessorCount,"battery_percent":max(0,Int(UIDevice.current.batteryLevel*100)),"thermal":thermal,"transport":transport,"lifecycle":"foreground-only","supported_jobs":["network","network_paced","cpu"]]
        if draft != nil {
            value["draft_timing_version"]=1;value["bounded_lookahead"]=false
            value["native_build"]="timing-v1-0.2.13"
            value["draft_sha256"]=draftSHA;value["tokenizer_fingerprint"]=draftFingerprint
            value["engine_ready"]=engineEnabled && permitsDraft
        }
        return value
    }
    private var permitsDraft:Bool {
        let battery=UIDevice.current.batteryLevel
        let thermal=ProcessInfo.processInfo.thermalState
        return battery>=0 && Double(battery*100)>=minimumBattery && thermal == .nominal && os_proc_available_memory()>268435456
    }
    func importDraft(_ url:URL) {
        guard !running && !importingModel else {return}
        Diagnostics.shared.record(.modelLoading)
        importingModel=true;engineStatus="Importing and verifying SHA-256…"
        Task {
            do { _ = try await NativeDraft.importFile(url);engineStatus="Draft imported · enable the engine and resume the session" }
            catch { Diagnostics.shared.record(.modelFailed,error:error);engineStatus=Message(error.localizedDescription) }
            importingModel=false
        }
    }
    func downloadDraft(useTransferred: Bool = false) {
        guard !importingModel, !diagnosticRunning, let saved = Vault.load() else { return }
        pause()
        engineEnabled = false
        importingModel = true; downloadingDraft = true; downloadProgress = 0
        let identifier = UUID(); transferID = identifier
        engineStatus = "Downloading draft from your computer…"
        let transferred = transferredDraftURL
        Diagnostics.shared.record(.modelLoading)
        modelTransfer = Task {
            do {
                let c = try NodeClient(ticket: saved.pairing, token: saved.token)
                defer { c.cancel() }
                let offer = try await c.draftOffer()
                let transfer = Task.detached(priority: .utility) { [self] () throws -> Void in
                    let source: URL
                    if useTransferred { source = transferred }
                    else {
                        source = try await c.downloadDraft(offer) { fraction in
                            await self.setDownloadProgress(fraction, identifier: identifier)
                        }
                    }
                    defer { if !useTransferred { try? FileManager.default.removeItem(at: source) } }
                    try Task.checkCancellation()
                    _ = try await NativeDraft.importFile(source, expectedSHA: offer.sha256)
                }
                try await withTaskCancellationHandler(operation: { try await transfer.value }, onCancel: { transfer.cancel() })
                try Task.checkCancellation()
                guard transferID == identifier else { return }
                if useTransferred { try? FileManager.default.removeItem(at: transferred) }
                engineEnabled = true
                engineStatus = "Draft verified · proposals enabled · resume the session"
            } catch {
                guard transferID == identifier else { return }
                Diagnostics.shared.record(.modelFailed, error: error)
                engineStatus = Task.isCancelled ? "Draft transfer cancelled" : Message(error.localizedDescription)
            }
            if transferID == identifier { importingModel = false; downloadingDraft = false; modelTransfer = nil }
        }
    }
    private func setDownloadProgress(_ value: Double, identifier: UUID) {
        guard transferID == identifier else { return }
        downloadProgress = value
    }
    func cancelDraftTransfer() {
        guard modelTransfer != nil else { return }
        modelTransfer?.cancel()
        // Keep setup locked until the stream and partial-file cleanup have finished.
    }
    private func prepareDraft() async throws {
        if !engineEnabled {draft?.cancel();draft=nil;return}
        guard draft == nil && permitsDraft else {return}
        Diagnostics.shared.record(.modelLoading);engineStatus="Loading draft…"
        let (sha,_) = try await NativeDraft.checkedModel()
        try Task.checkCancellation()
        let worker=try NativeDraft();draft=worker
        let info=try await worker.call(["op":"load","path":NativeDraft.modelURL.path,
                                        "n_ctx":engineContext,"threads":engineThreads,"gpu_layers":engineMetal ? 999:0])
        try Task.checkCancellation()
        guard let fingerprint=info["tokenizer_fingerprint"] as? String else {throw NodeError.message("Tokenizer missing")}
        draftSHA=sha;draftFingerprint=fingerprint;Diagnostics.shared.record(.modelReady)
        engineStatus=Message("Draft ready · {0} · foreground only",engineMetal ? "Metal":"CPU")
    }
    private func draftResult(_ work:[String:Any]) async -> [String:Any] {
        let started=ProcessInfo.processInfo.systemUptime
        var timing:[String:Any]=["schema_version":1]
        var result:[String:Any]=[:]
        for key in ["id","epoch","prefix_hash","tokenizer_fingerprint","model_sha256","sequence"] {result[key]=work[key]}
        do {
            guard engineEnabled && permitsDraft, let worker=draft else {throw NodeError.message("Draft paused: battery, thermal status or permission")}
            guard work["op"] as? String == "draft", work["model_sha256"] as? String == draftSHA,
                  work["tokenizer_fingerprint"] as? String == draftFingerprint,
                  let prefix=work["prefix"] as? [Int], !prefix.isEmpty, prefix.count<engineContext,
                  let count=work["count"] as? Int, (1...16).contains(count) else {throw NodeError.message("Incompatible model or request")}
            let data=try JSONSerialization.data(withJSONObject:prefix)
            let digest=SHA256.hash(data:data).map{String(format:"%02x",$0)}.joined()
            guard digest==work["prefix_hash"] as? String else {throw NodeError.message("Invalid context")}
            timing["worker_validation_ms"]=(ProcessInfo.processInfo.systemUptime-started)*1000
            let nativeStarted=ProcessInfo.processInfo.systemUptime
            let value=try await worker.call(["op":"draft","prefix":prefix,"count":count])
            timing["worker_native_ms"]=(ProcessInfo.processInfo.systemUptime-nativeStarted)*1000
            if let nativeTiming=value["timing"] as? [String:Any] {
                for (key,value) in nativeTiming where key != "schema_version" {timing[key]=value}
            }
            try Task.checkCancellation()
            guard permitsDraft else {throw NodeError.message("Thermal or battery pause")}
            result["tokens"]=value["tokens"]
            lastResult=Message("Native draft: {0} ms · proposals require verification on your Mac",String(format:"%.1f",value["ms"] as? Double ?? 0))
        } catch {Diagnostics.shared.record(.jobFailed,error:error);result["error"]=error.localizedDescription}
        timing["worker_total_ms"]=(ProcessInfo.processInfo.systemUptime-started)*1000
        result["telemetry"]=timing
        return result
    }
    func connect(newTicket: Bool) {
        guard !running && !importingModel else { return }
        Diagnostics.shared.record(.sessionStart)
        running = true; connected = false; status = "Connecting to your computer…"
        let current = UUID(); generation = current
        let text = ticketText
        task = Task {
            do {
                var credentials: Credentials
                if newTicket {
                    let ticket = try Ticket.decodeInvitation(text)
                    try ticket.validate()
                    guard let expiry = ticket.expires_at, expiry > Date().timeIntervalSince1970, let invite = ticket.invite else { throw NodeError.message("Invitation expired: create a new one") }
                    let pairingClient = try NodeClient(ticket: ticket)
                    client = pairingClient
                    let healthData = try await pairingClient.bytes("/health")
                    let health = try JSONSerialization.jsonObject(with:healthData) as? [String:Any]
                    var body = try Vault.enrollment(scope:health?["pairing_scope"] as? String ?? "", invite:invite, previous:Vault.load())
                    body["invite"] = invite; body["name"] = UIDevice.current.model + " · NodeLift"; body["capabilities"] = capabilities()
                    let response = try await pairingClient.json("/v1/pair",body:body)
                    guard let token = response["token"] as? String, let id = response["node_id"] as? String else { throw NodeError.message("Pairing failed") }
                    var saved = ticket; saved.invite = nil; saved.expires_at = nil
                    credentials = Credentials(pairing:saved,token:token,node_id:id)
                    try Vault.save(credentials); hasSavedSession=true; ticketText=""
                    pairingClient.cancel()
                } else {
                    guard let stored = Vault.load() else { throw NodeError.message("Paste an invitation from your computer") }
                    credentials = stored
                }
                try Task.checkCancellation()
                var c = try NodeClient(ticket:credentials.pairing,token:credentials.token); client=c
                var errors=0
                var lastHeartbeat=0.0
                while !Task.isCancelled {
                    do {
                        do {try await prepareDraft()}
                        catch {try Task.checkCancellation();draft?.cancel();draft=nil;Diagnostics.shared.record(.modelFailed,error:error);engineEnabled=false;engineStatus=Message(error.localizedDescription)}
                        var value:[String:Any]=[:]
                        if ProcessInfo.processInfo.systemUptime-lastHeartbeat>=3 {
                            value = try await c.json("/v1/heartbeat",body:capabilities())
                            lastHeartbeat=ProcessInfo.processInfo.systemUptime
                            try Task.checkCancellation()
                            guard generation == current else { return }
                            updateAssessment(value["assessment"] as? [String:Any])
                            if !connected {Diagnostics.shared.record(.sessionConnected)}
                            connected=true; status="Connected · waiting for work"
                        }
                        if let job=value["job"] as? [String:Any], let id=job["id"] as? String, let kind=job["kind"] as? String {
                            diagnosticRunning=true
                            defer { if generation == current { diagnosticRunning=false } }
                            status = kind.hasPrefix("network") ? "Measuring network…" : "Running synthetic CPU calibration…"
                            let result = await Benchmarks.run(client:c,id:id,kind:kind)
                            try Task.checkCancellation()
                            _ = try await c.json("/v1/result",body:result.payload)
                            lastResult = result.message
                        }
                        if engineEnabled && draft != nil && permitsDraft {
                            let data=try await c.bytes("/v1/engine/poll")
                            let polled=try JSONSerialization.jsonObject(with:data) as? [String:Any]
                            if let work=polled?["work"] as? [String:Any] {
                                let result=await draftResult(work)
                                try Task.checkCancellation()
                                do { _ = try await c.json("/v1/engine/result",body:result) }
                                catch NodeError.discardedDraft {
                                    Diagnostics.shared.record(.draftDiscarded)
                                    lastResult = "Draft proposal expired or superseded"
                                }
                            }
                            errors=0;continue
                        }
                        errors=0
                    } catch {
                        try Task.checkCancellation()
                        Diagnostics.shared.record(.sessionRetry,error:error)
                        connected=false; errors += 1; status=Message("Connection interrupted · attempt {0}/3",errors)
                        if c.ticket.protocol == 2 {
                            draft?.cancel();draft=nil
                            status="Finding your paired computer on the local network…"
                            var recovered:NodeClient?
                            for candidate in try await HostDiscovery.candidates(for:c.ticket) {
                                try Task.checkCancellation()
                                guard generation == current else {return}
                                let probe=try NodeClient(ticket:candidate)
                                client=probe
                                do {
                                    let healthData=try await probe.bytes("/health")
                                    let health=try JSONSerialization.jsonObject(with:healthData) as? [String:Any]
                                    guard health?["host_identity"] as? String == candidate.sha256 else {throw NodeError.message("Invalid computer identity")}
                                    probe.cancel()
                                    try Task.checkCancellation()
                                    let authenticated=try NodeClient(ticket:candidate,token:credentials.token)
                                    client=authenticated
                                    do {
                                        let sessionData=try await authenticated.bytes("/v1/session")
                                        let session=try JSONSerialization.jsonObject(with:sessionData) as? [String:Any]
                                        guard session?["node_id"] as? String == credentials.node_id else {throw NodeError.message("Invalid computer identity")}
                                        try Task.checkCancellation()
                                        guard generation == current else {authenticated.cancel();return}
                                        var updated=credentials;updated.pairing=candidate
                                        try Vault.save(updated);credentials=updated;recovered=authenticated;break
                                    }catch {authenticated.cancel();throw error}
                                }catch {probe.cancel();try Task.checkCancellation()}
                            }
                            if let recovered {c.cancel();c=recovered;client=c;errors=0;lastHeartbeat=0;status="Computer found · reconnecting…"}
                            else {client=c;status="Host not found. Check the local network or discovery permissions.";try await Task.sleep(nanoseconds:UInt64(min(60,1 << min(errors,6)))*1_000_000_000+UInt64.random(in:0...1_000_000_000))}
                        } else if errors>=3 { throw error }
                    }
                    try await Task.sleep(nanoseconds:3_000_000_000)
                }
            } catch { if !Task.isCancelled && generation == current { Diagnostics.shared.record(.sessionFailed,error:error);status=Message(error.localizedDescription) } }
            if generation == current { running=false; connected=false }
        }
    }
    func pause() {
        cancelDraftTransfer()
        if running {Diagnostics.shared.record(.sessionStop)}
        generation = UUID()
        task?.cancel();draft?.cancel();draft=nil;client?.cancel();client=nil;running=false;connected=false;diagnosticRunning=false;assessmentStatus=""
        engineStatus="Engine paused · resume with the app open"
        status="Paused · no delegated work"
    }
    func forget() { pause();Vault.clear();hasSavedSession=false;status="Computer forgotten" }
}

enum Benchmarks {
    static func now() -> Double { ProcessInfo.processInfo.systemUptime*1000 }
    static func check(_ started:Double) throws {
        try Task.checkCancellation()
        guard now()-started < 90000 else { throw NodeError.message("Measurement time limit exceeded") }
        guard ProcessInfo.processInfo.thermalState != .serious && ProcessInfo.processInfo.thermalState != .critical else { throw NodeError.message("thermal_pause") }
    }
    static func cpu() async throws -> [String:Any] {
        let work = Task.detached(priority:.utility) { () throws -> [String:Any] in
            let matrix=(0..<65536).map { Float(($0%97)-48)/97 }
            var vector=(0..<256).map { Float($0%13)/13 }
            var out=[Float](repeating:0,count:256)
            let start=now();var iterations=0
            repeat {
                try check(start)
                vector[iterations%256]=Float(iterations%17)/17
                for row in 0..<256 { var sum:Float=0;for col in 0..<256 { sum += matrix[row*256+col]*vector[col] };out[row]=sum }
                iterations += 1
            } while now()-start < 1500
            return ["kind":"cpu","iterations":iterations,"ms":now()-start,"checksum":abs(Double(out.reduce(0,+)))]
        }
        return try await withTaskCancellationHandler(operation:{try await work.value},onCancel:{work.cancel()})
    }
    static func run(client:NodeClient,id:String,kind:String) async -> (payload: [String:Any], message: Message) {
        var samples=[[String:Any]]();var state="completed";var note: Message=""
        let started=now()
        do {
            try check(started)
            if kind == "network" || kind == "network_paced" {
                _ = try await client.bytes("/v1/probe?size=64")
                let paced = kind == "network_paced"
                for pace in paced ? [0,30,60] : [0] {
                for _ in 0..<(paced ? 200 : 32) {
                    if pace > 0 { try await Task.sleep(nanoseconds:UInt64(pace)*1_000_000) }
                    try check(started);let t=now();let data=try await client.bytes("/v1/probe?size=64");let ms=now()-t
                    guard data.count==64 else { throw NodeError.message("Incomplete payload") }
                    samples.append(["kind":"rtt","bytes":64,"ms":ms,"pace_ms":pace,"connection_id":client.lastConnectionId])
                }
                }
                for size in [16384,1048576] {
                    let payload=Data((0..<size).map { UInt8(($0*31+17)&255) })
                    for _ in 0..<4 {
                        try check(started);var t=now();let data=try await client.bytes("/v1/probe?size=\(size)");var ms=now()-t
                        guard data.count==size else { throw NodeError.message("Incomplete payload") }
                        samples.append(["kind":"download","bytes":size,"ms":ms])
                        try check(started);t=now();let response=try await client.bytes("/v1/upload",body:payload,raw:true);ms=now()-t
                        let reply=try JSONSerialization.jsonObject(with:response) as? [String:Any]
                        guard reply?["bytes"] as? Int == size else { throw NodeError.message("Incomplete upload") }
                        samples.append(["kind":"upload","bytes":size,"ms":ms])
                    }
                }
                let rtt=samples.filter { $0["kind"] as? String == "rtt" }.compactMap { $0["ms"] as? Double }.sorted()
                note=paced ? "600 RTT samples: compare 0/30/60 ms groups separately. Application-level HTTPS test, not LLM inference." : Message("Quick diagnostics · p50 {0} ms · exploratory p95 {1} ms. Not an LLM benchmark.",String(format:"%.2f",rtt[15]),String(format:"%.2f",rtt[30]))
            } else if kind == "cpu" {
                let sample=try await cpu();samples.append(sample)
                note=Message("FP32 matvec 256×256, Swift, single thread: {0} iterations. Does not predict tokens/s.",sample["iterations"] ?? 0)
            } else { throw NodeError.message("Unsupported job") }
        } catch {
            Diagnostics.shared.record(.jobFailed,error:error)
            state=Task.isCancelled ? "cancelled" : error.localizedDescription == "thermal_pause" ? "thermal_pause" : "failed"
            note=Message(error.localizedDescription)
        }
        return (["job_id":id,"status":state,"samples":samples,"note":note.resolve("en")], note)
    }
}
