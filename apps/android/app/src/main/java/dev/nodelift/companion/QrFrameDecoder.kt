package dev.nodelift.companion

import com.google.zxing.*
import com.google.zxing.common.HybridBinarizer
import java.nio.ByteBuffer

/** Copies the Y plane with its actual row/pixel strides; no frame leaves this process. */
object QrFrameDecoder {
    fun luma(buffer:ByteBuffer,width:Int,height:Int,rowStride:Int,pixelStride:Int):ByteArray {
        require(width>0 && height>0 && width.toLong()*height<=4_194_304 && pixelStride>0)
        require(rowStride.toLong()>=(width-1L)*pixelStride+1)
        val source=buffer.duplicate();val base=source.position()
        val required=(height-1L)*rowStride+(width-1L)*pixelStride+1
        require(required<=source.remaining())
        val result=ByteArray(width*height)
        for(y in 0 until height) {
            val offset=base+y*rowStride
            if(pixelStride==1){source.position(offset);source.get(result,y*width,width)}
            else for(x in 0 until width)result[y*width+x]=source.get(offset+x*pixelStride)
        }
        return result
    }
    fun decode(bytes:ByteArray,width:Int,height:Int):String? {
        val source=PlanarYUVLuminanceSource(bytes,width,height,0,0,width,height,false)
        val reader=MultiFormatReader()
        return try {
            val result=reader.decode(BinaryBitmap(HybridBinarizer(source)),mapOf(DecodeHintType.POSSIBLE_FORMATS to listOf(BarcodeFormat.QR_CODE),DecodeHintType.TRY_HARDER to true))
            result.text.takeIf { it.length<=8192 }
        } catch(_:ReaderException){null} finally {reader.reset()}
    }
}
