package dev.nodelift.companion

import android.app.Activity
import android.app.Instrumentation
import android.os.Bundle
import java.util.Locale

/** Offline formatter/preference checks on a disposable emulator; no inference or network. */
class LocalizationCheck : Instrumentation() {
    override fun onCreate(arguments: Bundle?) { super.onCreate(arguments); start() }
    override fun onStart() {
        val result=Bundle()
        val prefs=targetContext.getSharedPreferences("language",0)
        val previous=prefs.getString("selected",null)
        val locale=Locale.getDefault()
        var success=false
        try {
            Locale.setDefault(Locale.CHINA)
            prefs.edit().remove("selected").commit()
            check(L10n.language(targetContext)=="en")
            val message=ui("CPU · {0} iterations in {1} ms",9,123)
            check(message.render(targetContext)=="CPU · 9 iterations in 123 ms")
            L10n.select(targetContext,"zh-Hans")
            check(L10n.language(targetContext)=="zh-Hans")
            check(message.render(targetContext)=="CPU · 123 毫秒内完成 9 次迭代")
            check(ui("Measurement interrupted: {0}","<script>{1}$&你好</script>").render(targetContext)=="测量已中断：<script>{1}$&你好</script>")
            check(ui("{0} · thermal: {1}",ui("Wi-Fi / hotspot"),ui("nominal")).render(targetContext)=="Wi-Fi / 热点 · 温度状态：正常")
            check(ui("External diagnostic E123").render(targetContext)=="External diagnostic E123")
            L10n.select(targetContext,"it")
            check(L10n.language(targetContext)=="it")
            check(prefs.getString("selected",null)=="it")
            check(message.render(targetContext)=="CPU · 9 iterazioni in 123 ms")
            check(ui("Add device").render(targetContext)=="Aggiungi dispositivo")
            check(ui("Measurement interrupted: {0}","<script>{1}$&你好</script>").render(targetContext)=="Misura interrotta: <script>{1}$&你好</script>")
            check(ui("{0} · thermal: {1}",ui("Wi-Fi / hotspot"),ui("nominal")).render(targetContext)=="Wi-Fi / hotspot · stato termico: normale")
            check(ui("External diagnostic E123").render(targetContext)=="External diagnostic E123")
            L10n.select(targetContext,"en")
            check(message.render(targetContext)=="CPU · 9 iterations in 123 ms")
            prefs.edit().putString("selected","invalid").commit()
            check(L10n.language(targetContext)=="en")
            success=true
            result.putString("stream","PASS: EN / zh-Hans / IT, English default with Chinese process locale, persisted selection, live message translation, nested telemetry, argument isolation, fallback. Emulator only.\n")
        } catch(error:Exception) {
            result.putString("stream","FAIL: ${error.javaClass.simpleName}: ${error.message}\n")
        } finally {
            Locale.setDefault(locale)
            if(previous==null)prefs.edit().remove("selected").commit() else prefs.edit().putString("selected",previous).commit()
        }
        finish(if(success)Activity.RESULT_OK else Activity.RESULT_CANCELED,result)
    }
}
