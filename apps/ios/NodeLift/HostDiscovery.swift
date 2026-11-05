import Foundation
import Network

/// Discovery metadata is untrusted. It never supplies a replacement certificate or token.
final class HostDiscovery: @unchecked Sendable {
    private let lock=NSLock()
    private var found:[String:Ticket]=[:]
    static func candidates(for ticket:Ticket) async throws -> [Ticket] {
        guard ticket.protocol==2 else {return []}
        let discovery=HostDiscovery()
        let parameters=NWParameters.tcp
        parameters.includePeerToPeer=false
        let browser=NWBrowser(for:.bonjourWithTXTRecord(type:"_nodelift._tcp",domain:"local."),using:parameters)
        browser.browseResultsChangedHandler = {results,_ in
            for result in results {
                guard case .bonjour(let txt)=result.metadata else {continue}
                func value(_ key:String)->String? {if case .string(let value)=txt.getEntry(for:key) {return value};return nil}
                guard value("protocol")=="2",value("id")==ticket.sha256,
                      let address=value("address"),address.count<=15,
                      let text=value("port"),let port=Int(text),(1...65535).contains(port) else {continue}
                var candidate=ticket;candidate.url="https://\(address):\(port)";candidate.invite=nil;candidate.expires_at=nil
                guard (try? candidate.validate()) != nil else {continue}
                discovery.lock.withLock {if discovery.found.count<8 {discovery.found[candidate.url]=candidate}}
            }
        }
        browser.start(queue:DispatchQueue(label:"dev.nodelift.discovery"))
        defer {browser.cancel()}
        for _ in 0..<40 {
            try Task.checkCancellation()
            try await Task.sleep(nanoseconds:200_000_000)
            let results=discovery.lock.withLock {Array(discovery.found.values)}
            if !results.isEmpty {return Array(results.prefix(3))}
        }
        return []
    }
}
