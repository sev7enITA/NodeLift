package dev.nodelift.companion

import android.app.Activity
import android.app.Dialog
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.ColorDrawable
import android.net.Uri
import android.os.Build
import android.util.TypedValue
import android.view.Gravity
import android.view.Window
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

@Suppress("DEPRECATION")
fun installedCompanionVersion(activity: Activity): String {
    return try {
        val info = activity.packageManager.getPackageInfo(activity.packageName, 0)
        val code = if (Build.VERSION.SDK_INT >= 28) info.longVersionCode else info.versionCode.toLong()
        L10n.text(activity, "Version {0} · build {1}", info.versionName ?: "—", code)
    } catch (_: PackageManager.NameNotFoundException) {
        L10n.text(activity, "Version unavailable")
    }
}

/** Project information stays local; each fixed public URL opens only after a tap. */
fun showAbout(activity: Activity): Dialog {
    val bg = Color.rgb(11, 21, 28)
    val mint = Color.rgb(145, 243, 206)
    val ink = Color.rgb(237, 245, 248)
    val muted = Color.rgb(158, 177, 189)
    fun dp(value: Int) = (value * activity.resources.displayMetrics.density).toInt()
    fun t(key: String) = L10n.text(activity, key)
    fun text(key: String, size: Float = 14f, color: Int = muted) = TextView(activity).apply {
        text = t(key); textSize = size; setTextColor(color)
        setPadding(0, dp(7), 0, dp(7))
    }
    fun open(url: String) {
        try {
            activity.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).apply {
                addCategory(Intent.CATEGORY_BROWSABLE)
            })
        } catch (_: ActivityNotFoundException) {
            Toast.makeText(activity, t("Unable to open this link. Open the official website in your browser."), Toast.LENGTH_LONG).show()
        } catch (_: SecurityException) {
            Toast.makeText(activity, t("Unable to open this link. Open the official website in your browser."), Toast.LENGTH_LONG).show()
        }
    }
    val dialog = Dialog(activity)
    dialog.requestWindowFeature(Window.FEATURE_NO_TITLE)
    val root = LinearLayout(activity).apply {
        orientation = LinearLayout.VERTICAL; setPadding(dp(22), dp(20), dp(22), dp(16))
        setBackgroundColor(bg)
    }
    root.addView(text("About & References", 23f, ink).apply { setTypeface(null, Typeface.BOLD) })
    val scroll = ScrollView(activity)
    val content = LinearLayout(activity).apply { orientation = LinearLayout.VERTICAL }
    fun link(label: String, url: String) {
        content.addView(Button(activity).apply {
            text = "${t(label)} ↗"; isAllCaps = false; textSize = 15f
            setTextColor(mint)
            val selectable = TypedValue()
            if (activity.theme.resolveAttribute(android.R.attr.selectableItemBackground, selectable, true)) {
                setBackgroundResource(selectable.resourceId)
            }
            gravity = Gravity.START or Gravity.CENTER_VERTICAL
            minHeight = dp(48); setPadding(0, dp(8), 0, dp(8))
            setOnClickListener { open(url) }
        }, LinearLayout.LayoutParams(-1, -2))
    }
    content.addView(text("NodeLift", 29f, ink).apply { setTypeface(null, Typeface.BOLD) })
    content.addView(text(installedCompanionVersion(activity), 13f, mint))
    content.addView(text("Experimental companion", 12f, mint))
    content.addView(text("Created by Fabrizio Degni", 19f, ink))
    content.addView(text("Original concept, research direction and development."))
    content.addView(text("Updates", 18f, ink))
    content.addView(text("Open the official releases page and compare your installed version with the release notes. This is a manual check; no update is installed automatically."))
    link("Check releases on GitHub", "https://github.com/sev7enITA/NodeLift/releases")
    link("Official downloads & installation", "https://www.fabriziodegni.com/NodeLift/#downloads")
    content.addView(text("Project & author", 18f, ink))
    link("Source repository", "https://github.com/sev7enITA/NodeLift")
    link("Project website", "https://www.fabriziodegni.com/NodeLift/")
    link("Author website", "https://www.fabriziodegni.com/")
    link("LinkedIn", "https://www.linkedin.com/in/fdegni/")
    content.addView(text("References & licenses", 18f, ink))
    link("Architecture & technical documentation", "https://github.com/sev7enITA/NodeLift/blob/main/docs/ARCHITECTURE.md")
    link("Research & comparison atlas", "https://github.com/sev7enITA/NodeLift/blob/main/research/comparison-2026-10-31/README.md")
    link("Third-party acknowledgements", "https://github.com/sev7enITA/NodeLift/blob/main/THIRD_PARTY_NOTICES.md")
    link("MIT license · original NodeLift code", "https://github.com/sev7enITA/NodeLift/blob/main/LICENSE")
    content.addView(text("Dependencies and model weights retain their own licenses and authorship."))
    content.addView(text("Capacity sharding is not implemented. Physical-phone inference speedup remains unproven."))
    content.addView(text("Links open in your browser. NodeLift does not attach pairing keys, model data or diagnostics."))
    content.addView(text("© 2026 Fabrizio Degni", 12f, muted))
    scroll.addView(content)
    root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
    root.addView(Button(activity).apply {
        text = t("Close"); isAllCaps = false; minHeight = dp(48)
        setTextColor(bg); backgroundTintList = android.content.res.ColorStateList.valueOf(mint)
        setOnClickListener { dialog.dismiss() }
    }, LinearLayout.LayoutParams(-1, -2))
    dialog.setContentView(root)
    dialog.show()
    dialog.window?.apply {
        setBackgroundDrawable(ColorDrawable(bg))
        setLayout(ViewGroup.LayoutParams.MATCH_PARENT, (activity.resources.displayMetrics.heightPixels * 0.88).toInt())
    }
    return dialog
}
