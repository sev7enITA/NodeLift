import Foundation
import UIKit
import Network
import os

@MainActor final class NodeModel: ObservableObject {
    @Published var status = "Pronto per l’associazione"
    @Published var running = false
    @Published var lastResult = "Nessuna misura eseguita"
    @Published var telemetry = ""
    @Published var hasSavedSession = Vault.load() != nil
    @Published var ticketText = ""
    private var task: Task<Void, Never>?
    private var client: NodeClient?
    private var generation = UUID()
    private var transport = "non rilevato"
    private let monitor = NWPathMonitor()

    init() {
        UIDevice.current.isBatteryMonitoringEnabled = true
        monitor.pathUpdateHandler = { [weak self] path in
            let name = path.usesInterfaceType(.wifi) ? "Wi-Fi / hotspot" : path.usesInterfaceType(.wiredEthernet) ? "Ethernet / USB" : path.usesInterfaceType(.cellular) ? "cellulare" : "altro"
            Task { @MainActor in self?.transport = name }
        }
        monitor.start(queue: DispatchQueue(label:"dev.nodelift.network"))
        _ = capabilities()
    }
    func capabilities() -> [String: Any] {
        let info = ProcessInfo.processInfo
        let thermal: String
        switch info.thermalState { case .nominal: thermal="nominal"; case .fair: thermal="fair"; case .serious: thermal="serious"; case .critical: thermal="critical"; @unknown default: thermal="unknown" }
        let available = os_proc_available_memory()
        var system = utsname(); uname(&system)
        let machine = withUnsafePointer(to:&system.machine) { pointer in pointer.withMemoryRebound(to:CChar.self, capacity:1) { String(cString:$0) } }
        #if targetEnvironment(simulator)
        let osName = "iOS Simulator \(UIDevice.current.systemVersion) — NOT physical device"
        #else
        let osName = "\(UIDevice.current.systemName) \(UIDevice.current.systemVersion)"
        #endif
        telemetry = String(format:"%@\nRAM fisica: %.1f GiB · margine processo: %.1f GiB\n%@ · termica: %@", machine, Double(info.physicalMemory)/1073741824, Double(available)/1073741824, transport, thermal)
        return ["model":machine,"os":osName,"app_version":"0.1.0","physical_memory_bytes":info.physicalMemory,"available_memory_bytes":available,"cpu_cores":info.activeProcessorCount,"battery_percent":max(0,Int(UIDevice.current.batteryLevel*100)),"thermal":thermal,"transport":transport,"lifecycle":"foreground-only","supported_jobs":["network","network_paced","cpu"]]
    }
    func connect(newTicket: Bool) {
        guard !running else { return }
        running = true; status = "Connessione al computer…"
        let current = UUID(); generation = current
        let text = ticketText
        task = Task {
            do {
                var credentials: Credentials
                if newTicket {
                    let ticket = try JSONDecoder().decode(Ticket.self, from: Data(text.utf8))
                    try ticket.validate()
                    guard let expiry = ticket.expires_at, expiry > Date().timeIntervalSince1970, let invite = ticket.invite else { throw NodeError.message("Invito scaduto: creane uno nuovo") }
                    let pairingClient = try NodeClient(ticket: ticket)
                    client = pairingClient
                    let response = try await pairingClient.json("/v1/pair",body:["invite":invite,"name":UIDevice.current.model + " · NodeLift","capabilities":capabilities()])
                    guard let token = response["token"] as? String, let id = response["node_id"] as? String else { throw NodeError.message("Associazione non riuscita") }
                    var saved = ticket; saved.invite = nil; saved.expires_at = nil
                    credentials = Credentials(pairing:saved,token:token,node_id:id)
                    try Vault.save(credentials); hasSavedSession=true; ticketText=""
                    pairingClient.cancel()
                } else {
                    guard let stored = Vault.load() else { throw NodeError.message("Incolla un invito dal computer") }
                    credentials = stored
                }
                try Task.checkCancellation()
                let c = try NodeClient(ticket:credentials.pairing,token:credentials.token); client=c
                var errors=0
                while !Task.isCancelled {
                    do {
                        let value = try await c.json("/v1/heartbeat",body:capabilities())
                        errors=0;status="Connesso · in attesa di una misura"
                        if let job=value["job"] as? [String:Any], let id=job["id"] as? String, let kind=job["kind"] as? String {
                            status = kind.hasPrefix("network") ? "Misura rete in corso…" : "Calibrazione CPU sintetica…"
                            let result = await Benchmarks.run(client:c,id:id,kind:kind)
                            try Task.checkCancellation()
                            _ = try await c.json("/v1/result",body:result)
                            lastResult = result["note"] as? String ?? "Misura completata"
                        }
                    } catch {
                        try Task.checkCancellation()
                        errors += 1; status="Connessione interrotta · tentativo \(errors)/3"
                        if errors>=3 { throw error }
                    }
                    try await Task.sleep(nanoseconds:3_000_000_000)
                }
            } catch { if !Task.isCancelled && generation == current { status=error.localizedDescription } }
            if generation == current { running=false }
        }
    }
    func pause() {
        generation = UUID()
        task?.cancel();client?.cancel();client=nil;running=false
        status="In pausa · nessun lavoro delegato"
    }
    func forget() { pause();Vault.clear();hasSavedSession=false;status="Computer dimenticato" }
}

