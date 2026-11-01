import Foundation
@main struct Checks {
 static func main() {
  precondition(Message("Add device").resolve("en") == "Add device")
  precondition(Message("Add device").resolve("zh-Hans") == "添加设备")
  precondition(Message("CPU · {0} iterations in {1} ms",9,123).resolve("zh-Hans") == "CPU · 123 毫秒内完成 9 次迭代")
  precondition(Message("Measurement interrupted: {0}","{1}你好$&").resolve("zh-Hans") == "测量已中断：{1}你好$&")
  precondition(Message("{0} · thermal: {1}",Message("Wi-Fi / hotspot"),Message("nominal")).resolve("zh-Hans") == "Wi-Fi / 热点 · 温度状态：正常")
  precondition(Message("Native error: E123").resolve("zh-Hans") == "Native error: E123")
  precondition(AppLanguage.normalize(nil) == "en")
  precondition(AppLanguage.normalize("unsupported") == "en")
  precondition(AppLanguage.normalize("it") == "it")
  precondition(AppLanguage.normalize("zh-Hans") == "zh-Hans")
  precondition(Message("Add device").resolve("it") == "Aggiungi dispositivo")
  precondition(Message("CPU · {0} iterations in {1} ms",9,123).resolve("it") == "CPU · 9 iterazioni in 123 ms")
  precondition(Message("Measurement interrupted: {0}","{1}你好$&").resolve("it") == "Misura interrotta: {1}你好$&")
  precondition(Message("{0} · thermal: {1}",Message("Wi-Fi / hotspot"),Message("nominal")).resolve("it") == "Wi-Fi / hotspot · stato termico: normale")
  precondition(Message("Native error: E123").resolve("it") == "Native error: E123")
  print("Swift EN / zh-Hans / IT: preference validation, fallback, nested messages, Unicode and literal isolation passed.")
 }
}
