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

    var certificateData: Data? {
        let lines = certificate.components(separatedBy: .newlines).filter { !$0.hasPrefix("---") }.joined()
        return Data(base64Encoded: lines)
    }
    func validate() throws {
        guard self.protocol == 1, let u = URLComponents(string: url), u.scheme == "https", u.user == nil, u.password == nil, u.query == nil, u.fragment == nil, u.path.isEmpty || u.path == "/", let host = u.host else { throw NodeError.message("Invito HTTPS non valido") }
        let parts = host.split(separator: ".").compactMap { Int($0) }
        guard parts.count == 4, parts.allSatisfy({ (0...255).contains($0) }), parts[0] == 10 || parts[0] == 127 || parts[0] == 192 && parts[1] == 168 || parts[0] == 172 && (16...31).contains(parts[1]) else { throw NodeError.message("Il computer deve essere nella rete locale") }
        guard let data = certificateData, data.count <= 16384, SecCertificateCreateWithData(nil, data as CFData) != nil, SHA256.hash(data: data).map({ String(format:"%02x", $0) }).joined() == sha256.lowercased() else { throw NodeError.message("Identità del computer non valida") }
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
        guard let url = URL(string: ticket.url.trimmingCharacters(in: CharacterSet(charactersIn: "/")) + path) else { throw NodeError.message("Indirizzo non valido") }
        var request = URLRequest(url: url)
        request.setValue("identity", forHTTPHeaderField: "Accept-Encoding")
        if !token.isEmpty { request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization") }
        if let body {
            request.httpMethod = "POST"; request.httpBody = body
            request.setValue(raw ? "application/octet-stream" : "application/json", forHTTPHeaderField: "Content-Type")
        }
        let (data, response) = try await session.data(for: request)
        guard let response = response as? HTTPURLResponse, (200...299).contains(response.statusCode) else { throw NodeError.message("Richiesta rifiutata: controlla connessione e associazione") }
        lastConnectionId = response.value(forHTTPHeaderField:"X-NodeLift-Connection-ID") ?? ""
        guard data.count <= 1048576 else { throw NodeError.message("Risposta troppo grande") }
        return data
    }
    func json(_ path: String, body: [String: Any]) async throws -> [String: Any] {
        let data = try await bytes(path, body: JSONSerialization.data(withJSONObject: body))
        guard let value = try JSONSerialization.jsonObject(with: data) as? [String: Any] else { throw NodeError.message("Risposta non valida") }
        return value
    }
}

enum Vault {
    static let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: "dev.nodelift.session", kSecAttrAccount as String: "host"]
    static func save(_ credentials: Credentials) throws {
        let data = try JSONEncoder().encode(credentials)
        var update: [String: Any] = [kSecValueData as String: data, kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly]
        let status = SecItemUpdate(query as CFDictionary, update as CFDictionary)
        if status == errSecItemNotFound { update.merge(query) { _,new in new }; guard SecItemAdd(update as CFDictionary, nil) == errSecSuccess else { throw NodeError.message("Salvataggio sicuro non riuscito") } }
        else if status != errSecSuccess { throw NodeError.message("Salvataggio sicuro non riuscito") }
    }
    static func load() -> Credentials? {
        var q = query; q[kSecReturnData as String] = true; q[kSecMatchLimit as String] = kSecMatchLimitOne
        var item: CFTypeRef?
        guard SecItemCopyMatching(q as CFDictionary, &item) == errSecSuccess, let data = item as? Data else { return nil }
        return try? JSONDecoder().decode(Credentials.self, from: data)
    }
    static func clear() { SecItemDelete(query as CFDictionary) }
}
