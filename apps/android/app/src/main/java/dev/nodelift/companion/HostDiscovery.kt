package dev.nodelift.companion

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import android.net.wifi.WifiManager
import android.os.SystemClock
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

/** DNS-SD supplies hints only. The caller must perform pinned TLS before sending a token. */
class HostDiscovery(private val context: Context) {
    @Suppress("DEPRECATION")
    fun candidates(pairing: Pairing, cancelled: () -> Boolean): List<Pairing> {
        if(pairing.protocol!=2)return emptyList()
        val manager=context.getSystemService(NsdManager::class.java)
        val queue=ArrayBlockingQueue<Pairing>(8)
        val active=AtomicBoolean(true)
        val resolving=Semaphore(1)
        val candidates=linkedMapOf<String,Pairing>()
        val multicast=context.applicationContext.getSystemService(WifiManager::class.java)?.createMulticastLock("NodeLift-discovery")?.apply {setReferenceCounted(false)}
        val listener=object:NsdManager.DiscoveryListener {
            override fun onDiscoveryStarted(type:String) {}
            override fun onDiscoveryStopped(type:String) {}
            override fun onStartDiscoveryFailed(type:String,code:Int) {active.set(false)}
            override fun onStopDiscoveryFailed(type:String,code:Int) {}
            override fun onServiceLost(info:NsdServiceInfo) {}
            override fun onServiceFound(info:NsdServiceInfo) {
                if(!active.get() || !info.serviceName.startsWith("NodeLift-"+pairing.sha256.take(12)) || !resolving.tryAcquire())return
                try {manager.resolveService(info,object:NsdManager.ResolveListener {
                    override fun onResolveFailed(service:NsdServiceInfo,code:Int) {resolving.release()}
                    override fun onServiceResolved(service:NsdServiceInfo) {
                        try {
                            fun attr(key:String)=service.attributes[key]?.toString(Charsets.UTF_8)
                            if(!active.get() || attr("protocol")!="2" || attr("id")!=pairing.sha256)return
                            val address=attr("address") ?: return
                            val port=attr("port")?.toIntOrNull() ?: return
                            // Re-run literal-address and port validation. Never accept new trust material from DNS.
                            val candidate=Pairing.parse(pairing.json().put("url","https://$address:$port"))
                            queue.offer(candidate)
                        } catch(_:Exception) {} finally {resolving.release()}
                    }
                })}catch(_:Exception){resolving.release()}
            }
        }
        try {
            multicast?.acquire()
            manager.discoverServices("_nodelift._tcp.",NsdManager.PROTOCOL_DNS_SD,listener)
            val deadline=SystemClock.elapsedRealtime()+8000
            while(active.get() && !cancelled() && SystemClock.elapsedRealtime()<deadline && candidates.size<3) {
                queue.poll(200,TimeUnit.MILLISECONDS)?.let { candidates[it.url]=it }
                if(candidates.isNotEmpty())break
            }
        } finally {
            active.set(false)
            try {manager.stopServiceDiscovery(listener)}catch(_:Exception){}
            if(multicast?.isHeld==true)multicast.release()
        }
        return candidates.values.toList()
    }
}
