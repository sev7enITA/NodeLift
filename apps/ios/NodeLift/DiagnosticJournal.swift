import Foundation

enum DiagnosticEvent:String {
    case appStart, previousInterruptionUnknown, sessionStart, sessionConnected, sessionRetry, sessionFailed, sessionStop
    case cameraOpen, cameraReady, cameraFailed, cameraResult, modelLoading, modelReady, modelFailed, jobFailed, thermalPause
    case updateCheck, updateAvailable, updateCurrent, updateFailed, exportFailed, systemCrash, systemHang
    case draftDiscarded
}

/// Only stable event names and numeric OS codes can enter the journal. No arbitrary text.
final class DiagnosticJournal {
    static let retention:TimeInterval = 7*24*60*60
    static let limit = 131072
    private let directory:URL
    private let lock=NSRecursiveLock()
    private let clock:()->Date
    private let build:Int
    private var lastPrune=Date.distantPast
    init(directory:URL,build:Int=0,clock:@escaping ()->Date = Date.init) {self.directory=directory;self.build=build;self.clock=clock}
    private func prune() {
        let now=clock()
        guard now<lastPrune || now.timeIntervalSince(lastPrune)>=3600 else{return}
        lastPrune=now
        for url in files {
            guard let attrs=try? FileManager.default.attributesOfItem(atPath:url.path),let size=attrs[.size] as? NSNumber else{continue}
            if size.intValue>Self.limit {try? FileManager.default.removeItem(at:url);continue}
            guard let data=try? Data(contentsOf:url),let text=String(data:data,encoding:.utf8) else{continue}
            let lines=text.split(separator:"\n")
            let kept=lines.filter { line in
                guard let object=try? JSONSerialization.jsonObject(with:Data(line.utf8)) as? [String:Any],let time=object["time"] as? Double else{return false}
                return time>=now.timeIntervalSince1970-Self.retention && time<=now.timeIntervalSince1970
            }
            if kept.isEmpty {try? FileManager.default.removeItem(at:url)}
            else if kept.count != lines.count {try? Data((kept.joined(separator:"\n")+"\n").utf8).write(to:url,options:.atomic)}
        }
    }
    private var files:[URL] {(0...2).map{directory.appendingPathComponent("events-\($0).jsonl")}}
    @discardableResult func clear()->Bool {
        lock.lock();defer{lock.unlock()}
        files.forEach{try? FileManager.default.removeItem(at:$0)}
        return files.allSatisfy{!FileManager.default.fileExists(atPath:$0.path)}
    }
    func entries()->[[String:Any]] {
        lock.lock();defer{lock.unlock()}
        prune()
        let now=clock().timeIntervalSince1970
        return files.reversed().flatMap { url -> [[String:Any]] in
            guard let attrs=try? FileManager.default.attributesOfItem(atPath:url.path),let size=attrs[.size] as? NSNumber,size.intValue<=Self.limit,
                  let data=try? Data(contentsOf:url),let text=String(data:data,encoding:.utf8) else{return []}
            return text.split(separator:"\n").compactMap {
                guard let object=try? JSONSerialization.jsonObject(with:Data($0.utf8)) as? [String:Any],
                      let time=object["time"] as? Double,time>=now-Self.retention,time<=now else{return nil}
                return object
            }
        }
    }
    func append(_ event:DiagnosticEvent,code:Int?=nil) {
        lock.lock();defer{lock.unlock()}
        do {
            try FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true)
            prune()
            let manager=FileManager.default
            for url in files {
                if let attrs=try? manager.attributesOfItem(atPath:url.path),
                   ((attrs[.size] as? NSNumber)?.intValue ?? 0 > Self.limit || (attrs[.modificationDate] as? Date ?? clock()) < clock().addingTimeInterval(-Self.retention)) {try? manager.removeItem(at:url)}
            }
            var object:[String:Any]=["time":clock().timeIntervalSince1970,"event":event.rawValue,"reporter_build":build]
            if let code {object["code"]=code}
            var data=try JSONSerialization.data(withJSONObject:object,options:[.sortedKeys]);data.append(10)
            var old=(try? Data(contentsOf:files[0])) ?? Data()
            if old.count+data.count>Self.limit {
                try? manager.removeItem(at:files[2]);try? manager.moveItem(at:files[1],to:files[2]);try? manager.moveItem(at:files[0],to:files[1]);old=Data()
            }
            old.append(data)
            #if os(iOS)
            try old.write(to:files[0],options:[.atomic,.completeFileProtectionUntilFirstUserAuthentication])
            #else
            try old.write(to:files[0],options:.atomic)
            #endif
        } catch { /* Logging must never interrupt the worker or mask its original error. */ }
    }
}
