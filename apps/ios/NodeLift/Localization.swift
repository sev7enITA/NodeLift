import Foundation

enum AppLanguage {
    static func normalize(_ value: String?) -> String {
        guard let value, ["en", "zh-Hans", "it"].contains(value) else { return "en" }
        return value
    }
}

struct Message: ExpressibleByStringLiteral {
    let key: String
    let args: [Any]
    init(_ key: String, _ args: Any...) { self.key = key; self.args = args }
    init(stringLiteral value: String) { key = value; args = [] }
    func resolve(_ language: String) -> String {
        let catalog = language == "zh-Hans" ? chineseMessages : language == "it" ? italianMessages : [:]
        let template = catalog[key] ?? key
        // Replace in a single pass. Parameter contents are never interpreted as templates.
        let regex = try! NSRegularExpression(pattern: "\\{(\\d+)\\}")
        let source = template as NSString
        var result = template
        for match in regex.matches(in: template, range: NSRange(location: 0, length: source.length)).reversed() {
            guard let index = Int(source.substring(with: match.range(at: 1))), index < args.count,
                  let range = Range(match.range, in: result) else { continue }
            let value = (args[index] as? Message)?.resolve(language) ?? String(describing: args[index])
            result.replaceSubrange(range, with: value)
        }
        return result
    }
}
