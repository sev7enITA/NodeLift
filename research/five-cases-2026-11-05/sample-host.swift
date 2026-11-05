// Small macOS telemetry helper. OS thermal pressure is not a temperature sensor.
import Foundation

let count = CommandLine.arguments.count > 1 ? Int(CommandLine.arguments[1]) ?? 0 : 1
let interval = CommandLine.arguments.count > 2 ? Double(CommandLine.arguments[2]) ?? 0 : 2
guard (1...10000).contains(count), interval.isFinite, (0.5...30).contains(interval) else {
    FileHandle.standardError.write(Data("Usage: sample-host [samples 1..10000] [interval 0.5..30 seconds]\n".utf8))
    exit(2)
}
for index in 0..<count {
    let info = ProcessInfo.processInfo
    let thermal: String
    switch info.thermalState {
    case .nominal: thermal = "nominal"
    case .fair: thermal = "fair"
    case .serious: thermal = "serious"
    case .critical: thermal = "critical"
    @unknown default: thermal = "unknown"
    }
    var value: [String: Any] = ["unix": Date().timeIntervalSince1970,
                              "system_uptime_seconds": info.systemUptime,
                              "thermal": thermal, "active_cpu_count": info.activeProcessorCount,
                              "source": "Foundation.ProcessInfo", "sample_index": index]
    if #available(macOS 12.0, *) { value["low_power_mode"] = info.isLowPowerModeEnabled }
    let data = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
    FileHandle.standardOutput.write(data + Data([10]))
    if index + 1 < count { Thread.sleep(forTimeInterval: interval) }
}
