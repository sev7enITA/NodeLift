import Foundation
import Security
import CryptoKit

struct Ticket: Codable, Sendable {
    let `protocol`: Int
    let url: String
    let certificate: String
    let sha256: String
    var invite: String?
    var expires_at: Double?

    static func decodeInvitation(_ value: String, now: Double = Date().timeIntervalSince1970) throws -> Ticket {
        guard value.utf8.count <= 8192 else { throw NodeError.message("Invalid invitation") }
        let text = value.trimmingCharacters(in: .whitespacesAndNewlines)
        let prefix = "nodelift://pair/v1/"
        let ticket: Ticket
        if text.hasPrefix(prefix) {
            let parts = text.dropFirst(prefix.count).components(separatedBy: "/")
            func matches(_ value: String, _ pattern: String) -> Bool { value.range(of: "^" + pattern + "$", options: .regularExpression) != nil }
            guard parts.count == 4, matches(parts[0], "[0-9.]+:[0-9]{1,5}"), matches(parts[1], "[0-9]{10}"), matches(parts[2], "[A-Za-z0-9_-]{32}"), matches(parts[3], "[A-Za-z0-9_-]{64,6000}"), let expiry = Double(parts[1]) else { throw NodeError.message("Invalid invitation") }
            var encoded = parts[3].replacingOccurrences(of: "-", with: "+").replacingOccurrences(of: "_", with: "/")
            encoded += String(repeating: "=", count: (4 - encoded.count % 4) % 4)
            guard let der = Data(base64Encoded: encoded) else { throw NodeError.message("Invalid invitation") }
            let certificate = "-----BEGIN CERTIFICATE-----\n" + der.base64EncodedString(options: [.lineLength64Characters, .endLineWithLineFeed]) + "\n-----END CERTIFICATE-----\n"
            ticket = Ticket(protocol: 1, url: "https://" + parts[0], certificate: certificate, sha256: SHA256.hash(data: der).map { String(format: "%02x", $0) }.joined(), invite: parts[2], expires_at: expiry)
        } else {
            do { ticket = try JSONDecoder().decode(Ticket.self, from: Data(text.utf8)) }
            catch { throw NodeError.message("Invalid invitation") }
        }
        guard let invite = ticket.invite, invite.range(of: "^[A-Za-z0-9_-]{32}$", options: .regularExpression) != nil else { throw NodeError.message("Invalid invitation") }
        guard let expiry = ticket.expires_at, expiry.isFinite, expiry > now else { throw NodeError.message("Invitation expired. Create a new one.") }
        try ticket.validate()
        return ticket
    }

    var certificateData: Data? {
        let lines = certificate.components(separatedBy: .newlines).filter { !$0.hasPrefix("---") }.joined()
        return Data(base64Encoded: lines)
    }
    func validate() throws {
        guard self.protocol == 1, let u = URLComponents(string: url), u.scheme == "https", u.user == nil, u.password == nil, u.query == nil, u.fragment == nil, u.path.isEmpty || u.path == "/", let host = u.host else { throw NodeError.message("Invalid HTTPS invitation") }
        guard u.port == nil || (1...65535).contains(u.port!) else { throw NodeError.message("Invalid HTTPS invitation") }
        let labels = host.split(separator: ".", omittingEmptySubsequences: false)
        let parts = labels.compactMap { Int($0) }
        guard labels.count == 4 else { throw NodeError.message("The computer must be on your local network") }
        guard parts.count == 4, parts.allSatisfy({ (0...255).contains($0) }), parts[0] == 10 || parts[0] == 127 || parts[0] == 192 && parts[1] == 168 || parts[0] == 172 && (16...31).contains(parts[1]) else { throw NodeError.message("The computer must be on your local network") }
        guard let data = certificateData, data.count <= 16384, SecCertificateCreateWithData(nil, data as CFData) != nil, SHA256.hash(data: data).map({ String(format:"%02x", $0) }).joined() == sha256.lowercased() else { throw NodeError.message("Invalid computer identity") }
    }
}
struct Credentials: Codable { var pairing: Ticket; let token: String; let node_id: String }
enum NodeError: LocalizedError {
    case message(String)
    var errorDescription: String? { if case .message(let m) = self { return m }; return nil }
}

final class PinnedDelegate: NSObject, URLSessionDelegate, URLSessionTaskDelegate, @unchecked Sendable {
    let ticket: Ticket
    init(_ ticket: Ticket) { self.ticket = ticket }
    func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge, completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        guard challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              challenge.protectionSpace.host == URL(string: ticket.url)?.host,
              let trust = challenge.protectionSpace.serverTrust,
              let data = ticket.certificateData,
              let anchor = SecCertificateCreateWithData(nil, data as CFData),
              let chain = SecTrustCopyCertificateChain(trust) as? [SecCertificate], let leaf = chain.first,
              (SecCertificateCopyData(leaf) as Data) == data else {
            completionHandler(.cancelAuthenticationChallenge, nil); return
        }
        SecTrustSetAnchorCertificates(trust, [anchor] as CFArray)
        SecTrustSetAnchorCertificatesOnly(trust, true)
        SecTrustSetPolicies(trust, SecPolicyCreateSSL(true, challenge.protectionSpace.host as CFString))
        if SecTrustEvaluateWithError(trust, nil) { completionHandler(.useCredential, URLCredential(trust: trust)) }
        else { completionHandler(.cancelAuthenticationChallenge, nil) }
    }
    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) { completionHandler(nil) }
}

