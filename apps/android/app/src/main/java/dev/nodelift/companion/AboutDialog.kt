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
        L10n.text(activity, "Version {0} · build {1}", info.versionName ?: "-", code)
    } catch (_: PackageManager.NameNotFoundException) {
        L10n.text(activity, "Version unavailable")
    }
}

/** Public update metadata is checked by UpdateMonitor; diagnostics leave the device only after export. */
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
    content.addView(LinearLayout(activity).apply {
        orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL
        addView(android.widget.ImageView(activity).apply {
            setImageResource(R.drawable.ic_node_mark); importantForAccessibility = android.view.View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }, LinearLayout.LayoutParams(dp(42), dp(42)).apply { marginEnd = dp(12) })
        addView(text("NodeLift", 29f, ink).apply { setTypeface(null, Typeface.BOLD) })
    })
    content.addView(text(installedCompanionVersion(activity), 13f, mint))
    content.addView(text("Experimental companion", 12f, mint))
    content.addView(text("Created by Fabrizio Degni", 19f, ink))
    content.addView(text("Original concept, research direction and development."))
    content.addView(text("Updates", 18f, ink))
    content.addView(text("NodeLift checks the official version metadata at launch and weekly while running. If the system suspends the app, an overdue check runs when you return. Installation is always your choice."))
    val updateState = text("", 14f, mint).apply { accessibilityLiveRegion = android.view.View.ACCESSIBILITY_LIVE_REGION_POLITE }
    content.addView(updateState)
    val checkUpdates = Button(activity).apply {
        text = t("Check now"); ControlUI.style(this, ControlUI.Tone.SECONDARY)
        setOnClickListener {
            isEnabled = false; text = t("Checking for updates…")
            UpdateMonitor.check(activity, manual = true)
        }
    }
    content.addView(checkUpdates, LinearLayout.LayoutParams(-1, -2))
    val viewRelease = Button(activity).apply {
        text = t("View release notes & download"); ControlUI.style(this, ControlUI.Tone.PRIMARY)
        setOnClickListener { UpdateMonitor.details?.let { showReleaseDetails(activity, it) } }
    }
    content.addView(viewRelease, LinearLayout.LayoutParams(-1, -2))
    link("Check releases on GitHub", "https://github.com/sev7enITA/NodeLift/releases")
    link("Official downloads & installation", "https://www.fabriziodegni.com/NodeLift/#downloads")
    content.addView(text("Diagnostics", 18f, ink))
    content.addView(text("A bounded seven-day log stays on this device. It records app and OS versions, technical events and limited error details. Pairing credentials, QR codes and prompt contents are excluded. Nothing is uploaded automatically."))
    content.addView(text("After an error or interruption, export a report and choose where to save or share it. Some native crashes and system shutdowns may leave no complete report."))
    val diagnosticState = text("", 14f, mint).apply {
        accessibilityLiveRegion = android.view.View.ACCESSIBILITY_LIVE_REGION_POLITE
        visibility = android.view.View.GONE
    }
    if (Diagnostics.hasPreviousIncident) {
        diagnosticState.text = t("A previous interruption was recorded. Export diagnostics from About & References.")
        diagnosticState.setTextColor(ControlUI.amber)
        diagnosticState.visibility = android.view.View.VISIBLE
    }
    content.addView(diagnosticState)
    content.addView(Button(activity).apply {
        text = t("Export diagnostics"); ControlUI.style(this, ControlUI.Tone.SECONDARY)
        setOnClickListener {
            isEnabled = false
            val exported = Diagnostics.export(activity)
            diagnosticState.text = t(if (exported) "Diagnostic report prepared. Choose where to save or share it." else "Unable to export diagnostics. Try again.")
            diagnosticState.setTextColor(if (exported) mint else ControlUI.amber)
            diagnosticState.visibility = android.view.View.VISIBLE
            isEnabled = true
        }
    }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(6) })
    content.addView(Button(activity).apply {
        text = t("Clear diagnostics"); ControlUI.style(this, ControlUI.Tone.DANGER)
        setOnClickListener {
            android.app.AlertDialog.Builder(activity)
                .setTitle(t("Clear diagnostics"))
                .setMessage(t("Delete the local diagnostic history? Previously exported copies are not affected."))
                .setNegativeButton(t("Cancel"), null)
                .setPositiveButton(t("Clear diagnostics")) { _, _ ->
                    val cleared = Diagnostics.clear()
                    diagnosticState.text = t(if (cleared) "Local diagnostic history cleared." else "Unable to clear diagnostics. Try again.")
                    diagnosticState.setTextColor(if (cleared) mint else ControlUI.amber)
                    diagnosticState.visibility = android.view.View.VISIBLE
                }.show()
        }
    }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(6) })
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
    val handler = android.os.Handler(android.os.Looper.getMainLooper())
    val refreshUpdates = object : Runnable {
        override fun run() {
            val currentMessage = UpdateMonitor.message.render(activity)
            if (updateState.text.toString() != currentMessage) updateState.text = currentMessage
            viewRelease.isEnabled = !UpdateMonitor.checking && UpdateMonitor.details != null
            checkUpdates.isEnabled = !UpdateMonitor.checking
            checkUpdates.text = t(if (UpdateMonitor.checking) "Checking for updates…" else "Check now")
            ControlUI.describe(checkUpdates, checkUpdates.text.toString())
            if (dialog.isShowing) handler.postDelayed(this, 1000)
        }
    }
    dialog.setOnDismissListener { handler.removeCallbacks(refreshUpdates) }
    dialog.show()
    handler.post(refreshUpdates)
    dialog.window?.apply {
        setBackgroundDrawable(ColorDrawable(bg))
        setLayout(ViewGroup.LayoutParams.MATCH_PARENT, (activity.resources.displayMetrics.heightPixels * 0.88).toInt())
    }
    return dialog
}

