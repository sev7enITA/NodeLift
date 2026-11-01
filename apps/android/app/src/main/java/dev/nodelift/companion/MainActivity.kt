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
import android.text.Editable
import android.text.TextWatcher

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
    private lateinit var scan: Button
    private lateinit var engineInfo: TextView
    private lateinit var pauseButton: Button
    private lateinit var forgetButton: Button
    private lateinit var downloadButton: Button
    private lateinit var engineSwitch: Switch
    private lateinit var sessionBadge: TextView
    private lateinit var engineBadge: TextView
    private lateinit var feedback: TextView
    private lateinit var busyIndicator: ProgressBar
    private lateinit var engineProgress: ProgressBar
    private lateinit var supportNotice: TextView
    private var syncingSwitch=false
    private var starting=false
    private var stopping=false
    private var scannerPending=false
    private var startedAt=0L
    private var feedbackMessage:UiText?=null
    private var feedbackUntil=0L
    private var aboutDialog: android.app.Dialog? = null
    private val render = object: Runnable {
        override fun run() {
            updateState()
            handler.postDelayed(this, 1000)
        }
    }
    private fun updateState() {
        val notices = mutableListOf<String>()
        if (UpdateMonitor.available) notices += UpdateMonitor.message.render(this)
        if (Diagnostics.hasPreviousIncident) notices += t("A previous interruption was recorded. Export diagnostics from About & References.")
        val noticeText = notices.joinToString("\n\n")
        if (supportNotice.text.toString() != noticeText) supportNotice.text = noticeText
        supportNotice.visibility = if (notices.isEmpty()) View.GONE else View.VISIBLE
        val running=NodeService.running
        if(running)starting=false
        if(!running)stopping=false
        if(starting && SystemClock.elapsedRealtime()-startedAt>15000) {
            starting=false;NodeService.status=ui("Connection did not start. Try again.")
        }
        val saved=Vault.load(this)!=null
        val busy=starting || stopping || (running && !NodeService.connected)
        val loading=NodeService.modelLoading || NodeService.downloadRequested.get()
        state.text=NodeService.status.render(this)
        info.text=NodeService.telemetry.render(this).ifEmpty { "${Build.MANUFACTURER} ${Build.MODEL}\nAndroid ${Build.VERSION.RELEASE}" }
        result.text=NodeService.lastResult.render(this)
        sessionBadge.text=t(when {stopping->"Pausing…";busy->"Connecting…";running && NodeService.connected->"● Session active";saved->"○ Session paused";else->"○ Not paired"})
        sessionBadge.setTextColor(if(running && NodeService.connected)mint else if(busy)ControlUI.amber else muted)
        busyIndicator.visibility=if(busy)View.VISIBLE else View.GONE
        scan.isEnabled=!running && !starting && !scannerPending
        scan.text=t(if(scannerPending)"Opening camera…" else "Scan QR")
        connect.isEnabled=!running && !starting && ticket.text.isNotBlank()
        connect.text=t(if(starting)"Connecting…" else "Pair and activate node")
        resume.isEnabled=!running && !starting && saved
        resume.text=t(if(running && NodeService.connected)"✓ Session active" else if(starting || running)"Connecting…" else "Resume session")
        pauseButton.isEnabled=(running || starting) && !stopping
        pauseButton.text=t(if(stopping)"Pausing…" else "Pause node")
        forgetButton.isEnabled=saved && !starting && !stopping && !running
        engineInfo.text=NodeService.engineStatus.render(this)
        val enabled=getSharedPreferences("engine",0).getBoolean("enabled",false)
        syncingSwitch=true;engineSwitch.isChecked=enabled;syncingSwitch=false
        engineSwitch.isEnabled=!loading
        engineSwitch.text=t(if(enabled)"LLM proposals · ON" else "LLM proposals · OFF")
        ControlUI.describe(engineSwitch,t(if(enabled)"Enabled" else "Disabled"))
        engineBadge.text=t(when {loading->"Loading model…";enabled && NodeService.engineReady->"✓ Draft ready";enabled->"Enabled · waiting for a ready session";else->"Engine off"})
        engineBadge.setTextColor(if(enabled && NodeService.engineReady)mint else if(loading)ControlUI.amber else muted)
        engineProgress.visibility=if(loading)View.VISIBLE else View.GONE
        downloadButton.isEnabled=saved && !loading && !starting && !stopping
        downloadButton.text=t(if(loading)"Loading model…" else "Download draft from Mac and enable")
        for(button in listOf(scan,connect,resume,pauseButton,forgetButton,downloadButton)) {
            ControlUI.describe(button,t(if(button.isEnabled)"Available" else "Unavailable")+" · "+button.text)
        }
        if(SystemClock.elapsedRealtime()>feedbackUntil)feedbackMessage=null
        feedback.text=feedbackMessage?.render(this) ?: ""
        feedback.visibility=if(feedbackMessage==null)View.GONE else View.VISIBLE
    }
    private fun acknowledge(key:String) { feedbackMessage=ui(key);feedbackUntil=SystemClock.elapsedRealtime()+6000;if(::feedback.isInitialized){feedback.text=t(key);feedback.visibility=View.VISIBLE} }
    private fun t(key: String, vararg args: Any) = L10n.text(this,key,*args)
    private fun dp(v: Int) = (v*resources.displayMetrics.density).toInt()
    private fun text(value: String, size: Float = 16f, color: Int = ink): TextView = TextView(this).apply { text=t(value); textSize=size; setTextColor(color); setPadding(0,dp(6),0,dp(6)) }
    private fun card(): LinearLayout = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(dp(20),dp(18),dp(20),dp(18)); background=GradientDrawable().apply { setColor(Color.rgb(19,35,45)); cornerRadius=dp(16).toFloat() }; layoutParams=LinearLayout.LayoutParams(-1,-2).apply { bottomMargin=dp(16) } }
    private fun button(label:String,tone:ControlUI.Tone=ControlUI.Tone.SECONDARY,callback:()->Unit)=Button(this).apply {
        text=t(label);ControlUI.style(this,tone)
        layoutParams=LinearLayout.LayoutParams(-1,-2).apply{topMargin=dp(6);bottomMargin=dp(6)}
        setOnClickListener{performHapticFeedback(android.view.HapticFeedbackConstants.VIRTUAL_KEY);callback();updateState()}
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        scannerPending=savedInstanceState?.getBoolean("scanner_pending") ?: false
        buildScreen()
        if (savedInstanceState == null) consumeLink(intent)
    }
    private fun buildScreen() {
        val pendingTicket=if(::ticket.isInitialized)ticket.text.toString() else ""
        val scroll = ScrollView(this).apply { setBackgroundColor(bg); isFillViewport=true }
        val root = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(dp(24),dp(24),dp(24),dp(32)) }
        root.setOnApplyWindowInsetsListener { v,insets -> v.setPadding(dp(24),dp(24)+insets.systemWindowInsetTop,dp(24),dp(32)+insets.systemWindowInsetBottom); insets }
        root.addView(LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL; gravity = android.view.Gravity.CENTER_VERTICAL
            addView(ImageView(this@MainActivity).apply {
                setImageResource(R.drawable.ic_node_mark); importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            }, LinearLayout.LayoutParams(dp(48), dp(48)).apply { marginEnd = dp(12) })
            addView(text("NodeLift",30f).apply { setTypeface(null,Typeface.BOLD) })
        })
        root.addView(button("About & References") {
            aboutDialog?.dismiss()
            aboutDialog = showAbout(this)
        })
        supportNotice = text("",14f,ControlUI.amber).apply {
            visibility = View.GONE
            accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_POLITE
        }
        root.addView(supportNotice)
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
        root.addView(text("More life for your hardware.\nOne node, new possibilities.",23f).apply { setPadding(0,dp(14),0,dp(16)) })
        val statusCard=card();sessionBadge=text("SESSION",12f,mint).apply{setTypeface(null,Typeface.BOLD);accessibilityLiveRegion=View.ACCESSIBILITY_LIVE_REGION_POLITE};statusCard.addView(sessionBadge)
        state=text(NodeService.status.render(this),19f);statusCard.addView(state)
        busyIndicator=ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal).apply{isIndeterminate=true;indeterminateTintList=android.content.res.ColorStateList.valueOf(mint)};statusCard.addView(busyIndicator)
        info=text("",14f,muted);statusCard.addView(info)
        feedback=text("",14f,mint).apply{accessibilityLiveRegion=View.ACCESSIBILITY_LIVE_REGION_POLITE};statusCard.addView(feedback)
        root.addView(statusCard)
        val pairing=card(); pairing.addView(text("Pair your computer",20f)); pairing.addView(text("Choose Add device on your computer, then scan its QR code. Keep both devices on the same local network or phone hotspot.",14f,muted))
        scan=button("Scan QR",ControlUI.Tone.PRIMARY) {
            scannerPending=true;acknowledge("Opening camera…");updateState()
            if(checkSelfPermission(Manifest.permission.CAMERA)==PackageManager.PERMISSION_GRANTED)openScanner()
            else try{requestPermissions(arrayOf(Manifest.permission.CAMERA),43)}catch(_:Exception){scannerPending=false;acknowledge("Camera unavailable. Use manual pairing.")}
        };pairing.addView(scan)
        pairing.addView(text("Pause an active session before pairing another computer.",13f,muted))
        val manual=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;visibility=View.GONE}
        pairing.addView(button("Manual pairing"){}.apply{setOnClickListener{
            val expanded=manual.visibility!=View.VISIBLE;manual.visibility=if(expanded)View.VISIBLE else View.GONE
            isSelected=expanded;text=t(if(expanded)"▾ Hide manual pairing" else "▸ Manual pairing")
            ControlUI.describe(this,t(if(expanded)"Expanded" else "Collapsed"))
        }})
        ticket=EditText(this).apply { hint=t("Paste your NodeLift invitation"); setTextColor(ink); setHintTextColor(muted); minLines=2; maxLines=4; textSize=13f; importantForAutofill=View.IMPORTANT_FOR_AUTOFILL_NO_EXCLUDE_DESCENDANTS }
        ticket.setText(pendingTicket)
        manual.addView(ticket)
        connect=button("Pair and activate node",ControlUI.Tone.PRIMARY) {
            val value=ticket.text.toString().trim()
            try { val obj=PairingCode.decode(value); start(obj.toString()); ticket.text.clear() }
            catch(e:Exception) { NodeService.status=ui(e.message ?: "Invalid invitation") }
        }
        manual.addView(connect);pairing.addView(manual)
        ticket.addTextChangedListener(object:TextWatcher{
            override fun beforeTextChanged(s:CharSequence?,start:Int,count:Int,after:Int){}
            override fun onTextChanged(s:CharSequence?,start:Int,before:Int,count:Int){if(::pauseButton.isInitialized)updateState()}
            override fun afterTextChanged(s:Editable?){}
        })
        resume=button("Resume session"){start(null)};pairing.addView(resume);root.addView(pairing)
        val prefs=getSharedPreferences("engine",0)
        val engine=card();engine.addView(text("EXPERIMENTAL ENGINE",11f,mint));engine.addView(text("Your phone proposes.\nYour Mac verifies.",23f));engineInfo=text(NodeService.engineStatus.render(this),14f,mint);engine.addView(engineInfo)
        engine.addView(text("A small GGUF model on your phone proposes token blocks. The main model stays on your computer and verifies every proposal. ARM64 CPU backend; GPU/NPU are not enabled in this build.",14f,muted))
        engineBadge=text("Engine off",14f,muted);engine.addView(engineBadge)
        engineProgress=ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal).apply{isIndeterminate=true;indeterminateTintList=android.content.res.ColorStateList.valueOf(mint)};engine.addView(engineProgress)
        engineSwitch=Switch(this).apply {
            setTextColor(ink);minHeight=dp(56);setPadding(0,dp(8),0,dp(8));isChecked=prefs.getBoolean("enabled",false)
            thumbTintList=android.content.res.ColorStateList(arrayOf(intArrayOf(android.R.attr.state_checked),intArrayOf()),intArrayOf(mint,muted))
            trackTintList=android.content.res.ColorStateList(arrayOf(intArrayOf(android.R.attr.state_checked),intArrayOf()),intArrayOf(Color.rgb(43,128,109),Color.rgb(63,78,89)))
            setOnCheckedChangeListener{_,value->if(!syncingSwitch){prefs.edit().putBoolean("enabled",value).apply();acknowledge(if(value)"LLM permission enabled. Model readiness is shown below." else "LLM permission disabled.");updateState()}}
        };engine.addView(engineSwitch)
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
        downloadButton=button("Download draft from Mac and enable") {
            if(Vault.load(this)==null)NodeService.status=ui("Pair your computer first")
            else {NodeService.downloadRequested.set(true);acknowledge("Model download requested. Wait for Draft ready.");if(!NodeService.running)start(null)}
        };engine.addView(downloadButton)
        engine.addView(text("Select the draft in the Mac dashboard first. Local downloads support up to 1 GiB with SHA-256 verification. Proposals pause when battery is low or thermal status is moderate. CPU and context settings apply on the next load.",13f,muted));root.addView(engine)
        val control=card();control.addView(text("You stay in control",20f));control.addView(text("Your paired computer can start measurements. LLM proposals require enabling the engine above. RAM is not shared automatically.",14f,muted))
        pauseButton=button("Pause node"){stopping=true;starting=false;stopService(Intent(this,NodeService::class.java));acknowledge("Pause requested. Waiting for current work to stop.")};control.addView(pauseButton)
        forgetButton=button("Forget computer",ControlUI.Tone.DANGER){
            android.app.AlertDialog.Builder(this).setTitle(t("Forget computer"))
                .setMessage(t("Remove the saved pairing from this phone? To revoke its server access too, use Revoke on the computer."))
                .setNegativeButton(t("Cancel"),null).setPositiveButton(t("Forget computer")){_,_->Vault.clear(this);NodeService.status=ui("Computer forgotten");acknowledge("Computer forgotten");updateState()}.show()
        };control.addView(forgetButton);control.addView(text("Pause the node before removing its saved pairing.",13f,muted));root.addView(control)
        val measurement=card();measurement.addView(text("Last measurement",20f));result=text(NodeService.lastResult.render(this),15f,mint);measurement.addView(result);measurement.addView(text("Available RAM is a system indicator, not memory already shared. Synthetic tests do not indicate tokens/s.",13f,muted));root.addView(measurement)
        root.addView(text(installedCompanionVersion(this),12f,muted))
        root.addView(text("Experimental companion",12f,muted));scroll.addView(root);setContentView(scroll); updateState()
    }
    private fun openScanner() {
        if(NodeService.running){scannerPending=false;return}
        scannerPending=true
        try {startActivityForResult(Intent(this,QRScannerActivity::class.java),QRScannerActivity.REQUEST)}
        catch(_:Exception){scannerPending=false;acknowledge("Camera unavailable. Use manual pairing.");updateState()}
    }
    override fun onRequestPermissionsResult(code:Int,permissions:Array<out String>,results:IntArray) {
        super.onRequestPermissionsResult(code,permissions,results)
        if(code==43) {
            if(results.firstOrNull()==PackageManager.PERMISSION_GRANTED)openScanner()
            else {scannerPending=false;acknowledge("Camera access is required to scan. Enable it in Settings or use manual pairing.");updateState()}
        }
    }
    override fun onActivityResult(code:Int,resultCode:Int,data:Intent?) {
        super.onActivityResult(code,resultCode,data)
        if(code==QRScannerActivity.REQUEST) {
            scannerPending=false
            val value=data?.getStringExtra(QRScannerActivity.RESULT_CODE)
            if(resultCode==RESULT_OK && value!=null)acceptCode(value)
            else acknowledge(data?.getStringExtra(QRScannerActivity.RESULT_ERROR) ?: "Scan cancelled. No pairing changed.")
            updateState()
        }
    }
    override fun onSaveInstanceState(out:Bundle){out.putBoolean("scanner_pending",scannerPending);super.onSaveInstanceState(out)}
    override fun onNewIntent(value:Intent) { super.onNewIntent(value);consumeLink(value) }
    private fun consumeLink(value:Intent?) {
        val link=value?.dataString ?: return
        value.data=null // Do not retain a single-use invitation in the activity intent.
        acceptCode(link)
    }
    private fun acceptCode(value:String) {
        if(NodeService.running){NodeService.status=ui("Pause the node before pairing another computer.");return}
        try {
            val obj=PairingCode.decode(value); val pairing=Pairing.parse(obj)
            android.app.AlertDialog.Builder(this).setTitle(t("Pair your computer"))
                .setMessage(t("Computer: {0} · Identity: {1}",java.net.URL(pairing.url).authority,pairing.sha256.take(16)))
                .setNegativeButton(t("Cancel"),null)
                .setPositiveButton(t("Pair and activate node")){_,_->
                    try{if(!NodeService.running){start(PairingCode.decode(obj.toString()).toString());ticket.text.clear()}}
                    catch(e:Exception){NodeService.status=ui(e.message ?: "Invalid invitation")}
                }.show()
        } catch(e:Exception){NodeService.status=ui(e.message ?: "Invalid invitation")}
    }
    private fun start(value: String?) {
        if(starting || NodeService.running)return
        starting=true;startedAt=SystemClock.elapsedRealtime();NodeService.status=ui("Connecting to your computer…");acknowledge("Connection requested…");updateState()
        try {
            if(Build.VERSION.SDK_INT>=33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS),42)
            startForegroundService(Intent(this,NodeService::class.java).apply{if(value!=null)putExtra("ticket",value)})
        }catch(_:Exception){starting=false;NodeService.downloadRequested.set(false);NodeService.status=ui("Connection did not start. Try again.");acknowledge("Connection did not start. Try again.");updateState()}
    }
    override fun onResume(){super.onResume();UpdateMonitor.onResume(this);handler.removeCallbacks(render);handler.post(render)}
    override fun onPause(){handler.removeCallbacks(render);super.onPause()}
    override fun onDestroy(){aboutDialog?.dismiss();aboutDialog=null;super.onDestroy()}
}
