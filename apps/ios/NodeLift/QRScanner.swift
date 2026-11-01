import SwiftUI
import AVFoundation

/// Camera frames are decoded on-device and are never persisted or uploaded.
struct QRScanner: UIViewControllerRepresentable {
    let language: String
    let onCode: (String) -> Void
    let onError: (String) -> Void
    func makeUIViewController(context: Context) -> CameraController {
        let controller = CameraController()
        controller.onCode = onCode; controller.onError = onError
        return controller
    }
    func updateUIViewController(_ controller: CameraController, context: Context) {}

    final class CameraController: UIViewController, AVCaptureMetadataOutputObjectsDelegate {
        var onCode: ((String) -> Void)?
        var onError: ((String) -> Void)?
        private let session = AVCaptureSession()
        private let queue = DispatchQueue(label: "dev.nodelift.qr-camera")
        private var preview: AVCaptureVideoPreviewLayer?
        private var closed = false // Accessed exclusively on queue.
        private var delivered = false // Metadata callbacks run on main.
        override func viewDidLoad() {
            super.viewDidLoad(); view.backgroundColor = .black
            switch AVCaptureDevice.authorizationStatus(for: .video) {
            case .authorized: configure()
            case .notDetermined:
                AVCaptureDevice.requestAccess(for: .video) { [weak self] allowed in
                    DispatchQueue.main.async { if allowed { self?.configure() } else { self?.fail("Camera access is required to scan. Enable it in Settings or use manual pairing.") } }
                }
            default: fail("Camera access is required to scan. Enable it in Settings or use manual pairing.")
            }
        }
        private func fail(_ message: String) { guard !delivered else { return }; delivered = true; onError?(message) }
        private func configure() {
            queue.async { [weak self] in
                guard let self, !closed else { return }
                guard let camera = AVCaptureDevice.default(for: .video), let input = try? AVCaptureDeviceInput(device: camera) else {
                    DispatchQueue.main.async { self.fail("Camera unavailable. Use manual pairing.") }; return
                }
                let output = AVCaptureMetadataOutput()
                session.beginConfiguration()
                guard session.canAddInput(input), session.canAddOutput(output) else {
                    session.commitConfiguration(); DispatchQueue.main.async { self.fail("Camera unavailable. Use manual pairing.") }; return
                }
                session.addInput(input); session.addOutput(output)
                output.setMetadataObjectsDelegate(self, queue: .main)
                guard output.availableMetadataObjectTypes.contains(.qr) else {
                    session.commitConfiguration(); DispatchQueue.main.async { self.fail("Camera unavailable. Use manual pairing.") }; return
                }
                output.metadataObjectTypes = [.qr]; session.commitConfiguration()
                DispatchQueue.main.async {
                    guard !self.delivered else { return }
                    let layer = AVCaptureVideoPreviewLayer(session: self.session)
                    layer.videoGravity = .resizeAspectFill; self.view.layer.addSublayer(layer); self.preview = layer; self.view.setNeedsLayout()
                }
                session.startRunning()
            }
        }
        override func viewDidLayoutSubviews() {
            super.viewDidLayoutSubviews(); preview?.frame = view.bounds
            let angle: CGFloat
            switch view.window?.windowScene?.interfaceOrientation {
            case .landscapeLeft: angle = 0
            case .landscapeRight: angle = 180
            case .portraitUpsideDown: angle = 270
            default: angle = 90
            }
            if let connection = preview?.connection, connection.isVideoRotationAngleSupported(angle) { connection.videoRotationAngle = angle }
        }
        override func viewDidDisappear(_ animated: Bool) {
            super.viewDidDisappear(animated); delivered = true
            queue.async { [self] in closed = true; session.stopRunning() }
        }
        func metadataOutput(_ output: AVCaptureMetadataOutput, didOutput objects: [AVMetadataObject], from connection: AVCaptureConnection) {
            guard !delivered, let value = (objects.first as? AVMetadataMachineReadableCodeObject)?.stringValue else { return }
            delivered = true; onCode?(value)
        }
    }
}
