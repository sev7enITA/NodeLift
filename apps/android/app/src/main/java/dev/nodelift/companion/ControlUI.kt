package dev.nodelift.companion

import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.RippleDrawable
import android.graphics.drawable.StateListDrawable
import android.view.View
import android.widget.Button

/** Shared native controls: state is conveyed by fill, outline, text and accessibility. */
object ControlUI {
    val canvas = Color.rgb(11,21,28)
    val panel = Color.rgb(19,35,45)
    val mint = Color.rgb(145,243,206)
    val ink = Color.rgb(237,245,248)
    val muted = Color.rgb(158,177,189)
    val amber = Color.rgb(255,207,133)
    val red = Color.rgb(255,169,169)
    enum class Tone { PRIMARY, SECONDARY, DANGER }
    fun dp(context:Context, value:Int) = (value*context.resources.displayMetrics.density).toInt()
    private fun box(context:Context, fill:Int, border:Int) = GradientDrawable().apply {
        setColor(fill);cornerRadius=dp(context,12).toFloat();setStroke(dp(context,1),border)
    }
    fun style(button:Button, tone:Tone=Tone.SECONDARY) {
        val context=button.context
        val accent=if(tone==Tone.DANGER)red else mint
        val primary=tone==Tone.PRIMARY
        val states=StateListDrawable().apply {
            addState(intArrayOf(-android.R.attr.state_enabled),box(context,Color.rgb(26,39,48),Color.rgb(60,77,89)))
            addState(intArrayOf(android.R.attr.state_pressed),box(context,Color.rgb(62,113,109),accent))
            addState(intArrayOf(android.R.attr.state_selected),box(context,Color.rgb(29,69,65),accent))
            addState(intArrayOf(android.R.attr.state_focused),box(context,if(primary)mint else panel,ink))
            addState(intArrayOf(),box(context,if(primary)mint else panel,if(primary)mint else Color.rgb(66,104,113)))
        }
        button.backgroundTintList=null
        button.background=RippleDrawable(ColorStateList.valueOf(Color.argb(80,237,245,248)),states,box(context,Color.WHITE,Color.WHITE))
        button.setTextColor(ColorStateList(arrayOf(intArrayOf(-android.R.attr.state_enabled),intArrayOf(android.R.attr.state_pressed),intArrayOf(android.R.attr.state_selected),intArrayOf()),intArrayOf(muted,ink,accent,if(primary)canvas else accent)))
        button.isAllCaps=false;button.minHeight=dp(context,52);button.minimumHeight=dp(context,52)
        button.setPadding(dp(context,14),dp(context,12),dp(context,14),dp(context,12))
        button.setTypeface(null,Typeface.BOLD);button.textSize=16f
    }
    fun describe(view:View, text:String) {
        if(android.os.Build.VERSION.SDK_INT>=30){if(view.stateDescription?.toString()!=text)view.stateDescription=text}
        else if(view.contentDescription?.toString()!=text)view.contentDescription=text
    }
}
