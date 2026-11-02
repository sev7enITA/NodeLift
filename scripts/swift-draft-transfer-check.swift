import Foundation

@main struct DraftTransferCheck {
    static func main() async throws {
        let ticket = try JSONDecoder().decode(Ticket.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
        let client = try NodeClient(ticket: ticket, token: "synthetic-draft-test")
        defer { client.cancel() }
        for text in ["{\"bytes\":true,\"sha256\":\"a\"}", "{\"bytes\":0,\"sha256\":\"a\"}", "{\"bytes\":1073741825,\"sha256\":\"a\"}"] {
            var rejected = false
            do { let o = try JSONDecoder().decode(DraftOffer.self, from: Data(text.utf8)); try o.validate() } catch { rejected = true }
            precondition(rejected)
        }
        let before = Set(try FileManager.default.contentsOfDirectory(atPath: NSTemporaryDirectory()).filter { $0.hasSuffix(".gguf.partial") })
        for mode in ["valid", "hash-mismatch", "wrong-length", "truncated", "redirect", "unauthorized", "cancelled"] {
            let offer = try await client.draftOffer()
            let work = Task { try await client.downloadDraft(offer) { _ in } }
            if mode == "cancelled" {
                try await Task.sleep(nanoseconds: 100_000_000)
                work.cancel()
            }
            var succeeded = false
            do {
                let file = try await work.value
                defer { try? FileManager.default.removeItem(at: file) }
                succeeded = true
                let received = try Data(contentsOf: file); precondition(received.count == Int(offer.bytes))
            } catch { if mode == "valid" { throw error } }
            precondition(succeeded == (mode == "valid"), "Unexpected result: " + mode)
            print("PASS: " + mode)
        }
        let wrongTicket = try JSONDecoder().decode(Ticket.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[2])))
        let wrongClient = try NodeClient(ticket: wrongTicket, token: "synthetic-draft-test")
        defer { wrongClient.cancel() }
        var pinRejected = false
        do {
            let file = try await wrongClient.downloadDraft(DraftOffer(bytes: 4, sha256: String(repeating: "0", count: 64))) { _ in }
            try? FileManager.default.removeItem(at: file)
        } catch let error as NSError { pinRejected = error.domain == NSURLErrorDomain && [-1200, -1202, -999].contains(error.code) }
        precondition(pinRejected, "Unpinned server was not rejected by TLS")
        print("PASS: download TLS pin mismatch rejected")
        let after = Set(try FileManager.default.contentsOfDirectory(atPath: NSTemporaryDirectory()).filter { $0.hasSuffix(".gguf.partial") })
        precondition(before == after, "Temporary transfer files leaked")
        print("PASS: metadata bounds and partial-file cleanup")
    }
}
