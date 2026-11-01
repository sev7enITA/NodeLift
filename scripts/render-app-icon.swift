import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

// Build assets from the approved showcase artwork, without redrawing the logo.
// Run from the repository root: swift scripts/render-app-icon.swift
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let sourceURL = root.appendingPathComponent("assets/brand/nodelift-emblem.png")
guard let source = CGImageSourceCreateWithURL(sourceURL as CFURL, nil),
      let emblem = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
    fatalError("Cannot read the canonical NodeLift emblem")
}

func render(_ path: String, edge: Int, inset: Double, opaque: Bool) throws {
    let alpha = opaque ? CGImageAlphaInfo.noneSkipLast : CGImageAlphaInfo.premultipliedLast
    guard let context = CGContext(data: nil, width: edge, height: edge,
                                  bitsPerComponent: 8, bytesPerRow: edge * 4,
                                  space: CGColorSpace(name: CGColorSpace.sRGB)!,
                                  bitmapInfo: alpha.rawValue) else { fatalError("Cannot allocate icon") }
    let size = Double(edge)
    if opaque {
        context.setFillColor(CGColor(red: 9.0/255, green: 18.0/255, blue: 22.0/255, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: size, height: size))
    }
    let available = size * (1 - 2 * inset)
    let scale = available / Double(max(emblem.width, emblem.height))
    let width = Double(emblem.width) * scale, height = Double(emblem.height) * scale
    context.interpolationQuality = .high
    context.draw(emblem, in: CGRect(x: (size-width)/2, y: (size-height)/2, width: width, height: height))
    let target = root.appendingPathComponent(path)
    try FileManager.default.createDirectory(at: target.deletingLastPathComponent(), withIntermediateDirectories: true)
    guard let destination = CGImageDestinationCreateWithURL(target as CFURL, UTType.png.identifier as CFString, 1, nil),
          let result = context.makeImage() else { fatalError("Cannot encode icon") }
    CGImageDestinationAddImage(destination, result, nil)
    precondition(CGImageDestinationFinalize(destination), "Cannot write icon")
    print(path)
}

try render("apps/ios/NodeLift/Assets.xcassets/AppIcon.appiconset/NodeLift-1024.png", edge: 1024, inset: 0.02, opaque: true)
try render("apps/ios/NodeLift/Assets.xcassets/NodeLiftEmblem.imageset/emblem.png", edge: 512, inset: 0, opaque: false)
try render("apps/android/app/src/main/res/drawable-nodpi/nodelift_emblem.png", edge: 512, inset: 0, opaque: false)
// Reserve one sixth on each side of the 108 dp layer for launcher masks/motion.
try render("apps/android/app/src/main/res/drawable-nodpi/nodelift_launcher_foreground.png", edge: 432, inset: 1.0/6, opaque: false)
try render("apps/android/app/src/main/res/drawable-nodpi/nodelift_launcher_legacy.png", edge: 512, inset: 0.02, opaque: true)
try render("apps/harmony/AppScope/resources/base/media/app_icon.png", edge: 512, inset: 0.02, opaque: true)
try render("apps/harmony/entry/src/main/resources/base/media/nodelift_emblem.png", edge: 512, inset: 0, opaque: false)
