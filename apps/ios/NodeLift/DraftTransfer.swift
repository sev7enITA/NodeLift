import Foundation
import CryptoKit

struct DraftOffer: Decodable {
    let bytes: Int64
    let sha256: String
    func validate() throws {
        guard (1...1_073_741_824).contains(bytes),
              sha256.range(of: "^[a-f0-9]{64}$", options: .regularExpression) != nil else {
            throw NodeError.message("Invalid draft metadata")
        }
    }
}

extension NodeClient {
    func draftOffer() async throws -> DraftOffer {
        let offer = try JSONDecoder().decode(DraftOffer.self, from: await bytes("/v1/engine/model-info"))
        try offer.validate()
        return offer
    }

    /// Streams into an owned temporary file with a strict byte ceiling. Never follows a URL from metadata.
    func downloadDraft(_ offer: DraftOffer, progress: @Sendable (Double) async -> Void) async throws -> URL {
        try offer.validate()
        let folder = FileManager.default.temporaryDirectory
        let capacity = try folder.resourceValues(forKeys: [.volumeAvailableCapacityForImportantUsageKey]).volumeAvailableCapacityForImportantUsage ?? 0
        guard capacity > offer.bytes * 2 + 536_870_912 else { throw NodeError.message("Not enough free storage") }
        let file = folder.appendingPathComponent(UUID().uuidString + ".gguf.partial")
        guard FileManager.default.createFile(atPath: file.path, contents: nil) else { throw NodeError.message("Not enough free storage") }
        var completed = false
        defer { if !completed { try? FileManager.default.removeItem(at: file) } }
        let output = try FileHandle(forWritingTo: file)
        defer { try? output.close() }
        let config = URLSessionConfiguration.ephemeral
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 900
        config.urlCache = nil
        config.requestCachePolicy = .reloadIgnoringLocalCacheData
        config.tlsMinimumSupportedProtocolVersion = .TLSv12
        let pin = PinnedDelegate(ticket)
        let transfer = URLSession(configuration: config, delegate: pin, delegateQueue: nil)
        defer { transfer.invalidateAndCancel() }
        var request = URLRequest(url: URL(string: ticket.url.trimmingCharacters(in: CharacterSet(charactersIn: "/")) + "/v1/engine/model")!)
        request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization")
        request.setValue("identity", forHTTPHeaderField: "Accept-Encoding")
        let (stream, response) = try await transfer.bytes(for: request, delegate: pin)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200,
              http.expectedContentLength == offer.bytes else { throw NodeError.message("Model download unavailable") }
        var buffer = Data(); buffer.reserveCapacity(262_144)
        var count: Int64 = 0
        var digest = SHA256()
        var reported: Int64 = 0
        for try await byte in stream {
            count += 1
            guard count <= offer.bytes else { throw NodeError.message("Model integrity check failed") }
            buffer.append(byte)
            if buffer.count == 262_144 {
                try Task.checkCancellation()
                digest.update(data: buffer); try output.write(contentsOf: buffer); buffer.removeAll(keepingCapacity: true)
                if count - reported >= 4_194_304 {
                    reported = count; await progress(Double(count) / Double(offer.bytes))
                }
            }
        }
        try Task.checkCancellation()
        digest.update(data: buffer); try output.write(contentsOf: buffer)
        let sha = digest.finalize().map { String(format: "%02x", $0) }.joined()
        guard count == offer.bytes, sha == offer.sha256 else { throw NodeError.message("Model integrity check failed") }
        try output.synchronize()
        completed = true
        await progress(1)
        return file
    }
}
