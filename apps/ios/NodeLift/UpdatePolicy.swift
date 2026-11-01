import Foundation

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
