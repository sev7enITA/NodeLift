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
    private lateinit var engineInfo: TextView
    private val render = object: Runnable {
        override fun run() {
            state.text = NodeService.status; info.text = NodeService.telemetry.ifEmpty { "${Build.MANUFACTURER} ${Build.MODEL}\nAndroid ${Build.VERSION.RELEASE}" }; result.text = NodeService.lastResult
            connect.isEnabled = !NodeService.running; resume.isEnabled = !NodeService.running && Vault.load(this@MainActivity) != null
            engineInfo.text=NodeService.engineStatus
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
        root.addView(text("Più vita al tuo hardware.\nUn nodo, nuove possibilità.",27f).apply { setPadding(0,dp(24),0,dp(20)) })
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
        val prefs=getSharedPreferences("engine",0)
        val engine=card();engine.addView(text("MOTORE SPERIMENTALE",11f,mint));engine.addView(text("Il telefono propone.\nIl Mac verifica.",23f));engineInfo=text(NodeService.engineStatus,14f,mint);engine.addView(engineInfo)
        engine.addView(text("Un piccolo modello GGUF sul telefono propone blocchi di token. Il modello principale resta sul computer e verifica ogni proposta. Backend CPU ARM64; GPU/NPU non abilitate in questa build.",14f,muted))
        engine.addView(Switch(this).apply { text="Consenti proposte LLM";setTextColor(ink);isChecked=prefs.getBoolean("enabled",false);setOnCheckedChangeListener { _,value -> prefs.edit().putBoolean("enabled",value).apply() } })
        fun slider(label:String,key:String,min:Int,max:Int,initial:Int) {
            val caption=text("$label: ${prefs.getInt(key,initial)}",14f);engine.addView(caption)
            engine.addView(SeekBar(this).apply { this.max=max-min;progress=prefs.getInt(key,initial)-min;setOnSeekBarChangeListener(object:SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(bar:SeekBar?,value:Int,fromUser:Boolean){caption.text="$label: ${value+min}";if(fromUser)prefs.edit().putInt(key,value+min).apply()}
                override fun onStartTrackingTouch(bar:SeekBar?){};override fun onStopTrackingTouch(bar:SeekBar?){}
            }) })
        }
        slider("Thread CPU al prossimo caricamento","threads",1,8,4)
        slider("Batteria minima (%)","min_battery",20,70,20)
        engine.addView(text("Contesto al prossimo caricamento",14f))
        val contexts=listOf(512,1024,2048,4096)
        engine.addView(Spinner(this).apply {adapter=ArrayAdapter(this@MainActivity,android.R.layout.simple_spinner_dropdown_item,contexts.map{"$it token"});setSelection(contexts.indexOf(prefs.getInt("n_ctx",2048)).coerceAtLeast(0));onItemSelectedListener=object:AdapterView.OnItemSelectedListener{
            override fun onItemSelected(parent:AdapterView<*>?,view:View?,position:Int,id:Long){prefs.edit().putInt("n_ctx",contexts[position]).apply()}
            override fun onNothingSelected(parent:AdapterView<*>?){}
        }})
        engine.addView(button("Scarica draft dal Mac e attiva") {
            if(Vault.load(this)==null)NodeService.status="Associa prima il computer"
            else {NodeService.downloadRequested.set(true);if(!NodeService.running)start(null)}
        })
        engine.addView(text("Scegli prima il draft nella dashboard del Mac. Download locale fino a 1 GiB con controllo SHA-256. Il nodo sospende le proposte con batteria bassa o stato termico moderato. Le opzioni CPU e contesto si applicano al prossimo caricamento.",13f,muted));root.addView(engine)
        val control=card(); control.addView(text("Il controllo resta tuo",20f)); control.addView(text("Il computer associato può avviare misure; le proposte LLM richiedono l’attivazione del motore qui sopra. Nessuna RAM è condivisa automaticamente.",14f,muted));control.addView(button("Metti in pausa") { stopService(Intent(this,NodeService::class.java)); NodeService.status="In pausa · nessun lavoro delegato" });control.addView(button("Dimentica computer") { stopService(Intent(this,NodeService::class.java)); Vault.clear(this); NodeService.status="Computer dimenticato" });root.addView(control)
        val measurement=card();measurement.addView(text("Ultima misura",20f));result=text(NodeService.lastResult,15f,mint);measurement.addView(result);measurement.addView(text("La RAM disponibile è un indicatore del sistema, non memoria già condivisa. I test sintetici non indicano token/s.",13f,muted));root.addView(measurement)
        root.addView(text("0.2 · Motore sperimentale\nTutto nella tua rete locale",12f,muted));scroll.addView(root);setContentView(scroll)
    }
    private fun start(value: String?) {
        if(Build.VERSION.SDK_INT>=33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED) requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS),42)
        startForegroundService(Intent(this,NodeService::class.java).apply { if(value!=null)putExtra("ticket",value) })
    }
    override fun onResume(){super.onResume();handler.post(render)}
    override fun onPause(){handler.removeCallbacks(render);super.onPause()}
}
