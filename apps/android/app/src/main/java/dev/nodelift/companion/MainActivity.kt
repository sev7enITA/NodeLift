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
            updateState()
            handler.postDelayed(this, 1000)
        }
    }
    private fun updateState() {
            state.text = NodeService.status.render(this@MainActivity); info.text = NodeService.telemetry.render(this@MainActivity).ifEmpty { "${Build.MANUFACTURER} ${Build.MODEL}\nAndroid ${Build.VERSION.RELEASE}" }; result.text = NodeService.lastResult.render(this@MainActivity)
            connect.isEnabled = !NodeService.running; resume.isEnabled = !NodeService.running && Vault.load(this@MainActivity) != null
            engineInfo.text=NodeService.engineStatus.render(this@MainActivity)
    }
    private fun t(key: String, vararg args: Any) = L10n.text(this,key,*args)
    private fun dp(v: Int) = (v*resources.displayMetrics.density).toInt()
    private fun text(value: String, size: Float = 16f, color: Int = ink): TextView = TextView(this).apply { text=t(value); textSize=size; setTextColor(color); setPadding(0,dp(6),0,dp(6)) }
    private fun card(): LinearLayout = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(dp(20),dp(18),dp(20),dp(18)); background=GradientDrawable().apply { setColor(Color.rgb(19,35,45)); cornerRadius=dp(16).toFloat() }; layoutParams=LinearLayout.LayoutParams(-1,-2).apply { bottomMargin=dp(16) } }
    private fun button(label: String, callback: ()->Unit) = Button(this).apply { text=t(label); isAllCaps=false; setTextColor(bg); backgroundTintList=android.content.res.ColorStateList.valueOf(mint); minHeight=dp(48); setOnClickListener { callback() } }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        buildScreen()
    }
    private fun buildScreen() {
        val pendingTicket=if(::ticket.isInitialized)ticket.text.toString() else ""
        val scroll = ScrollView(this).apply { setBackgroundColor(bg); isFillViewport=true }
        val root = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(dp(24),dp(24),dp(24),dp(32)) }
        root.setOnApplyWindowInsetsListener { v,insets -> v.setPadding(dp(24),dp(24)+insets.systemWindowInsetTop,dp(24),dp(32)+insets.systemWindowInsetBottom); insets }
        root.addView(text("◈ NodeLift",30f).apply { setTypeface(null,Typeface.BOLD) })
        root.addView(text("Language",12f,muted))
        root.addView(Spinner(this).apply {
            contentDescription=t("Language")
            val languages=listOf("en","zh-Hans","it")
            adapter=ArrayAdapter(this@MainActivity,android.R.layout.simple_spinner_dropdown_item,listOf("English","简体中文","Italiano"))
            setSelection(languages.indexOf(L10n.language(this@MainActivity)))
            onItemSelectedListener=object:AdapterView.OnItemSelectedListener {
                override fun onItemSelected(parent:AdapterView<*>?,view:View?,position:Int,id:Long) {
                    val selected=languages[position]
                    if(selected!=L10n.language(this@MainActivity)) {
                        L10n.select(this@MainActivity,selected)
                        NodeService.refreshNotification(this@MainActivity)
                        buildScreen()
                    }
                }
                override fun onNothingSelected(parent:AdapterView<*>?) {}
            }
        })
        root.addView(text("YOUR DEVICE. A NEW NODE.",11f,mint))
        root.addView(text("More life for your hardware.\nOne node, new possibilities.",27f).apply { setPadding(0,dp(24),0,dp(20)) })
        val statusCard=card(); statusCard.addView(text("SESSION",11f,mint)); state=text(NodeService.status.render(this),19f); statusCard.addView(state); info=text("",14f,muted); statusCard.addView(info); root.addView(statusCard)
        val pairing=card(); pairing.addView(text("Pair your computer",20f)); pairing.addView(text("Choose “Add device” in the NodeLift dashboard, then paste the invitation here. It is private, temporary and single-use.",14f,muted))
        ticket=EditText(this).apply { hint=t("Paste your NodeLift invitation"); setTextColor(ink); setHintTextColor(muted); minLines=2; maxLines=4; textSize=13f; importantForAutofill=View.IMPORTANT_FOR_AUTOFILL_NO_EXCLUDE_DESCENDANTS }
        ticket.setText(pendingTicket)
        pairing.addView(ticket)
        connect=button("Pair and activate node") {
            val value=ticket.text.toString().trim()
            try { val obj=org.json.JSONObject(value); require(obj.getInt("protocol")==1); require(obj.getDouble("expires_at")>System.currentTimeMillis()/1000.0) { "Invitation expired. Create a new one." }; Pairing.parse(obj); start(value); ticket.text.clear() }
            catch(e:Exception) { NodeService.status=ui(e.message ?: "Invalid invitation") }
        }
        pairing.addView(connect); resume=button("Resume session") { start(null) }; pairing.addView(resume); root.addView(pairing)
        val prefs=getSharedPreferences("engine",0)
        val engine=card();engine.addView(text("EXPERIMENTAL ENGINE",11f,mint));engine.addView(text("Your phone proposes.\nYour Mac verifies.",23f));engineInfo=text(NodeService.engineStatus.render(this),14f,mint);engine.addView(engineInfo)
        engine.addView(text("A small GGUF model on your phone proposes token blocks. The main model stays on your computer and verifies every proposal. ARM64 CPU backend; GPU/NPU are not enabled in this build.",14f,muted))
        engine.addView(Switch(this).apply { text=t("Allow LLM proposals");setTextColor(ink);isChecked=prefs.getBoolean("enabled",false);setOnCheckedChangeListener { _,value -> prefs.edit().putBoolean("enabled",value).apply() } })
        fun slider(label:String,key:String,min:Int,max:Int,initial:Int) {
            val caption=text("${t(label)}: ${prefs.getInt(key,initial)}",14f);engine.addView(caption)
            engine.addView(SeekBar(this).apply { this.max=max-min;progress=prefs.getInt(key,initial)-min;setOnSeekBarChangeListener(object:SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(bar:SeekBar?,value:Int,fromUser:Boolean){caption.text="${t(label)}: ${value+min}";if(fromUser)prefs.edit().putInt(key,value+min).apply()}
                override fun onStartTrackingTouch(bar:SeekBar?){};override fun onStopTrackingTouch(bar:SeekBar?){}
            }) })
        }
        slider("CPU threads on next load","threads",1,8,4)
        slider("Minimum battery (%)","min_battery",20,70,20)
        engine.addView(text("Context on next load",14f))
        val contexts=listOf(512,1024,2048,4096)
        engine.addView(Spinner(this).apply {adapter=ArrayAdapter(this@MainActivity,android.R.layout.simple_spinner_dropdown_item,contexts.map{t("{0} tokens",it)});setSelection(contexts.indexOf(prefs.getInt("n_ctx",2048)).coerceAtLeast(0));onItemSelectedListener=object:AdapterView.OnItemSelectedListener{
            override fun onItemSelected(parent:AdapterView<*>?,view:View?,position:Int,id:Long){prefs.edit().putInt("n_ctx",contexts[position]).apply()}
            override fun onNothingSelected(parent:AdapterView<*>?){}
        }})
        engine.addView(button("Download draft from Mac and enable") {
            if(Vault.load(this)==null)NodeService.status=ui("Pair your computer first")
            else {NodeService.downloadRequested.set(true);if(!NodeService.running)start(null)}
        })
        engine.addView(text("Select the draft in the Mac dashboard first. Local downloads support up to 1 GiB with SHA-256 verification. Proposals pause when battery is low or thermal status is moderate. CPU and context settings apply on the next load.",13f,muted));root.addView(engine)
        val control=card(); control.addView(text("You stay in control",20f)); control.addView(text("Your paired computer can start measurements. LLM proposals require enabling the engine above. RAM is not shared automatically.",14f,muted));control.addView(button("Pause node") { stopService(Intent(this,NodeService::class.java)); NodeService.status=ui("Paused · no delegated work") });control.addView(button("Forget computer") { stopService(Intent(this,NodeService::class.java)); Vault.clear(this); NodeService.status=ui("Computer forgotten") });root.addView(control)
        val measurement=card();measurement.addView(text("Last measurement",20f));result=text(NodeService.lastResult.render(this),15f,mint);measurement.addView(result);measurement.addView(text("Available RAM is a system indicator, not memory already shared. Synthetic tests do not indicate tokens/s.",13f,muted));root.addView(measurement)
        root.addView(text("0.2.3 · Experimental companion\nEverything on your local network",12f,muted));scroll.addView(root);setContentView(scroll); updateState()
    }
    private fun start(value: String?) {
        if(Build.VERSION.SDK_INT>=33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED) requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS),42)
        startForegroundService(Intent(this,NodeService::class.java).apply { if(value!=null)putExtra("ticket",value) })
    }
    override fun onResume(){super.onResume();handler.post(render)}
    override fun onPause(){handler.removeCallbacks(render);super.onPause()}
}
