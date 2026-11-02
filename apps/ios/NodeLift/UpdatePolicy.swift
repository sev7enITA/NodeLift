import Foundation
import CoreFoundation

struct CompanionRelease:Comparable {
    let version:String
    let build:Int
    private let parts:[Int]
    init?(version:String,build:Int) {
        guard version.range(of:"^[0-9]{1,6}\\.[0-9]{1,6}\\.[0-9]{1,6}$",options:.regularExpression) != nil,build>0,build<=Int32.max else{return nil}
        self.version=version;self.build=build;self.parts=version.split(separator:".").compactMap{Int($0)}
    }
    static func < (a:Self,b:Self)->Bool {
        for (left,right) in zip(a.parts,b.parts) {if left != right{return left<right}}
        return a.build<b.build
    }
    static func == (a:Self,b:Self)->Bool {a.parts==b.parts && a.build==b.build}
}
enum UpdatePolicy {
    static let week:TimeInterval=7*24*60*60
    static let retry:TimeInterval=60*60
    static func due(now:TimeInterval,success:TimeInterval,attempt:TimeInterval)->Bool {
        if now<success || now<attempt{return true}
        return (success<=0 || now-success>=week) && (attempt<=0 || now-attempt>=retry)
    }
}

struct ReleaseDetails:Identifiable {
    let release:CompanionRelease
    let date:String
    let title:String
    let changes:[String]
    let validation:String
    let limitations:String
    let artifact:String
    let bytes:Int64
    let sha256:String
    let url:URL
    let id=UUID()
}
enum ReleaseMetadata {
    enum Invalid:Error {case metadata}
    private static func object(_ value:Any?) throws -> [String:Any] {
        guard let value=value as? [String:Any] else {throw Invalid.metadata};return value
    }
    private static func text(_ value:Any?,_ limit:Int) throws -> String {
        guard let s=value as? String,!s.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty,s.utf16.count<=limit,
              !s.unicodeScalars.contains(where:{$0.value<32 && $0.value != 10 && $0.value != 9}) else{throw Invalid.metadata};return s
    }
    private static func integer(_ value:Any?,_ maximum:Int64) throws -> Int64 {
        guard let n=value as? NSNumber,CFGetTypeID(n) != CFBooleanGetTypeID(),
              String(cString:n.objCType) != "d",String(cString:n.objCType) != "f",
              n.int64Value>0,n.int64Value<=maximum else {throw Invalid.metadata};return n.int64Value
    }
    static func parse(manifest:[String:Any],changelog:[String:Any],current:CompanionRelease) throws -> ReleaseDetails {
        guard let release=CompanionRelease(version:try text(manifest["version"],32),build:Int(try integer(manifest["build"],Int64(Int32.max)))),release>=current,release.build>=current.build,
              try integer(changelog["schema_version"],1)==1 else {throw Invalid.metadata}
        let date=try text(manifest["published_at"],32)
        guard date.range(of:"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$",options:.regularExpression) != nil,
              ISO8601DateFormatter().date(from:date) != nil,
              let entries=changelog["releases"] as? [[String:Any]],(1...256).contains(entries.count) else{throw Invalid.metadata}
        guard entries[0]["version"] as? String==release.version,try integer(entries[0]["build"],Int64(Int32.max))==Int64(release.build) else{throw Invalid.metadata}
        let matches=try entries.filter { entry in
            guard entry["version"] as? String==release.version else{return false}
            return try integer(entry["build"],Int64(Int32.max))==Int64(release.build)
        }
        guard matches.count==1 else{throw Invalid.metadata}
        let notes=matches[0]
        guard notes["published_at"] as? String==date,
              notes["url"] as? String=="https://github.com/sev7enITA/NodeLift/releases/tag/v\(release.version)",
              let rawChanges=notes["changes"] as? [Any],(1...40).contains(rawChanges.count) else {throw Invalid.metadata}
        let name="NodeLift-\(release.version)-ios-unsigned.ipa"
        let platforms=try object(manifest["platforms"])
        let platform=try object(platforms["ios"])
        guard let artifacts=platform["artifacts"] as? [String],artifacts.contains(name),artifacts.count<=8,
              platform["status"] as? String=="compiled-unsigned",platform["architecture"] as? String=="arm64",
              let signing=platform["requires_personal_signing"] as? NSNumber,CFGetTypeID(signing)==CFBooleanGetTypeID(),signing.boolValue,
              let direct=platform["direct_browser_install"] as? NSNumber,CFGetTypeID(direct)==CFBooleanGetTypeID(),!direct.boolValue else {throw Invalid.metadata}
        let assets=try object(manifest["assets"]);let asset=try object(assets[name])
        let url="https://github.com/sev7enITA/NodeLift/releases/download/v\(release.version)/\(name)"
        let hash=try text(asset["sha256"],64)
        guard asset["url"] as? String==url,hash.range(of:"^[a-f0-9]{64}$",options:.regularExpression) != nil,let download=URL(string:url) else{throw Invalid.metadata}
        return ReleaseDetails(release:release,date:date,title:try text(notes["title"],240),changes:try rawChanges.map{try text($0,4096)},validation:try text(notes["validation"],8192),limitations:try text(notes["limitations"],8192),artifact:name,bytes:try integer(asset["bytes"],2*1024*1024*1024),sha256:hash,url:download)
    }
}
