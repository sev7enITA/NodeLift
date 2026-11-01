package dev.nodelift.companion

/** Navigation guidance never treats loaded weights as evidence of useful inference. */
enum class HomeAction(val label:String,val guidance:String,val enabled:Boolean=true) {
    PAIR("Scan QR","Start by pairing this phone with your computer."),
    RESUME("Resume session","Your pairing is saved. Resume to make this phone available."),
    CONNECTING("Connecting…","Waiting for the computer. You can pause the connection attempt.",false),
    LOADING("Loading model…","Keep this app open while the draft is prepared.",false),
    SETUP("Set up draft","The connection is active. Open Settings to prepare or enable the draft."),
    ASSESSING("Pause node","Your computer is assessing this phone. You can pause at any time."),
    PAUSE("Pause node","The draft is ready. Start a measured run from your computer."),
    BUSY("Please wait…","The current action is still in progress.",false);
    companion object {
        fun choose(saved:Boolean,running:Boolean,connected:Boolean,loading:Boolean,ready:Boolean,busy:Boolean,diagnosticRunning:Boolean=false):HomeAction = when {
            busy -> BUSY
            running && diagnosticRunning -> ASSESSING
            running && !connected -> CONNECTING
            !saved && !running -> PAIR
            !saved -> BUSY
            !running -> RESUME
            loading -> LOADING
            !ready -> SETUP
            else -> PAUSE
        }
    }
}
