import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers
let edge = 1024
let context = CGContext(data: nil, width: edge, height: edge, bitsPerComponent: 8, bytesPerRow: edge * 4, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
context.setFillColor(CGColor(red: 9/255, green: 18/255, blue: 22/255, alpha: 1))
context.fill(CGRect(x: 0, y: 0, width: edge, height: edge))
context.translateBy(x: 102.4, y: 921.6)
context.scaleBy(x: 12.8, y: -12.8)
let aqua=CGColor(red:160/255,green:1,blue:241/255,alpha:1)
let white=CGColor(red:233/255,green:249/255,blue:252/255,alpha:1)
context.setStrokeColor(aqua);context.setLineWidth(8);context.setLineCap(.square);context.setLineJoin(.bevel)
context.move(to: CGPoint(x:15,y:48));context.addLine(to:CGPoint(x:15,y:17));context.addLine(to:CGPoint(x:49,y:47));context.addLine(to:CGPoint(x:49,y:16));context.strokePath()
context.setStrokeColor(white);context.setLineWidth(2);context.setLineCap(.butt)
context.move(to:CGPoint(x:5,y:40));context.addCurve(to:CGPoint(x:59,y:26),control1:CGPoint(x:12,y:53),control2:CGPoint(x:52,y:43));context.strokePath()
context.setFillColor(white);context.fillEllipse(in:CGRect(x:5,y:39,width:6,height:6))
context.setFillColor(aqua);context.fillEllipse(in:CGRect(x:52,y:28,width:6,height:6))
let target=URL(fileURLWithPath:CommandLine.arguments[1])
let destination = CGImageDestinationCreateWithURL(target as CFURL, UTType.png.identifier as CFString, 1, nil)!
CGImageDestinationAddImage(destination, context.makeImage()!, nil)
precondition(CGImageDestinationFinalize(destination))
