import Foundation

@main struct ProtocolCheck {
    static func main() async throws {
        let ticket = try JSONDecoder().decode(Ticket.self,from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1])))
        try ticket.validate()
        let c = try NodeClient(ticket:ticket)
        let result = try await c.json("/v1/pair",body:["invite":ticket.invite!,"name":"Swift protocol QA (macOS, not iPhone)","capabilities":["os":"macOS protocol test","supported_jobs":["network"]]])
        c.cancel()
        guard let token=result["token"] as? String else { fatalError("missing token") }
        let authenticated = try NodeClient(ticket:ticket,token:token)
        let data=try await authenticated.bytes("/v1/probe?size=16384")
        guard data.count==16384 else { fatalError("truncated payload") }
        let upload=try await authenticated.bytes("/v1/upload",body:data,raw:true)
        guard (try JSONSerialization.jsonObject(with:upload) as? [String:Any])?["bytes"] as? Int == 16384 else { fatalError("incorrect upload receipt") }
        _ = try await authenticated.json("/v1/heartbeat",body:["model":"Swift protocol QA","supported_jobs":["network"]])
        authenticated.cancel()
        let invalid=Ticket(protocol:ticket.protocol,url:ticket.url,certificate:ticket.certificate,sha256:String(repeating:"0",count:64),invite:nil,expires_at:nil)
        var rejected=false
        do { try invalid.validate() } catch { rejected=true }
        guard rejected else { fatalError("invalid certificate fingerprint accepted") }
        let wrong=try JSONDecoder().decode(Ticket.self,from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[2])))
        let untrusted=try NodeClient(ticket:wrong)
        var transportRejected=false
        do { _ = try await untrusted.bytes("/health") }
        catch { transportRejected = error is URLError }
        untrusted.cancel()
        guard transportRejected else { fatalError("wrong host certificate not rejected at TLS transport") }
        print("PASS: native Swift client TLS enrollment, authenticated download/upload, heartbeat, invalid fingerprint and wrong-host certificate rejection. Executed on macOS, not iOS hardware.")
    }
}
