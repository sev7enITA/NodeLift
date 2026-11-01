package dev.nodelift.companion

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.util.Size
import android.view.View
import android.view.WindowManager
import android.widget.*
import androidx.camera.core.*
import androidx.camera.core.resolutionselector.ResolutionSelector
import androidx.camera.core.resolutionselector.ResolutionStrategy
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

/** Lifecycle-bound CameraX scanner. No legacy CaptureActivity, battery receiver or orientation lock. */
class QRScannerActivity:Activity(),LifecycleOwner {
    companion object { const val REQUEST=731;const val RESULT_CODE="pairing_code";const val RESULT_ERROR="scanner_error" }
    private val registry=LifecycleRegistry(this)
    override fun getLifecycle():Lifecycle = registry
    private val executor=Executors.newSingleThreadExecutor()
    private val handler=Handler(Looper.getMainLooper())
    private val delivered=AtomicBoolean(false)
    private var attempt=0
    private var provider:ProcessCameraProvider?=null
    private var analysis:ImageAnalysis?=null
    private var previewUseCase:Preview?=null
    private var timeout:Runnable?=null
    private lateinit var preview:PreviewView
    private lateinit var message:TextView
    private lateinit var retry:Button
    private var streaming=false
    private var lastFrame=0L
    private fun t(key:String)=L10n.text(this,key)
    private fun dp(value:Int)=ControlUI.dp(this,value)
    override fun onCreate(savedInstanceState:Bundle?) {
        super.onCreate(savedInstanceState);registry.handleLifecycleEvent(Lifecycle.Event.ON_CREATE)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        val root=LinearLayout(this).apply {orientation=LinearLayout.VERTICAL;setBackgroundColor(ControlUI.canvas);setPadding(dp(20),dp(16),dp(20),dp(20))}
        root.setOnApplyWindowInsetsListener {view,insets->view.setPadding(dp(20)+insets.systemWindowInsetLeft,dp(16)+insets.systemWindowInsetTop,dp(20)+insets.systemWindowInsetRight,dp(20)+insets.systemWindowInsetBottom);insets}
        root.addView(TextView(this).apply{text=t("Scan QR");textSize=24f;setTextColor(ControlUI.ink);setPadding(0,0,0,dp(14))})
        message=TextView(this).apply {textSize=16f;setTextColor(ControlUI.mint);minHeight=dp(64);accessibilityLiveRegion=View.ACCESSIBILITY_LIVE_REGION_POLITE};root.addView(message)
        preview=PreviewView(this).apply {implementationMode=PreviewView.ImplementationMode.COMPATIBLE;scaleType=PreviewView.ScaleType.FIT_CENTER;contentDescription=t("Camera preview")}
        root.addView(preview,LinearLayout.LayoutParams(-1,0,1f))
        root.addView(TextView(this).apply{text=t("Fit the entire QR code in the preview. Scanning stays on this device.");textSize=14f;setTextColor(ControlUI.muted);setPadding(0,dp(14),0,dp(14))})
        retry=Button(this).apply {text=t("Retry camera");ControlUI.style(this);visibility=View.GONE;setOnClickListener{startCamera()}};root.addView(retry)
        root.addView(Button(this).apply{text=t("Cancel");ControlUI.style(this);setOnClickListener{finish()}})
        setContentView(root)
        preview.previewStreamState.observe(this){state->
            if(!delivered.get() && retry.visibility!=View.VISIBLE) {
                streaming=state==PreviewView.StreamState.STREAMING
                if(streaming){Diagnostics.record(DiagnosticEvent.CAMERA_READY);cancelTimeout();message.text=t("Point the camera at the QR code on your computer.")}
                else if(registry.currentState.isAtLeast(Lifecycle.State.STARTED)) {
                    message.text=t("Opening camera…")
                    if(timeout==null)scheduleTimeout(attempt)
                }
            }
        }
        if(checkSelfPermission(Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED) {
            setResult(RESULT_CANCELED,Intent().putExtra(RESULT_ERROR,"Camera access is required to scan. Enable it in Settings or use manual pairing."));finish()
        } else startCamera()
    }
    private fun startCamera() {
        Diagnostics.record(DiagnosticEvent.CAMERA_OPEN)
        val current=++attempt
        streaming=false;retry.visibility=View.GONE;message.text=t("Opening camera…")
        scheduleTimeout(current)
        if(!packageManager.hasSystemFeature(PackageManager.FEATURE_CAMERA_ANY)){fail(current);return}
        try {
            val future=ProcessCameraProvider.getInstance(this)
            future.addListener({
                if(isFinishing || isDestroyed || current!=attempt)return@addListener
                try {
                    val cameras=future.get();unbindOwned();provider=cameras
                    val selector=when {
                        cameras.hasCamera(CameraSelector.DEFAULT_BACK_CAMERA)->CameraSelector.DEFAULT_BACK_CAMERA
                        cameras.hasCamera(CameraSelector.DEFAULT_FRONT_CAMERA)->CameraSelector.DEFAULT_FRONT_CAMERA
                        else->throw IllegalStateException("No camera")
                    }
                    val view=Preview.Builder().build().also{it.setSurfaceProvider(preview.surfaceProvider)}
                    previewUseCase=view
                    val reader=ImageAnalysis.Builder().setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                        .setResolutionSelector(ResolutionSelector.Builder().setResolutionStrategy(ResolutionStrategy(Size(1280,960),ResolutionStrategy.FALLBACK_RULE_CLOSEST_LOWER_THEN_HIGHER))
                            .setResolutionFilter{sizes,_->sizes.filter{it.width.toLong()*it.height<=4_194_304}}.build()).build()
                    analysis=reader
                    reader.setAnalyzer(executor){image->
                        try {
                            val now=SystemClock.elapsedRealtime()
                            if(!delivered.get() && now-lastFrame>=125) {
                                lastFrame=now
                                val plane=image.planes[0]
                                val bytes=QrFrameDecoder.luma(plane.buffer,image.width,image.height,plane.rowStride,plane.pixelStride)
                                val code=QrFrameDecoder.decode(bytes,image.width,image.height)
                                if(code!=null)handler.post {
                                    if(current==attempt && !isFinishing && registry.currentState.isAtLeast(Lifecycle.State.STARTED) && delivered.compareAndSet(false,true)) {
                                        Diagnostics.record(DiagnosticEvent.CAMERA_RESULT);setResult(RESULT_OK,Intent().putExtra(RESULT_CODE,code));finish()
                                    }
                                }
                            }
                        } catch(error:Exception){handler.post{fail(current,error)}} finally {image.close()}
                    }
                    // Let CameraX recover transient camera ownership errors. The foreground
                    // watchdog bounds startup without consuming sticky errors from an old bind.
                    cameras.bindToLifecycle(this,selector,view,reader)
                } catch(error:Exception){fail(current,error)}
            },androidx.core.content.ContextCompat.getMainExecutor(this))
        } catch(error:Exception){fail(current,error)}
    }
    private fun cancelTimeout(){timeout?.let{handler.removeCallbacks(it)};timeout=null}
    private fun scheduleTimeout(current:Int) {
        cancelTimeout()
        timeout=Runnable {
            timeout=null
            if(current==attempt && !streaming && !isFinishing && registry.currentState.isAtLeast(Lifecycle.State.STARTED))fail(current)
        }.also{handler.postDelayed(it,12000)}
    }
    private fun unbindOwned() {
        analysis?.clearAnalyzer()
        val owned=listOfNotNull<UseCase>(previewUseCase,analysis).toTypedArray()
        try{if(owned.isNotEmpty())provider?.unbind(*owned)}catch(_:Exception){}
        analysis=null;previewUseCase=null
    }
    private fun fail(current:Int,error:Throwable?=null) {
        if(current!=attempt || isFinishing || isDestroyed || delivered.get())return
        Diagnostics.record(DiagnosticEvent.CAMERA_FAILED,error)
        attempt++ // Ignore late results/errors from this attempt.
        retry.visibility=View.VISIBLE;cancelTimeout();unbindOwned()
        message.text=t("Camera unavailable. Retry or return to manual pairing.")
    }
    override fun onStart(){super.onStart();registry.handleLifecycleEvent(Lifecycle.Event.ON_START);if(::retry.isInitialized && retry.visibility!=View.VISIBLE && !streaming)scheduleTimeout(attempt)}
    override fun onResume(){super.onResume();registry.handleLifecycleEvent(Lifecycle.Event.ON_RESUME)}
    override fun onPause(){registry.handleLifecycleEvent(Lifecycle.Event.ON_PAUSE);super.onPause()}
    override fun onStop(){cancelTimeout();streaming=false;registry.handleLifecycleEvent(Lifecycle.Event.ON_STOP);super.onStop()}
    override fun onDestroy(){attempt++;delivered.set(true);cancelTimeout();handler.removeCallbacksAndMessages(null);unbindOwned();registry.handleLifecycleEvent(Lifecycle.Event.ON_DESTROY);executor.shutdown();super.onDestroy()}
}
