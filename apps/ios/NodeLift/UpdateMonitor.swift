import Foundation
import Combine

private final class UpdateSessionDelegate:NSObject,URLSessionTaskDelegate {
    func urlSession(_ session:URLSession,task:URLSessionTask,willPerformHTTPRedirection response:HTTPURLResponse,newRequest request:URLRequest,completionHandler:@escaping(URLRequest?)->Void) {completionHandler(nil)}
}

@MainActor final class UpdateMonitor:ObservableObject {
    static let shared=UpdateMonitor()
    @Published private(set) var message:Message="Updates have not been checked yet."
    @Published private(set) var checking=false
    @Published private(set) var available=false
    @Published private(set) var details:ReleaseDetails?
    private let defaults=UserDefaults.standard
    private var started=false
    private var timer:Timer?
    func start(){guard !started else{return};started=true;check()}
    func onResume() {
        if UpdatePolicy.due(now:Date().timeIntervalSince1970,success:defaults.double(forKey:"update-success"),attempt:defaults.double(forKey:"update-attempt")){check()}
        else{schedule()}
    }
    private func schedule() {
        let now=Date().timeIntervalSince1970
        let success=defaults.double(forKey:"update-success");let attempt=defaults.double(forKey:"update-attempt")
        let next=(success>0 && now>=success && now-success<UpdatePolicy.week) ? success+UpdatePolicy.week : attempt+UpdatePolicy.retry
        timer?.invalidate()
        timer=Timer.scheduledTimer(withTimeInterval:max(1,min(UpdatePolicy.week,next-now)),repeats:false){[weak self] _ in Task{@MainActor in self?.onResume()}}
    }
    func check(manual:Bool=false) {
        guard !checking else{return}
        checking=true;available=false;details=nil;message="Checking for updates…";defaults.set(Date().timeIntervalSince1970,forKey:"update-attempt")
        Diagnostics.shared.record(.updateCheck)
        Task {
            let configuration=URLSessionConfiguration.ephemeral
            configuration.timeoutIntervalForRequest=10;configuration.timeoutIntervalForResource=15
            configuration.httpCookieStorage=nil;configuration.urlCredentialStorage=nil;configuration.urlCache=nil
            let session=URLSession(configuration:configuration,delegate:UpdateSessionDelegate(),delegateQueue:nil)
            defer{session.invalidateAndCancel();checking=false;schedule()}
            do {
                let manifest=try await fetch("https://www.fabriziodegni.com/NodeLift/data/mobile-downloads.json",session:session)
                let changelog=try await fetch("https://www.fabriziodegni.com/NodeLift/data/changelog.json",session:session)
                guard let current=CompanionRelease(version:Bundle.main.object(forInfoDictionaryKey:"CFBundleShortVersionString") as? String ?? "",build:Int(Bundle.main.object(forInfoDictionaryKey:"CFBundleVersion") as? String ?? "") ?? 0) else{throw URLError(.cannotParseResponse)}
                let verified=try ReleaseMetadata.parse(manifest:manifest,changelog:changelog,current:current)
                let release=verified.release
                details=verified;available=release>current
                message=available ? Message("Update available: {0} · build {1}",release.version,release.build) : "No newer companion release was found."
                defaults.set(Date().timeIntervalSince1970,forKey:"update-success")
                Diagnostics.shared.record(available ? .updateAvailable:.updateCurrent)
            } catch {available=false;details=nil;message="Update check unavailable. Check your connection or try again later.";Diagnostics.shared.record(.updateFailed,error:error)}
        }
    }
    private func fetch(_ endpoint:String,session:URLSession) async throws -> [String:Any] {
        var request=URLRequest(url:URL(string:endpoint)!)
        request.setValue("application/json",forHTTPHeaderField:"Accept");request.setValue("NodeLift-update-check",forHTTPHeaderField:"User-Agent")
        let (stream,response)=try await session.bytes(for:request)
        guard (response as? HTTPURLResponse)?.statusCode==200,response.mimeType?.lowercased()=="application/json" else{throw URLError(.badServerResponse)}
        var data=Data()
        for try await byte in stream {guard data.count<524288 else{throw URLError(.dataLengthExceedsMaximum)};data.append(byte)}
        guard let object=try JSONSerialization.jsonObject(with:data) as? [String:Any] else{throw URLError(.cannotParseResponse)}
        return object
    }

}
