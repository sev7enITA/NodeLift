import Foundation

@main struct RoamingCheck {
    static func main() async throws {
        let tickets=try JSONDecoder().decode([Ticket].self,from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1])))
        let first=tickets[0],moved=tickets[1],wrong=tickets[2]
        let encoded=first.certificateData!.base64EncodedString().replacingOccurrences(of:"+",with:"-").replacingOccurrences(of:"/",with:"_").replacingOccurrences(of:"=",with:"")
        let authority=URLComponents(string:first.url)!
        let compact="nodelift://pair/v2/\(authority.host!):\(authority.port!)/\(Int(first.expires_at!))/\(first.invite!)/\(first.tls_name!)/\(encoded)"
        let decoded=try Ticket.decodeInvitation(compact)
        precondition(decoded.sha256==first.sha256 && decoded.tls_name==first.tls_name)
        let initial=try NodeClient(ticket:first)
        let health=try JSONSerialization.jsonObject(with:await initial.bytes("/health")) as! [String:Any]
        precondition(health["host_identity"] as? String == first.sha256)
        let enrolled=try await initial.json("/v1/pair",body:["invite":first.invite!,"name":"Swift roaming test on Mac","capabilities":[:]])
        let token=enrolled["token"] as! String
        let resumed=try NodeClient(ticket:moved,token:token)
        let session=try JSONSerialization.jsonObject(with:await resumed.bytes("/v1/session")) as! [String:Any]
        precondition(session["node_id"] as? String == enrolled["node_id"] as? String)
        let invalid=try NodeClient(ticket:wrong)
        var rejected=false
        do {_ = try await invalid.bytes("/health")} catch {rejected=true}
        precondition(rejected,"Changed TLS identity accepted")
        var wrongName=first;wrongName.tls_name="nodelift-"+String(repeating:"0",count:32)+".local"
        let named=try NodeClient(ticket:wrongName);rejected=false
        do {_ = try await named.bytes("/health")} catch {rejected=true}
        precondition(rejected,"Wrong logical hostname accepted")
        if CommandLine.arguments.contains("--discovery") {
            let candidates=try await HostDiscovery.candidates(for:first)
            precondition(candidates.contains(where:{$0.url==first.url}),"Bonjour discovery did not find the announced host")
            print("PASS: real NWBrowser found the advertised host on this Mac.")
        }
        let cancelled=Task {try await HostDiscovery.candidates(for:wrong)}
        cancelled.cancel()
        var cancellationObserved=false
        do {_ = try await cancelled.value} catch is CancellationError {cancellationObserved=true}
        precondition(cancellationObserved,"Discovery did not respect cancellation")
        initial.cancel();resumed.cancel();invalid.cancel();named.cancel()
        print("PASS: v2 QR, stable identity over two endpoints, same authenticated node, wrong-key and wrong-name rejection. macOS client test, not physical iOS roaming.")
    }
}
