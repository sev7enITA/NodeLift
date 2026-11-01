import Foundation

@main struct SupportPolicyCheck {
    static func main() throws {
        func release(_ version:String,_ build:Int)->CompanionRelease {CompanionRelease(version:version,build:build)!}
        precondition(release("0.10.0",1)>release("0.9.9",99))
        precondition(release("0.2.6",9)>release("0.2.6",8))
        precondition(release("0.2.5",99)<release("0.2.6",8))
        for value in ["v0.2.6","0.2","0.2.6-beta","https://bad.test","9999999.0.0"] {precondition(CompanionRelease(version:value,build:1)==nil)}
        let start=1000000.0
        precondition(!UpdatePolicy.due(now:start+UpdatePolicy.week-1,success:start,attempt:start))
        precondition(UpdatePolicy.due(now:start+UpdatePolicy.week,success:start,attempt:start))
        precondition(!UpdatePolicy.due(now:start+100,success:0,attempt:start))
        precondition(UpdatePolicy.due(now:start+UpdatePolicy.retry,success:0,attempt:start))
        precondition(UpdatePolicy.due(now:start-1,success:start,attempt:start))
        let directory=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer{try? FileManager.default.removeItem(at:directory)}
        var now=Date()
        let journal=DiagnosticJournal(directory:directory,clock:{now})
        // No free-form data API exists: only stable event enumeration and numeric codes.
        for _ in 0..<9000 {journal.append(.sessionRetry,code:-1001)}
        let files=try FileManager.default.contentsOfDirectory(at:directory,includingPropertiesForKeys:[.fileSizeKey])
        precondition(files.count<=3)
        for file in files {let size=try file.resourceValues(forKeys:[.fileSizeKey]).fileSize!;precondition(size<=DiagnosticJournal.limit)}
        precondition(!DiagnosticJournal(directory:directory,clock:{now}).entries().isEmpty)
        precondition(journal.entries().allSatisfy{Set($0.keys)==["time","event","code","reporter_build"]})
        now=now.addingTimeInterval(DiagnosticJournal.retention+1)
        precondition(journal.entries().isEmpty)
        journal.append(.appStart);precondition(journal.entries().count==1)
        journal.clear();precondition(journal.entries().isEmpty)
        print("iOS support policies: numeric release ordering, weekly deadline/retry, clock correction, journal privacy/rotation/restart/expiry/clear passed.")
    }
}