final class NodeClient: @unchecked Sendable {
    let ticket: Ticket
    let token: String
    private(set) var lastConnectionId: String = ""
    private let responseLock = NSLock()
    private var responseUptime: TimeInterval?
    var contactAgeSeconds: Int? { responseLock.withLock { responseUptime.map { Int(max(0,ProcessInfo.processInfo.systemUptime-$0)) } } }
    private func recordResponse() { responseLock.withLock { responseUptime=ProcessInfo.processInfo.systemUptime } }
    private let session: URLSession
    init(ticket: Ticket, token: String = "") throws {
        try ticket.validate()
        self.ticket = ticket; self.token = token
        let configuration = URLSessionConfiguration.ephemeral
        configuration.timeoutIntervalForRequest = 10
        configuration.timeoutIntervalForResource = 15
        configuration.requestCachePolicy = .reloadIgnoringLocalCacheData
        configuration.urlCache = nil
        configuration.tlsMinimumSupportedProtocolVersion = .TLSv12
        session = URLSession(configuration: configuration, delegate: PinnedDelegate(ticket), delegateQueue: nil)
    }
    func cancel() { session.invalidateAndCancel() }
    func bytes(_ path: String, body: Data? = nil, raw: Bool = false) async throws -> Data {
        guard let url = URL(string: ticket.url.trimmingCharacters(in: CharacterSet(charactersIn: "/")) + path) else { throw NodeError.message("Invalid address") }
        var request = URLRequest(url: url)
        request.setValue("identity", forHTTPHeaderField: "Accept-Encoding")
        if !token.isEmpty { request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization") }
        if let body {
            request.httpMethod = "POST"; request.httpBody = body
            request.setValue(raw ? "application/octet-stream" : "application/json", forHTTPHeaderField: "Content-Type")
        }
        let (data, response) = try await session.data(for: request)
        guard let response = response as? HTTPURLResponse, (200...299).contains(response.statusCode) else { throw NodeError.message("Request rejected: check connection and pairing") }
        lastConnectionId = response.value(forHTTPHeaderField:"X-NodeLift-Connection-ID") ?? ""
        guard data.count <= 1048576 else { throw NodeError.message("Response too large") }
        if !token.isEmpty { recordResponse() }
        return data
    }
    func json(_ path: String, body: [String: Any]) async throws -> [String: Any] {
        let data = try await bytes(path, body: JSONSerialization.data(withJSONObject: body))
        guard let value = try JSONSerialization.jsonObject(with: data) as? [String: Any] else { throw NodeError.message("Invalid response") }
        return value
    }
}

enum Vault {
    static let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: "dev.nodelift.session", kSecAttrAccount as String: "host"]
    static func save(_ credentials: Credentials) throws {
        let data = try JSONEncoder().encode(credentials)
        var update: [String: Any] = [kSecValueData as String: data, kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly]
        let status = SecItemUpdate(query as CFDictionary, update as CFDictionary)
        if status == errSecItemNotFound { update.merge(query) { _,new in new }; guard SecItemAdd(update as CFDictionary, nil) == errSecSuccess else { throw NodeError.message("Secure storage failed") } }
        else if status != errSecSuccess { throw NodeError.message("Secure storage failed") }
    }
    static func load() -> Credentials? {
        var q = query; q[kSecReturnData as String] = true; q[kSecMatchLimit as String] = kSecMatchLimitOne
        var item: CFTypeRef?
        guard SecItemCopyMatching(q as CFDictionary, &item) == errSecSuccess, let data = item as? Data else { return nil }
        return try? JSONDecoder().decode(Credentials.self, from: data)
    }
    private static func identity() throws -> Data {
        let identityQuery: [String: Any] = [kSecClass as String:kSecClassGenericPassword,
            kSecAttrService as String:"dev.nodelift.identity", kSecAttrAccount as String:"installation"]
        var lookup = identityQuery
        lookup[kSecReturnData as String] = true; lookup[kSecMatchLimit as String] = kSecMatchLimitOne
        var item: CFTypeRef?
        let status = SecItemCopyMatching(lookup as CFDictionary, &item)
        if status == errSecSuccess, let data = item as? Data, data.count == 32 { return data }
        guard status == errSecItemNotFound else { throw NodeError.message("Secure storage failed") }
        var bytes = [UInt8](repeating:0, count:32)
        guard SecRandomCopyBytes(kSecRandomDefault, bytes.count, &bytes) == errSecSuccess else { throw NodeError.message("Secure storage failed") }
        let data = Data(bytes)
        var record = identityQuery; record[kSecValueData as String] = data
        record[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        guard SecItemAdd(record as CFDictionary, nil) == errSecSuccess else { throw NodeError.message("Secure storage failed") }
        return data
    }
    static func enrollment(scope: String, invite: String, previous: Credentials?) throws -> [String: Any] {
        guard scope.range(of:"^[0-9a-f]{64}$", options:.regularExpression) != nil else {
            throw NodeError.message("Update NodeLift on your computer before pairing.")
        }
        var result:[String:Any] = ["device_key":EnrollmentIdentity.scoped(try identity(), scope)]
        if let previous {
            result["previous"] = ["node_id":previous.node_id,
                "proof":EnrollmentIdentity.continuity(previous.token, invite)]
        }
        return result
    }
    static func clear() { SecItemDelete(query as CFDictionary) }
}

// Pure protocol primitives shared with the host test vectors.
enum EnrollmentIdentity {
    private static func hmac(_ key:Data, _ message:String) -> String {
        HMAC<SHA256>.authenticationCode(for:Data(message.utf8), using:SymmetricKey(data:key)).map { String(format:"%02x",$0) }.joined()
    }
    static func scoped(_ root:Data, _ scope:String) -> String { hmac(root, "nodelift-device-v1\n"+scope) }
    static func continuity(_ token:String, _ invite:String) -> String {
        hmac(Data(SHA256.hash(data:Data(token.utf8))), "nodelift-repair-v1\n"+invite)
    }
}
