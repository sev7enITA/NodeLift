package dev.nodelift.companion

import android.content.Context
import org.json.JSONObject

/** Message IDs and parameters stay separate so an active session can change language. */
data class UiText(val key: String, val args: List<Any> = emptyList()) {
    fun render(context: Context): String = L10n.text(context, key, *args.toTypedArray())
}
fun ui(key: String, vararg args: Any) = UiText(key, args.toList())

object L10n {
    private val catalogs = mutableMapOf<String, JSONObject>()
    private fun normalize(language: String?) = if (language in listOf("en", "zh-Hans", "it")) language!! else "en"
    fun language(context: Context): String =
        normalize(context.getSharedPreferences("language", 0).getString("selected", "en"))
    fun select(context: Context, language: String) {
        context.getSharedPreferences("language", 0).edit().putString("selected", normalize(language)).apply()
    }
    fun text(context: Context, key: String, vararg args: Any): String {
        val selected = language(context)
        val template = if (selected != "en") {
            val catalog = synchronized(this) {
                catalogs.getOrPut(selected) { context.assets.open("$selected.json").bufferedReader().use { JSONObject(it.readText()) } }
            }
            catalog.optString(key, key)
        } else key
        return Regex("\\{(\\d+)\\}").replace(template) { match ->
            val value = args.getOrNull(match.groupValues[1].toInt())
            when (value) { is UiText -> value.render(context); null -> match.value; else -> value.toString() }
        }
    }
}
