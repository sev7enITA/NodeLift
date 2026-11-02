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
    private lateinit var homeAction: Button
    private lateinit var nextStep: TextView
    private lateinit var activityFeedback: TextView
    private lateinit var draftSummary: TextView
    private lateinit var contactAge: TextView
    private lateinit var pairedComputer: TextView
    private lateinit var assessment: TextView
    private lateinit var modelSetupHeading: TextView
    private lateinit var draftCard: LinearLayout
    private val pages = mutableListOf<View>()
    private val navigation = mutableListOf<Button>()
    private var selectedPage = 0
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
    private lateinit var releaseButton:Button
    private fun updateState() {
        val notices = mutableListOf<String>()
        if (UpdateMonitor.available) notices += UpdateMonitor.message.render(this)
        if(::releaseButton.isInitialized) releaseButton.visibility=if(UpdateMonitor.available && !UpdateMonitor.checking && UpdateMonitor.details!=null)View.VISIBLE else View.GONE
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
        val savedSession=Vault.load(this)
        val saved=savedSession!=null
        val computer=try{savedSession?.optJSONObject("pairing")?.optString("url")?.let{java.net.URL(it).host}}catch(_:Exception){null}
        setTextIfChanged(pairedComputer,if(!computer.isNullOrBlank())t("Paired computer: {0}",computer) else "")
        pairedComputer.visibility=if(computer.isNullOrBlank())View.GONE else View.VISIBLE
        draftCard.visibility=if(saved)View.VISIBLE else View.GONE
        val busy=starting || stopping || (running && !NodeService.connected)
        val loading=NodeService.modelLoading || NodeService.downloadRequested.get()
        val assessing=NodeService.diagnosticRunning
        val assessmentText=NodeService.assessmentStatus.render(this)
        setTextIfChanged(assessment,assessmentText)
        assessment.visibility=if(assessmentText.isBlank())View.GONE else View.VISIBLE
        val age=NodeService.contactAgeSeconds
        setTextIfChanged(state,if(running && age!=null && age>=20)t("Waiting for a recent response from the computer") else NodeService.status.render(this))
        setTextIfChanged(contactAge,if(age!=null)t("Last response: {0} s ago",age) else t("No response yet"))
        info.text=NodeService.telemetry.render(this).ifEmpty { "${Build.MANUFACTURER} ${Build.MODEL}\nAndroid ${Build.VERSION.RELEASE}" }
        result.text=NodeService.lastResult.render(this)
        setTextIfChanged(sessionBadge,t(when {stopping->"Pausing…";running && age!=null && age>=20->"Connection needs checking";busy->"Connecting…";running && NodeService.connected->"● Session active";saved->"○ Session paused";else->"○ Not paired"}))
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
        engineSwitch.isEnabled=!loading && !assessing
        engineSwitch.text=t(if(enabled)"LLM proposals · ON" else "LLM proposals · OFF")
        ControlUI.describe(engineSwitch,t(if(enabled)"Enabled" else "Disabled")+" · "+engineSwitch.text)
        setTextIfChanged(engineBadge,t(when {loading->"Loading model…";enabled && NodeService.engineReady->"✓ Draft ready";enabled->"Enabled · waiting for a ready session";else->"Engine off"}))
        engineBadge.setTextColor(if(enabled && NodeService.engineReady)mint else if(loading)ControlUI.amber else muted)
        engineProgress.visibility=if(loading)View.VISIBLE else View.GONE
        downloadButton.isEnabled=saved && !loading && !starting && !stopping && !assessing
        downloadButton.text=t(if(loading)"Loading model…" else "Download draft from Mac and enable")
        val action=HomeAction.choose(saved,running,NodeService.connected,loading,NodeService.engineReady,starting||stopping||scannerPending,NodeService.diagnosticRunning)
        setTextIfChanged(homeAction,t(if(scannerPending)"Opening camera…" else action.label));homeAction.isEnabled=action.enabled
        setTextIfChanged(nextStep,t(action.guidance))
        draftSummary.text=t("Draft readiness is separate from measured contribution. See the computer for assessment and accepted tokens.")
        pauseButton.visibility=if(running && action !in listOf(HomeAction.PAUSE,HomeAction.ASSESSING))View.VISIBLE else View.GONE
        for(button in listOf(scan,connect,resume,pauseButton,forgetButton,downloadButton,homeAction)) {
            ControlUI.describe(button,t(if(button.isEnabled)"Available" else "Unavailable")+" · "+button.text)
        }
        if(SystemClock.elapsedRealtime()>feedbackUntil)feedbackMessage=null
        setTextIfChanged(feedback,feedbackMessage?.render(this) ?: "")
        feedback.visibility=if(feedbackMessage==null)View.GONE else View.VISIBLE
        setTextIfChanged(activityFeedback,feedbackMessage?.render(this) ?: "")
        activityFeedback.visibility=if(feedbackMessage==null)View.GONE else View.VISIBLE
    }
    private fun setTextIfChanged(view:TextView,value:String){if(view.text.toString()!=value)view.text=value}
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
        selectedPage=savedInstanceState?.getInt("selected_page",0) ?: 0
        buildScreen()
        if (savedInstanceState == null) consumeLink(intent)
    }
    private fun showPage(index:Int) {
        selectedPage=index.coerceIn(0,2)
        pages.forEachIndexed { i,page -> page.visibility=if(i==selectedPage)View.VISIBLE else View.GONE }
        navigation.forEachIndexed { i,button ->
            button.isSelected=i==selectedPage
            button.text=(if(i==selectedPage)"✓ " else "")+t(button.tag as String)
            ControlUI.describe(button,button.text.toString()+" · "+t(if(i==selectedPage)"Selected" else "Available"))
        }
    }
    private fun openModelSettings() {
        if(NodeService.diagnosticRunning)return
        showPage(2)
        modelSetupHeading.post {
            modelSetupHeading.requestRectangleOnScreen(android.graphics.Rect(0,0,modelSetupHeading.width,modelSetupHeading.height),true)
            modelSetupHeading.requestFocus()
        }
    }
    private fun heading(label:String)=text(label,24f).apply {
        setTypeface(null,Typeface.BOLD)
        if(Build.VERSION.SDK_INT>=28)isAccessibilityHeading=true
    }
    private fun openAbout(){aboutDialog?.dismiss();aboutDialog=showAbout(this)}
    private fun scanCode(){
        if(scannerPending || starting || NodeService.running)return
        scannerPending=true;acknowledge("Opening camera…");updateState()
        if(checkSelfPermission(Manifest.permission.CAMERA)==PackageManager.PERMISSION_GRANTED)openScanner()
        else try{requestPermissions(arrayOf(Manifest.permission.CAMERA),43)}catch(_:Exception){scannerPending=false;acknowledge("Camera unavailable. Use manual pairing.")}
    }
    private fun buildScreen() {
        val pendingTicket=if(::ticket.isInitialized)ticket.text.toString() else ""
        pages.clear();navigation.clear()
        val shell=LinearLayout(this).apply {orientation=LinearLayout.VERTICAL;setBackgroundColor(bg)}
        shell.setOnApplyWindowInsetsListener { view,insets -> view.setPadding(0,insets.systemWindowInsetTop,0,insets.systemWindowInsetBottom);insets }
        val frame=FrameLayout(this)
        fun page():LinearLayout {
            val content=LinearLayout(this).apply {orientation=LinearLayout.VERTICAL;setPadding(dp(20),dp(20),dp(20),dp(24))}
            val scroll=ScrollView(this).apply {isFillViewport=true;addView(content)}
            frame.addView(scroll,FrameLayout.LayoutParams(-1,-1));pages.add(scroll);return content
        }
        val home=page();val activity=page();val settings=page()
        home.addView(LinearLayout(this).apply {
            orientation=LinearLayout.HORIZONTAL;gravity=android.view.Gravity.CENTER_VERTICAL
            addView(ImageView(this@MainActivity).apply {setImageResource(R.drawable.nodelift_emblem);importantForAccessibility=View.IMPORTANT_FOR_ACCESSIBILITY_NO},LinearLayout.LayoutParams(dp(44),dp(44)).apply{marginEnd=dp(12)})
            addView(heading("NodeLift"))
        })
        home.addView(text("Your phone, ready to help",18f,muted))
        supportNotice=text("",15f,ControlUI.amber).apply {visibility=View.GONE;accessibilityLiveRegion=View.ACCESSIBILITY_LIVE_REGION_POLITE};home.addView(supportNotice)
        releaseButton=button("View release notes & download"){UpdateMonitor.details?.let{showReleaseDetails(this,it)}}.apply{visibility=View.GONE}
        home.addView(releaseButton)
        val statusCard=card()
        statusCard.addView(text("Computer connection",16f,muted))
        sessionBadge=text("SESSION",18f,mint).apply {setTypeface(null,Typeface.BOLD);accessibilityLiveRegion=View.ACCESSIBILITY_LIVE_REGION_POLITE};statusCard.addView(sessionBadge)
        state=text("",16f);statusCard.addView(state)
        contactAge=text("",15f,muted);statusCard.addView(contactAge)
        assessment=text("",16f,ControlUI.amber).apply{accessibilityLiveRegion=View.ACCESSIBILITY_LIVE_REGION_POLITE;visibility=View.GONE};statusCard.addView(assessment)
        pairedComputer=text("",15f,muted);statusCard.addView(pairedComputer)
        busyIndicator=ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal).apply{isIndeterminate=true;indeterminateTintList=android.content.res.ColorStateList.valueOf(mint)};statusCard.addView(busyIndicator)
        feedback=text("",15f,mint).apply{accessibilityLiveRegion=View.ACCESSIBILITY_LIVE_REGION_POLITE};statusCard.addView(feedback)
        home.addView(statusCard)
        val readyCard=card();draftCard=readyCard;readyCard.addView(text("Draft model",16f,muted))
        engineBadge=text("Engine off",18f,muted).apply{setTypeface(null,Typeface.BOLD)};readyCard.addView(engineBadge)
        draftSummary=text("",15f,muted);readyCard.addView(draftSummary);home.addView(readyCard)
        nextStep=text("",16f);home.addView(nextStep)
        homeAction=button("Scan QR",ControlUI.Tone.PRIMARY){
            when(HomeAction.choose(Vault.load(this)!=null,NodeService.running,NodeService.connected,NodeService.modelLoading||NodeService.downloadRequested.get(),NodeService.engineReady,starting||stopping||scannerPending,NodeService.diagnosticRunning)) {
                HomeAction.PAIR->scanCode()
                HomeAction.RESUME->start(null)
                HomeAction.SETUP->openModelSettings()
                HomeAction.PAUSE,HomeAction.ASSESSING->pauseButton.performClick()
                else->Unit
            }
        }.apply{accessibilityLiveRegion=View.ACCESSIBILITY_LIVE_REGION_POLITE};home.addView(homeAction)
        pauseButton=button("Pause node"){stopping=true;starting=false;stopService(Intent(this,NodeService::class.java));acknowledge("Pause requested. Waiting for current work to stop.")};home.addView(pauseButton)
        home.addView(text("You choose when this phone contributes. RAM is not pooled automatically.",15f,muted))
        activity.addView(heading("Activity"))
        activity.addView(text("Measurements and support",16f,muted))
        val measurement=card();measurement.addView(text("Last measurement",20f));result=text("",16f,mint);measurement.addView(result)
        measurement.addView(text("Available RAM is a system indicator, not memory already shared. Synthetic tests do not indicate tokens/s.",15f,muted));activity.addView(measurement)
        val inventory=card();inventory.addView(text("Device details",20f));info=text("",16f,muted);inventory.addView(info);activity.addView(inventory)
        activity.addView(button("Export diagnostics") {acknowledge(if(Diagnostics.export(this))"Diagnostic report prepared. Choose where to save or share it." else "Unable to export diagnostics. Try again.")})
        activityFeedback=text("",15f,mint).apply{visibility=View.GONE;accessibilityLiveRegion=View.ACCESSIBILITY_LIVE_REGION_POLITE};activity.addView(activityFeedback)
        activity.addView(text("Logs stay on this phone until you choose to share them.",15f,muted))
        settings.addView(heading("Settings"))
        settings.addView(button("About & References"){openAbout()})
        settings.addView(text("Language",16f,muted))
        settings.addView(Spinner(this).apply {
            minimumHeight=dp(48);contentDescription=t("Language")
            val languages=listOf("en","zh-Hans","it")
            adapter=ArrayAdapter(this@MainActivity,android.R.layout.simple_spinner_dropdown_item,listOf("English","简体中文","Italiano"))
            setSelection(languages.indexOf(L10n.language(this@MainActivity)))
            onItemSelectedListener=object:AdapterView.OnItemSelectedListener {
                override fun onItemSelected(parent:AdapterView<*>?,view:View?,position:Int,id:Long){val selected=languages[position];if(selected!=L10n.language(this@MainActivity)){L10n.select(this@MainActivity,selected);NodeService.refreshNotification(this@MainActivity);buildScreen()}}
                override fun onNothingSelected(parent:AdapterView<*>?){}
            }
        })
        val prefs=getSharedPreferences("engine",0)
        val engine=card();modelSetupHeading=heading("Draft model").apply{isFocusable=true;isFocusableInTouchMode=true};engine.addView(modelSetupHeading);engineInfo=text("",16f,mint);engine.addView(engineInfo)
        engine.addView(text("A small GGUF model on your phone proposes token blocks. The main model stays on your computer and verifies every proposal. ARM64 CPU backend; GPU/NPU are not enabled in this build.",15f,muted))
        engineProgress=ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal).apply{isIndeterminate=true;indeterminateTintList=android.content.res.ColorStateList.valueOf(mint)};engine.addView(engineProgress)
        engineSwitch=Switch(this).apply {
            setTextColor(ink);textSize=16f;minHeight=dp(56);setPadding(0,dp(8),0,dp(8));isChecked=prefs.getBoolean("enabled",false)
            thumbTintList=android.content.res.ColorStateList(arrayOf(intArrayOf(android.R.attr.state_checked),intArrayOf()),intArrayOf(mint,muted))
            trackTintList=android.content.res.ColorStateList(arrayOf(intArrayOf(android.R.attr.state_checked),intArrayOf()),intArrayOf(Color.rgb(43,128,109),Color.rgb(63,78,89)))
            setOnCheckedChangeListener{_,value->if(!syncingSwitch){prefs.edit().putBoolean("enabled",value).apply();acknowledge(if(value)"LLM permission enabled. Model readiness is shown below." else "LLM permission disabled.");updateState()}}
        };engine.addView(engineSwitch)
        downloadButton=button("Download draft from Mac and enable") {
            if(NodeService.diagnosticRunning){acknowledge("Assessment running");return@button}
            if(Vault.load(this)==null)NodeService.status=ui("Pair your computer first")
            else {NodeService.downloadRequested.set(true);acknowledge("Model download requested. Wait for Draft ready.");if(!NodeService.running)start(null)}
        };engine.addView(downloadButton)
        engine.addView(text("Select the draft in the Mac dashboard first. Local downloads support up to 1 GiB with SHA-256 verification. Proposals pause when battery is low or thermal status is moderate. CPU and context settings apply on the next load.",15f,muted))
        val resources=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;visibility=View.GONE}
        engine.addView(button("Resource limits"){}.apply{setOnClickListener{
            val expanded=resources.visibility!=View.VISIBLE;resources.visibility=if(expanded)View.VISIBLE else View.GONE
            isSelected=expanded;ControlUI.describe(this,text.toString()+" · "+t(if(expanded)"Expanded" else "Collapsed"))
        }})
        fun slider(label:String,key:String,min:Int,max:Int,initial:Int) {
            val caption=text("${t(label)}: ${prefs.getInt(key,initial)}",16f);caption.id=View.generateViewId();resources.addView(caption)
            resources.addView(SeekBar(this).apply {
                minimumHeight=dp(48);this.max=max-min;progress=prefs.getInt(key,initial)-min;contentDescription=t(label)
                setOnSeekBarChangeListener(object:SeekBar.OnSeekBarChangeListener {
                    override fun onProgressChanged(bar:SeekBar?,value:Int,fromUser:Boolean){caption.text="${t(label)}: ${value+min}";ControlUI.describe(this@apply,"${t(label)}: ${value+min}");if(fromUser)prefs.edit().putInt(key,value+min).apply()}
                    override fun onStartTrackingTouch(bar:SeekBar?){};override fun onStopTrackingTouch(bar:SeekBar?){}
                })
            })
        }
        slider("CPU threads on next load","threads",1,8,4);slider("Minimum battery (%)","min_battery",20,70,20)
        resources.addView(text("Context on next load",16f));val contexts=listOf(512,1024,2048,4096)
        resources.addView(Spinner(this).apply {minimumHeight=dp(48);contentDescription=t("Context on next load");adapter=ArrayAdapter(this@MainActivity,android.R.layout.simple_spinner_dropdown_item,contexts.map{t("{0} tokens",it)});setSelection(contexts.indexOf(prefs.getInt("n_ctx",2048)).coerceAtLeast(0));onItemSelectedListener=object:AdapterView.OnItemSelectedListener{
            override fun onItemSelected(parent:AdapterView<*>?,view:View?,position:Int,id:Long){prefs.edit().putInt("n_ctx",contexts[position]).apply()}
            override fun onNothingSelected(parent:AdapterView<*>?){}
        }})
        engine.addView(resources);settings.addView(engine)
        val pairCard=card();pairCard.addView(text("Computer pairing",20f));pairCard.addView(text("Choose Add device on your computer, then scan its QR code. Keep both devices on the same local network or phone hotspot.",15f,muted))
        scan=button("Scan QR"){scanCode()};pairCard.addView(scan)
        resume=button("Resume session"){start(null)};pairCard.addView(resume)
        pairCard.addView(text("Pause an active session before pairing another computer.",15f,muted))
        val manual=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;visibility=View.GONE}
        pairCard.addView(button("Manual pairing"){}.apply{setOnClickListener{
            val expanded=manual.visibility!=View.VISIBLE;manual.visibility=if(expanded)View.VISIBLE else View.GONE
            isSelected=expanded;ControlUI.describe(this,text.toString()+" · "+t(if(expanded)"Expanded" else "Collapsed"))
        }})
        ticket=EditText(this).apply {hint=t("Paste your NodeLift invitation");contentDescription=t("NodeLift invitation");setTextColor(ink);setHintTextColor(muted);minLines=2;maxLines=4;textSize=16f;importantForAutofill=View.IMPORTANT_FOR_AUTOFILL_NO_EXCLUDE_DESCENDANTS};ticket.setText(pendingTicket);manual.addView(ticket)
        connect=button("Pair and activate node"){
            try{val obj=PairingCode.decode(ticket.text.toString().trim());acceptCode(obj.toString())}catch(e:Exception){NodeService.status=ui(e.message?:"Invalid invitation")}
        };manual.addView(connect);pairCard.addView(manual)
        ticket.addTextChangedListener(object:TextWatcher{
            override fun beforeTextChanged(s:CharSequence?,start:Int,count:Int,after:Int){}
            override fun onTextChanged(s:CharSequence?,start:Int,before:Int,count:Int){if(::forgetButton.isInitialized)updateState()}
            override fun afterTextChanged(s:Editable?){}
        })
        forgetButton=button("Forget computer",ControlUI.Tone.DANGER){
            android.app.AlertDialog.Builder(this).setTitle(t("Forget computer")).setMessage(t("Remove the saved pairing from this phone? To revoke its server access too, use Revoke on the computer."))
                .setNegativeButton(t("Cancel"),null).setPositiveButton(t("Forget computer")){_,_->Vault.clear(this);NodeService.status=ui("Computer forgotten");acknowledge("Computer forgotten");updateState()}.show()
        };pairCard.addView(forgetButton);settings.addView(pairCard)
        settings.addView(text(installedCompanionVersion(this),15f,muted));settings.addView(text("Experimental companion",15f,muted))
        shell.addView(frame,LinearLayout.LayoutParams(-1,0,1f))
        val nav=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL;setPadding(dp(8),dp(4),dp(8),dp(4));setBackgroundColor(ControlUI.panel)}
        listOf("Home","Activity","Settings").forEachIndexed{index,label->
            val item=button(label){showPage(index)}.apply{tag=label;layoutParams=LinearLayout.LayoutParams(0,-2,1f).apply{marginStart=dp(3);marginEnd=dp(3)};setPadding(dp(5),dp(12),dp(5),dp(12))}
            navigation.add(item);nav.addView(item)
        }
        shell.addView(nav);setContentView(shell);showPage(selectedPage);updateState()
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
    override fun onSaveInstanceState(out:Bundle){out.putBoolean("scanner_pending",scannerPending);out.putInt("selected_page",selectedPage);super.onSaveInstanceState(out)}
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
            val computer=java.net.URL(pairing.url).authority
            val fingerprint=pairing.sha256.chunked(4).joinToString(" ")
            val spokenFingerprint=pairing.sha256.toList().joinToString(" ")
            val dialog=android.app.AlertDialog.Builder(this).setTitle(t("Pair your computer"))
                .setMessage(t("Computer: {0} · Identity: {1}",computer,"\n"+fingerprint))
                .setNegativeButton(t("Cancel"),null)
                .setPositiveButton(t("Pair and activate node")){_,_->
                    try{if(!NodeService.running){start(PairingCode.decode(obj.toString()).toString());ticket.text.clear()}}
                    catch(e:Exception){NodeService.status=ui(e.message ?: "Invalid invitation")}
                }.show()
            dialog.findViewById<TextView>(android.R.id.message)?.apply {
                textSize=16f
                contentDescription=t("Computer: {0} · Identity: {1}",computer,spokenFingerprint)
            }
        } catch(e:Exception){NodeService.status=ui(e.message ?: "Invalid invitation")}
    }
    private fun start(value: String?) {
        if(starting || NodeService.running)return
        showPage(0)
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
