import Foundation
import CryptoKit
import os

/// Serialized native work never runs on the UI actor. The C ABI retains in-flight handles.
final class NativeDraft: @unchecked Sendable {
    private let handle: UnsafeMutableRawPointer
    private let queue = DispatchQueue(label:"dev.nodelift.native",qos:.userInitiated)
    init() throws {
        guard let value=nl_create() else { throw NodeError.message("Engine allocation failed") }
        handle=value
    }
    deinit { nl_destroy(handle) }
    func cancel() { nl_cancel(handle) }
    func call(_ request:[String:Any]) async throws -> [String:Any] {
        let data=try JSONSerialization.data(withJSONObject:request)
        let text=String(decoding:data,as:UTF8.self)
        return try await withCheckedThrowingContinuation { continuation in
            queue.async { [self] in
                do {
                    guard let pointer=text.withCString({nl_call(handle,$0)}) else { throw NodeError.message("Native response missing") }
                    defer { nl_free_string(pointer) }
                    let response=Data(String(cString:pointer).utf8)
                    guard let value=try JSONSerialization.jsonObject(with:response) as? [String:Any] else { throw NodeError.message("Invalid native response") }
                    if let error=value["error"] as? String { throw NodeError.message(error) }
                    continuation.resume(returning:value)
                } catch { continuation.resume(throwing:error) }
            }
        }
    }
    static var modelURL:URL {
        FileManager.default.urls(for:.applicationSupportDirectory,in:.userDomainMask)[0].appendingPathComponent("NodeLift/draft.gguf")
    }
    static func hash(_ url:URL) throws -> String {
        let input=try FileHandle(forReadingFrom:url);defer { try? input.close() }
        var digest=SHA256()
        while let data=try input.read(upToCount:262144), !data.isEmpty {
            try Task.checkCancellation();digest.update(data:data)
        }
        return digest.finalize().map{String(format:"%02x",$0)}.joined()
    }
    static func importFile(_ source:URL) async throws -> String {
        let task=Task.detached(priority:.utility) { () throws -> String in
            let scoped=source.startAccessingSecurityScopedResource()
            defer { if scoped {source.stopAccessingSecurityScopedResource()} }
            let size=try source.resourceValues(forKeys:[.fileSizeKey]).fileSize ?? 0
            guard size>0 && size<=1073741824 else {throw NodeError.message("Choose a GGUF no larger than 1 GiB")}
            let destination=modelURL,folder=destination.deletingLastPathComponent()
            try FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true)
            let capacity=try folder.resourceValues(forKeys:[.volumeAvailableCapacityForImportantUsageKey]).volumeAvailableCapacityForImportantUsage ?? 0
            guard capacity>Int64(size)+536870912 else {throw NodeError.message("Not enough free storage")}
            let partial=folder.appendingPathComponent(UUID().uuidString+".partial")
            defer { try? FileManager.default.removeItem(at:partial) }
            try FileManager.default.copyItem(at:source,to:partial)
            try Task.checkCancellation()
            let file=try FileHandle(forReadingFrom:partial)
            let magic=try file.read(upToCount:4);try file.close()
            guard magic==Data("GGUF".utf8) else {throw NodeError.message("This is not a GGUF file")}
            let sha=try hash(partial)
            if FileManager.default.fileExists(atPath:destination.path) {
                _ = try FileManager.default.replaceItemAt(destination,withItemAt:partial)
            } else {try FileManager.default.moveItem(at:partial,to:destination)}
            var excluded=destination;var values=URLResourceValues();values.isExcludedFromBackup=true
            try excluded.setResourceValues(values)
            UserDefaults.standard.set(sha,forKey:"draft_sha256")
            return sha
        }
        return try await withTaskCancellationHandler(operation:{try await task.value},onCancel:{task.cancel()})
    }
    static func checkedModel() async throws -> (String,UInt64) {
        let task=Task.detached(priority:.utility) { () throws -> (String,UInt64) in
            let path=modelURL
            let size=UInt64(try path.resourceValues(forKeys:[.fileSizeKey]).fileSize ?? 0)
            guard size>0 && size<=1073741824 else {throw NodeError.message("First import a draft no larger than 1 GiB")}
            guard os_proc_available_memory()>size*2+268435456 else {throw NodeError.message("Not enough available RAM")}
            let sha=try hash(path)
            guard sha==UserDefaults.standard.string(forKey:"draft_sha256") else {throw NodeError.message("Hash mismatch: import the draft again")}
            return (sha,size)
        }
        return try await withTaskCancellationHandler(operation:{try await task.value},onCancel:{task.cancel()})
    }
}
