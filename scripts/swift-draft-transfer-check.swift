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
        let expired = "unknown, expired or replayed inference lease"
        let cases: [(String, Int, String, Bool)] = [
            (expired, 400, "/v1/engine/result", true),
            (expired, 400, "/v1/engine/result", true),
            (expired, 400, "/v1/engine/result", true),
            ("stale or mismatched draft identity", 400, "/v1/engine/result", true),
            ("invalid draft token IDs", 400, "/v1/engine/result", false),
            (expired, 401, "/v1/engine/result", false),
            (expired, 400, "/v1/heartbeat", false)
        ]
        for (reason, status, path, expectedDiscard) in cases {
            var discarded = false
            do { _ = try await client.json(path, body: ["error": reason, "status": status]); preconditionFailure("Rejected result accepted") }
            catch NodeError.discardedDraft { discarded = true }
            catch { }
            precondition(discarded == expectedDiscard)
        }
        _ = try await client.json("/v1/engine/result", body: ["error": "synthetic", "status": 200])
        print("PASS: obsolete results discarded without retry; other errors remain errors; session reusable")
        let after = Set(try FileManager.default.contentsOfDirectory(atPath: NSTemporaryDirectory()).filter { $0.hasSuffix(".gguf.partial") })
        precondition(before == after, "Temporary transfer files leaked")
        print("PASS: metadata bounds and partial-file cleanup")
    }
}
