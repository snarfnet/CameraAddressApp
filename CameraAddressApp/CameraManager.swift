import AVFoundation
import UIKit
import Photos

class CameraManager: NSObject, ObservableObject {
    let session = AVCaptureSession()
    private let output = AVCapturePhotoOutput()
    private var completion: ((UIImage?) -> Void)?

    @Published var lastPhoto: UIImage?
    @Published var isCaptured = false

    override init() {
        super.init()
        setupSession()
    }

    private func setupSession() {
        session.beginConfiguration()
        session.sessionPreset = .photo

        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
              let input = try? AVCaptureDeviceInput(device: device) else {
            session.commitConfiguration()
            return
        }

        if session.canAddInput(input) { session.addInput(input) }
        if session.canAddOutput(output) { session.addOutput(output) }

        session.commitConfiguration()
    }

    func start() {
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            self?.session.startRunning()
        }
    }

    func stop() {
        session.stopRunning()
    }

    func capture(completion: @escaping (UIImage?) -> Void) {
        self.completion = completion
        let settings = AVCapturePhotoSettings()
        output.capturePhoto(with: settings, delegate: self)
    }
}

extension CameraManager: AVCapturePhotoCaptureDelegate {
    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        guard let data = photo.fileDataRepresentation(),
              let image = UIImage(data: data) else {
            completion?(nil)
            return
        }
        completion?(image)
    }
}

// Save image with overlay text
extension CameraManager {
    static func saveWithOverlay(image: UIImage, address: String, landmark: String, postalCode: String) {
        let size = image.size
        let renderer = UIGraphicsImageRenderer(size: size)
        let result = renderer.image { ctx in
            image.draw(at: .zero)

            let scale = size.width / 390.0
            let padding = 16.0 * scale
            let fontSize = 18.0 * scale
            let smallFontSize = 14.0 * scale

            let shadow = NSShadow()
            shadow.shadowColor = UIColor.black.withAlphaComponent(0.8)
            shadow.shadowBlurRadius = 4 * scale
            shadow.shadowOffset = CGSize(width: 1 * scale, height: 1 * scale)

            let mainAttrs: [NSAttributedString.Key: Any] = [
                .font: UIFont.boldSystemFont(ofSize: fontSize),
                .foregroundColor: UIColor.white,
                .shadow: shadow
            ]
            let smallAttrs: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: smallFontSize),
                .foregroundColor: UIColor.white.withAlphaComponent(0.9),
                .shadow: shadow
            ]

            var y = size.height - padding

            // Landmark
            if !landmark.isEmpty {
                let landmarkStr = NSString(string: landmark)
                let landmarkSize = landmarkStr.size(withAttributes: mainAttrs)
                y -= landmarkSize.height
                landmarkStr.draw(at: CGPoint(x: padding, y: y), withAttributes: mainAttrs)
                y -= 4 * scale
            }

            // Address
            let addrStr = NSString(string: address)
            let addrSize = addrStr.size(withAttributes: mainAttrs)
            y -= addrSize.height
            addrStr.draw(at: CGPoint(x: padding, y: y), withAttributes: mainAttrs)

            // Postal code
            if !postalCode.isEmpty {
                y -= 4 * scale
                let pcStr = NSString(string: "〒\(postalCode)")
                let pcSize = pcStr.size(withAttributes: smallAttrs)
                y -= pcSize.height
                pcStr.draw(at: CGPoint(x: padding, y: y), withAttributes: smallAttrs)
            }
        }

        PHPhotoLibrary.requestAuthorization(for: .addOnly) { status in
            guard status == .authorized || status == .limited else { return }
            PHPhotoLibrary.shared().performChanges {
                PHAssetCreationRequest.forAsset().addResource(with: .photo,
                    data: result.jpegData(compressionQuality: 0.9)!, options: nil)
            }
        }
    }
}
