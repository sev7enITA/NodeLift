package dev.nodelift.companion

import android.content.Context
import org.json.JSONObject

/** Message IDs and parameters stay separate so an active session can change language. */
data class UiText(val key: String, val args: List<Any> = emptyList()) {
    fun render(context: Context): String = L10n.text(context, key, *args.toTypedArray())
}
fun ui(key: String, vararg args: Any) = UiText(key, args.toList())

object L10n {
    private var chinese: JSONObject? = null
    fun language(context: Context): String =
        if (context.getSharedPreferences("language", 0).getString("selected", "en") == "zh-Hans") "zh-Hans" else "en"
    fun select(context: Context, language: String) {
        context.getSharedPreferences("language", 0).edit().putString("selected", if (language == "zh-Hans") language else "en").apply()
    }
    fun text(context: Context, key: String, vararg args: Any): String {
        val template = if (language(context) == "zh-Hans") {
            val catalog = chinese ?: synchronized(this) {
                chinese ?: context.assets.open("zh-Hans.json").bufferedReader().use { JSONObject(it.readText()) }.also { chinese = it }
            }
            catalog.optString(key, key)
        } else key
        return Regex("\\{(\\d+)\\}").replace(template) { match ->
            val value = args.getOrNull(match.groupValues[1].toInt())
            when (value) { is UiText -> value.render(context); null -> match.value; else -> value.toString() }
        }
    }
}