/** Review is local and cancellable. Only the explicit final button opens the exact public asset. */
fun showReleaseDetails(activity:Activity, details:ReleaseDetails):Dialog {
    fun t(key:String)=L10n.text(activity,key)
    fun dp(n:Int)=(n*activity.resources.displayMetrics.density).toInt()
    val dialog=Dialog(activity);dialog.requestWindowFeature(Window.FEATURE_NO_TITLE)
    val root=LinearLayout(activity).apply { orientation=LinearLayout.VERTICAL;setPadding(dp(22),dp(18),dp(22),dp(12));setBackgroundColor(ControlUI.canvas) }
    val content=LinearLayout(activity).apply { orientation=LinearLayout.VERTICAL }
    fun text(value:String,heading:Boolean=false) {
        content.addView(TextView(activity).apply {
            text=value;textSize=if(heading)20f else 16f;setTextColor(ControlUI.ink);setPadding(0,dp(8),0,dp(8))
            if(heading){setTypeface(null,Typeface.BOLD);if(Build.VERSION.SDK_INT>=28)isAccessibilityHeading=true}
            else setTextIsSelectable(true)
        },LinearLayout.LayoutParams(-1,-2))
    }
    text(t("Release notes"),true)
    text(L10n.text(activity,"Version {0} · build {1}",details.release.version,details.release.build))
    text(t("Published (UTC)")+": "+details.date)
    text(details.title,true)
    text(t("Release notes are published in English."))
    details.changes.forEach { text("• $it") }
    text(t("Validation"),true);text(details.validation)
    text(t("Limitations"),true);text(details.limitations)
    text(t("Download details"),true);text(details.artifact)
    text(L10n.text(activity,"Artifact size: {0} bytes",details.bytes))
    text("SHA-256\n"+details.sha256)
    text(t("This hash is published metadata. NodeLift does not verify the downloaded file when your browser downloads it."))
    text(t("The APK download opens in your browser. Android asks you before installation; NodeLift does not install it automatically."))
    val action=Button(activity).apply {
        text=t("Download APK in browser");ControlUI.style(this,ControlUI.Tone.PRIMARY)
        setOnClickListener {
            if(UpdateMonitor.checking || UpdateMonitor.details !== details)return@setOnClickListener
            try {activity.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(details.url)).addCategory(Intent.CATEGORY_BROWSABLE))}
            catch(_:ActivityNotFoundException){Toast.makeText(activity,t("Unable to open this link. Open the official website in your browser."),Toast.LENGTH_LONG).show()}
            catch(_:SecurityException){Toast.makeText(activity,t("Unable to open this link. Open the official website in your browser."),Toast.LENGTH_LONG).show()}
        }
    }
    content.addView(action,LinearLayout.LayoutParams(-1,-2))
    val expired=TextView(activity).apply {text=t("Release details need a new check. Close this view and choose Check now.");setTextColor(ControlUI.amber);textSize=16f;accessibilityLiveRegion=android.view.View.ACCESSIBILITY_LIVE_REGION_POLITE}
    content.addView(expired)
    root.addView(ScrollView(activity).apply{addView(content)},LinearLayout.LayoutParams(-1,0,1f))
    root.addView(Button(activity).apply{text=t("Close");ControlUI.style(this,ControlUI.Tone.SECONDARY);setOnClickListener{dialog.dismiss()}},LinearLayout.LayoutParams(-1,-2))
    dialog.setContentView(root)
    val handler=android.os.Handler(android.os.Looper.getMainLooper())
    val refresh=object:Runnable {override fun run(){
        val valid=!UpdateMonitor.checking && UpdateMonitor.details === details
        action.isEnabled=valid;expired.visibility=if(valid)android.view.View.GONE else android.view.View.VISIBLE
        if(dialog.isShowing)handler.postDelayed(this,500)
    }}
    dialog.setOnDismissListener{handler.removeCallbacks(refresh)};dialog.show();handler.post(refresh)
    dialog.window?.apply{setBackgroundDrawable(ColorDrawable(ControlUI.canvas));setLayout(-1,(activity.resources.displayMetrics.heightPixels*0.90).toInt())}
    return dialog
}
