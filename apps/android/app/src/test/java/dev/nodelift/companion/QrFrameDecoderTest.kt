package dev.nodelift.companion

import com.google.zxing.BarcodeFormat
import com.google.zxing.EncodeHintType
import com.google.zxing.qrcode.QRCodeWriter
import org.junit.Assert.*
import org.junit.Test
import java.nio.ByteBuffer

class QrFrameDecoderTest {
    @Test fun paddedRowsAndBufferPositionAreRespected() {
        val source=ByteBuffer.wrap(byteArrayOf(99,99,1,2,3,88,88,4,5,6))
        source.position(2)
        assertArrayEquals(byteArrayOf(1,2,3,4,5,6),QrFrameDecoder.luma(source,3,2,5,1))
        assertEquals(2,source.position())
    }
    @Test fun pixelStrideIsRespected() {
        assertArrayEquals(byteArrayOf(1,2,3,4),QrFrameDecoder.luma(ByteBuffer.wrap(byteArrayOf(1,99,2,99,3,99,4)),2,2,4,2))
    }
    @Test fun denseInvitationSurvivesQuarterTurnsAndPaddedCameraPlanes() {
        val code="nodelift://pair/v1/192.168.1.2:9867/1999999999/"+"A".repeat(32)+"/"+"b".repeat(1030)
        val matrix=QRCodeWriter().encode(code,BarcodeFormat.QR_CODE,768,768,mapOf(EncodeHintType.MARGIN to 4))
        val size=matrix.width
        var pixels=ByteArray(size*size){i->if(matrix[i%size,i/size])0 else 255.toByte()}
        repeat(4) {
            val stride=size+17;val padded=ByteArray(stride*size)
            for(row in 0 until size)pixels.copyInto(padded,row*stride,row*size,(row+1)*size)
            assertEquals(code,QrFrameDecoder.decode(QrFrameDecoder.luma(ByteBuffer.wrap(padded),size,size,stride,1),size,size))
            val rotated=ByteArray(pixels.size)
            for(y in 0 until size)for(x in 0 until size)rotated[x*size+(size-y-1)]=pixels[y*size+x]
            pixels=rotated
        }
    }
    @Test fun emptyFrameIsNotAnError() {assertNull(QrFrameDecoder.decode(ByteArray(64*64){255.toByte()},64,64))}
    @Test(expected=IllegalArgumentException::class) fun truncatedCameraBufferIsRejected() {QrFrameDecoder.luma(ByteBuffer.allocate(8),4,3,4,1)}
    @Test(expected=IllegalArgumentException::class) fun oversizedAllocationIsRejected() {QrFrameDecoder.luma(ByteBuffer.allocate(8),Int.MAX_VALUE,Int.MAX_VALUE,Int.MAX_VALUE,1)}
}
