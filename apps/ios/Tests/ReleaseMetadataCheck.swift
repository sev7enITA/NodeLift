import Foundation

@main struct ReleaseMetadataCheck {
    static func main() throws {
        let current=CompanionRelease(version:"0.2.10",build:12)!
        let name="NodeLift-0.2.10-ios-unsigned.ipa"
        let url="https://github.com/sev7enITA/NodeLift/releases/download/v0.2.10/\(name)"
        func asset()->[String:Any] {["bytes":5378286,"sha256":String(repeating:"a",count:64),"url":url]}
        func manifest(_ a:[String:Any]?=nil)->[String:Any] {["version":"0.2.10","build":12,"published_at":"2026-11-01T23:18:55Z","assets":[name:a ?? asset()],"platforms":["ios":["artifacts":[name],"status":"compiled-unsigned","architecture":"arm64","requires_personal_signing":true,"direct_browser_install":false]]]}
        func notes()->[String:Any] {["version":"0.2.10","build":12,"published_at":"2026-11-01T23:18:55Z","title":"Release","url":"https://github.com/sev7enITA/NodeLift/releases/tag/v0.2.10","changes":["Actual change"],"validation":"Build only","limitations":"No physical qualification"]}
        func log(_ n:[String:Any]?=nil)->[String:Any] {["schema_version":1,"releases":[n ?? notes()]]}
        func rejected(_ m:[String:Any],_ c:[String:Any]) {
            do {_ = try ReleaseMetadata.parse(manifest:m,changelog:c,current:current);preconditionFailure("Invalid metadata accepted")}
            catch {}
        }
        let equal=try ReleaseMetadata.parse(manifest:manifest(),changelog:log(),current:current)
        precondition(equal.release==current && equal.artifact==name && equal.bytes==5378286)
        let newer=try ReleaseMetadata.parse(manifest:manifest(),changelog:log(),current:CompanionRelease(version:"0.2.9",build:11)!)
        precondition(newer.release>CompanionRelease(version:"0.2.9",build:11)!)
        for (key,value) in [("url","https://github.com.evil.test" as Any),("url",url+"?token=x"),("url",url.replacingOccurrences(of:"ios-unsigned.ipa",with:"android-debug.apk")),("bytes",true),("bytes","123"),("bytes",1.5),("bytes",0),("bytes",Int64(2147483649)),("sha256",String(repeating:"g",count:64))] {
            var a=asset();a[key]=value;rejected(manifest(a),log())
        }
        for (key,value) in [("build",13 as Any),("build",true),("build","12"),("published_at","2026-11-02T00:00:00Z"),("changes",[String]()),("changes",Array(repeating:"change",count:41)),("title","\u{0}unsafe"),("limitations",String(repeating:"x",count:8193))] {
            var n=notes();n[key]=value;rejected(manifest(),log(n))
        }
        for value:Any in [true,"12",12.5,0,Int64(Int32.max)+1] {
            var m=manifest();m["build"]=value;rejected(m,log())
        }
        rejected(manifest(),["schema_version":1,"releases":[notes(),notes()]])
        var future=notes();future["version"]="0.2.11";future["build"]=13
        rejected(manifest(),["schema_version":1,"releases":[future,notes()]])
        var m=manifest();m["platforms"]=["ios":["artifacts":[name],"status":"compiled-unsigned","architecture":"arm64","requires_personal_signing":1,"direct_browser_install":0]]
        rejected(m,log())
        // Exercise actual Foundation JSON number/boolean bridging, not only Swift literals.
        let realManifest=try JSONSerialization.jsonObject(with:JSONSerialization.data(withJSONObject:manifest())) as! [String:Any]
        let realLog=try JSONSerialization.jsonObject(with:JSONSerialization.data(withJSONObject:log())) as! [String:Any]
        _ = try ReleaseMetadata.parse(manifest:realManifest,changelog:realLog,current:current)
        if CommandLine.arguments.count==3 {
            let m=try JSONSerialization.jsonObject(with:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1]))) as! [String:Any]
            let c=try JSONSerialization.jsonObject(with:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[2]))) as! [String:Any]
            let installed=CompanionRelease(version:m["version"] as! String,build:(m["build"] as! NSNumber).intValue)!
            let verified=try ReleaseMetadata.parse(manifest:m,changelog:c,current:installed)
            precondition(verified.release==installed)
            print("Current release fixture review passed: \(verified.release.version) build \(verified.release.build)")
        }
        print("iOS release metadata: current/newer, strict artifact URL/types/bounds/hash, exact notes identity/date, duplicate/stale rejection, unsigned policy passed.")
    }
}
