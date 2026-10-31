package dev.nodelift.companion

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.*
import android.view.View
import android.widget.*

class MainActivity : Activity() {
    private val bg = Color.rgb(11,21,28)
    private val mint = Color.rgb(145,243,206)
    private val ink = Color.rgb(237,245,248)
    private val muted = Color.rgb(158,177,189)
    private val handler = Handler(Looper.getMainLooper())
    private lateinit var ticket: EditText
    private lateinit var state: TextView
    private lateinit var info: TextView
    private lateinit var result: TextView
    private lateinit var connect: Button
    private lateinit var resume: Button
    private val render = object: Runnable {
        override fun run() {
            state.text = NodeService.status; info.text = NodeService.telemetry.ifEmpty { "${Build.MANUFACTURER} ${Build.MODEL}\nAndroid ${Build.VERSION.RELEASE}" }; result.text = NodeService.lastResult
            connect.isEnabled = !NodeService.running; resume.isEnabled = !NodeService.running && Vault.load(this@MainActivity) != null
            handler.postDelayed(this, 1000)
        }
    }
    private fun dp(v: Int) = (v*resources.displayMetrics.density).toInt()
    private fun text(value: String, size: Float = 16f, color: Int = ink): TextView = TextView(this).apply { text=value; textSize=size; setTextColor(color); setPadding(0,dp(6),0,dp(6)) }
    private fun card(): LinearLayout = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(dp(20),dp(18),dp(20),dp(18)); background=GradientDrawable().apply { setColor(Color.rgb(19,35,45)); cornerRadius=dp(16).toFloat() }; layoutParams=LinearLayout.LayoutParams(-1,-2).apply { bottomMargin=dp(16) } }
    private fun button(label: String, callback: ()->Unit) = Button(this).apply { text=label; isAllCaps=false; setTextColor(bg); backgroundTintList=android.content.res.ColorStateList.valueOf(mint); minHeight=dp(48); setOnClickListener { callback() } }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val scroll = ScrollView(this).apply { setBackgroundColor(bg); isFillViewport=true }
        val root = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(dp(24),dp(24),dp(24),dp(32)) }
        root.setOnApplyWindowInsetsListener { v,insets -> v.setPadding(dp(24),dp(24)+insets.systemWindowInsetTop,dp(24),dp(32)+insets.systemWindowInsetBottom); insets }
        root.addView(text("◈ NodeLift",30f).apply { setTypeface(null,Typeface.BOLD) })
        root.addView(text("IL TUO DISPOSITIVO. UN NUOVO NODO.",11f,mint))
        root.addView(text("Collega. Misura.\nScegli quando partecipare.",27f).apply { setPadding(0,dp(24),0,dp(20)) })
        val statusCard=card(); statusCard.addView(text("SESSIONE",11f,mint)); state=text(NodeService.status,19f); statusCard.addView(state); info=text("",14f,muted); statusCard.addView(info); root.addView(statusCard)
        val pairing=card(); pairing.addView(text("Associa il computer",20f)); pairing.addView(text("Nella dashboard NodeLift scegli “Aggiungi dispositivo”, poi incolla l’invito qui. È personale, temporaneo e monouso.",14f,muted))
        ticket=EditText(this).apply { hint="Incolla l’invito NodeLift"; setTextColor(ink); setHintTextColor(muted); minLines=2; maxLines=4; textSize=13f; importantForAutofill=View.IMPORTANT_FOR_AUTOFILL_NO_EXCLUDE_DESCENDANTS }
        pairing.addView(ticket)
        connect=button("Associa e attiva nodo") {
            val value=ticket.text.toString().trim()
            try { val obj=org.json.JSONObject(value); require(obj.getInt("protocol")==1); require(obj.getDouble("expires_at")>System.currentTimeMillis()/1000.0) { "Invito scaduto. Creane uno nuovo." }; Pairing.parse(obj); start(value); ticket.text.clear() }
            catch(e:Exception) { NodeService.status=e.message ?: "Invito non valido" }
        }
        pairing.addView(connect); resume=button("Riprendi sessione") { start(null) }; pairing.addView(resume); root.addView(pairing)
        val control=card(); control.addView(text("Il controllo resta tuo",20f)); control.addView(text("Quando il nodo è attivo il computer può avviare brevi test di rete e CPU. Il calcolo LLM distribuito non è ancora abilitato.",14f,muted));control.addView(button("Metti in pausa") { stopService(Intent(this,NodeService::class.java)); NodeService.status="In pausa · nessun lavoro delegato" });control.addView(button("Dimentica computer") { stopService(Intent(this,NodeService::class.java)); Vault.clear(this); NodeService.status="Computer dimenticato" });root.addView(control)
        val measurement=card();measurement.addView(text("Ultima misura",20f));result=text(NodeService.lastResult,15f,mint);measurement.addView(result);measurement.addView(text("La RAM disponibile è un indicatore del sistema, non memoria già condivisa. I test sintetici non indicano token/s.",13f,muted));root.addView(measurement)
        root.addView(text("0.1 · Qualification build\nNessun account cloud richiesto",12f,muted));scroll.addView(root);setContentView(scroll)
    }
    private fun start(value: String?) {
        if(Build.VERSION.SDK_INT>=33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED) requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS),42)
        startForegroundService(Intent(this,NodeService::class.java).apply { if(value!=null)putExtra("ticket",value) })
    }
    override fun onResume(){super.onResume();handler.post(render)}
    override fun onPause(){handler.removeCallbacks(render);super.onPause()}
}
