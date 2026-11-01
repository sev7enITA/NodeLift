import Foundation
import UIKit
import MetricKit

/// Local-only support journal. MetricKit payloads are reduced to numeric codes, never exported raw.
final class Diagnostics:NSObject,MXMetricManagerSubscriber {
    static let shared=Diagnostics()
    private let defaults=UserDefaults.standard
    private let lock=NSRecursiveLock()
    private var started=false
    private let directory:URL
    private let journal:DiagnosticJournal
    var hasPreviousIncident:Bool {defaults.bool(forKey:"diagnostics-incident")}
    private override init() {
        directory=FileManager.default.urls(for:.applicationSupportDirectory,in:.userDomainMask)[0].appendingPathComponent("Diagnostics",isDirectory:true)
        journal=DiagnosticJournal(directory:directory,build:Int(Bundle.main.object(forInfoDictionaryKey:"CFBundleVersion") as? String ?? "") ?? 0)
        super.init()
    }
    func start() {
        lock.lock();defer{lock.unlock()}
        guard !started else{return};started=true
        try? FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true)
        var url=directory;var values=URLResourceValues();values.isExcludedFromBackup=true;try? url.setResourceValues(values)
        if defaults.bool(forKey:"diagnostics-active") {
            journal.append(.previousInterruptionUnknown);defaults.set(true,forKey:"diagnostics-incident")
        }
        journal.append(.appStart)
        cleanExport()
        MXMetricManager.shared.add(self)
    }
    func setActive(_ active:Bool) {defaults.set(active,forKey:"diagnostics-active")}
    func record(_ event:DiagnosticEvent,error:Error?=nil) {
        // NSError descriptions/domains can include URLs, paths or model responses; numeric code only.
        journal.append(event,code:error.map{($0 as NSError).code})
    }
    func didReceive(_ payloads:[MXDiagnosticPayload]) {
        for payload in payloads {
            for crash in payload.crashDiagnostics ?? [] {journal.append(.systemCrash,code:crash.signal?.intValue);defaults.set(true,forKey:"diagnostics-incident")}
            for _ in payload.hangDiagnostics ?? [] {journal.append(.systemHang);defaults.set(true,forKey:"diagnostics-incident")}
        }
    }
    private var exportURL:URL {FileManager.default.temporaryDirectory.appendingPathComponent("NodeLift-diagnostics.json")}
    private func cleanExport(){try? FileManager.default.removeItem(at:exportURL)}
    func clear()->Bool {
        let cleared=journal.clear();cleanExport()
        guard cleared && !FileManager.default.fileExists(atPath:exportURL.path) else{return false}
        defaults.set(false,forKey:"diagnostics-incident");return true
    }
    func export() throws -> URL {
        let object:[String:Any]=[
            "schema":"nodelift-diagnostics-v1","platform":"ios",
            "version":Bundle.main.object(forInfoDictionaryKey:"CFBundleShortVersionString") as? String ?? "unknown",
            "build":Bundle.main.object(forInfoDictionaryKey:"CFBundleVersion") as? String ?? "unknown",
            "os":ProcessInfo.processInfo.operatingSystemVersionString,
            "thermal":ProcessInfo.processInfo.thermalState.rawValue,
            "events":journal.entries(),
            "scope":"Local allowlisted events and numeric error codes. No prompts, credentials, QR data, addresses, model paths or raw MetricKit payloads. A previous interruption is not proof of a crash. OS diagnostics may be delayed or absent."
        ]
        do {
            let data=try JSONSerialization.data(withJSONObject:object,options:[.prettyPrinted,.sortedKeys])
            try data.write(to:exportURL,options:[.atomic,.completeFileProtectionUntilFirstUserAuthentication])
            return exportURL
        } catch {record(.exportFailed,error:error);throw error}
    }
}