enum Benchmarks {
    static func now() -> Double { ProcessInfo.processInfo.systemUptime*1000 }
    static func check(_ started:Double) throws {
        try Task.checkCancellation()
        guard now()-started < 90000 else { throw NodeError.message("Tempo massimo della misura superato") }
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
    static func run(client:NodeClient,id:String,kind:String) async -> [String:Any] {
        var samples=[[String:Any]]();var state="completed";var note=""
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
                    guard data.count==64 else { throw NodeError.message("Payload incompleto") }
                    samples.append(["kind":"rtt","bytes":64,"ms":ms,"pace_ms":pace,"connection_id":client.lastConnectionId])
                }
                }
                for size in [16384,1048576] {
                    let payload=Data((0..<size).map { UInt8(($0*31+17)&255) })
                    for _ in 0..<4 {
                        try check(started);var t=now();let data=try await client.bytes("/v1/probe?size=\(size)");var ms=now()-t
                        guard data.count==size else { throw NodeError.message("Payload incompleto") }
                        samples.append(["kind":"download","bytes":size,"ms":ms])
                        try check(started);t=now();let response=try await client.bytes("/v1/upload",body:payload,raw:true);ms=now()-t
                        let reply=try JSONSerialization.jsonObject(with:response) as? [String:Any]
                        guard reply?["bytes"] as? Int == size else { throw NodeError.message("Upload incompleto") }
                        samples.append(["kind":"upload","bytes":size,"ms":ms])
                    }
                }
                let rtt=samples.filter { $0["kind"] as? String == "rtt" }.compactMap { $0["ms"] as? Double }.sorted()
                note=paced ? "600 RTT: gruppi 0/30/60ms da confrontare separatamente. Test HTTPS applicativo, non LLM." : String(format:"Diagnostica breve · p50 %.2f ms · p95 esplorativo %.2f ms. Non è un benchmark LLM.",rtt[15],rtt[30])
            } else if kind == "cpu" {
                let sample=try await cpu();samples.append(sample)
                note="FP32 matvec 256×256, Swift, singolo thread: \(sample["iterations"] ?? 0) iterazioni. Non predice token/s."
            } else { throw NodeError.message("Job non supportato") }
        } catch {
            state=Task.isCancelled ? "cancelled" : error.localizedDescription == "thermal_pause" ? "thermal_pause" : "failed"
            note=error.localizedDescription
        }
        return ["job_id":id,"status":state,"samples":samples,"note":note]
    }
}
