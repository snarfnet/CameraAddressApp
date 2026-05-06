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
            let outerPadding = 18.0 * scale
            let innerPadding = 14.0 * scale
            let cardWidth = size.width - outerPadding * 2
            let titleFontSize = 12.0 * scale
            let addressFontSize = 18.0 * scale
            let metaFontSize = 13.0 * scale
            let lineGap = 7.0 * scale

            let titleAttrs: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: titleFontSize, weight: .black),
                .foregroundColor: UIColor(red: 0.42, green: 0.91, blue: 0.98, alpha: 1)
            ]
            let addressAttrs: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: addressFontSize, weight: .heavy),
                .foregroundColor: UIColor.white
            ]
            let metaAttrs: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: metaFontSize, weight: .bold),
                .foregroundColor: UIColor.white.withAlphaComponent(0.84)
            ]
            let landmarkAttrs: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: metaFontSize, weight: .bold),
                .foregroundColor: UIColor(red: 0.99, green: 0.9, blue: 0.54, alpha: 1)
            ]

            let addressText = address.isEmpty ? "住所を取得できませんでした" : address
            let maxTextWidth = cardWidth - innerPadding * 2
            let addressRect = NSString(string: addressText).boundingRect(
                with: CGSize(width: maxTextWidth, height: .greatestFiniteMagnitude),
                options: [.usesLineFragmentOrigin, .usesFontLeading],
                attributes: addressAttrs,
                context: nil
            )
            let landmarkHeight = landmark.isEmpty ? 0 : 20.0 * scale
            let metaHeight = postalCode.isEmpty ? 0 : 18.0 * scale
            let cardHeight = innerPadding * 2 + 16.0 * scale + lineGap + ceil(addressRect.height) + landmarkHeight + metaHeight + lineGap * 2
            let cardRect = CGRect(
                x: outerPadding,
                y: size.height - outerPadding - cardHeight,
                width: cardWidth,
                height: cardHeight
            )

            let path = UIBezierPath(roundedRect: cardRect, cornerRadius: 22.0 * scale)
            UIColor.black.withAlphaComponent(0.58).setFill()
            path.fill()
            UIColor.white.withAlphaComponent(0.18).setStroke()
            path.lineWidth = 1.0 * scale
            path.stroke()

            var y = cardRect.minY + innerPadding
            NSString(string: "ADDRESS STAMP").draw(
                at: CGPoint(x: cardRect.minX + innerPadding, y: y),
                withAttributes: titleAttrs
            )

            if !postalCode.isEmpty {
                let postal = NSString(string: "〒\(postalCode)")
                let postalSize = postal.size(withAttributes: metaAttrs)
                postal.draw(
                    at: CGPoint(x: cardRect.maxX - innerPadding - postalSize.width, y: y),
                    withAttributes: metaAttrs
                )
            }

            y += 16.0 * scale + lineGap
            NSString(string: addressText).draw(
                with: CGRect(x: cardRect.minX + innerPadding, y: y, width: maxTextWidth, height: ceil(addressRect.height)),
                options: [.usesLineFragmentOrigin, .usesFontLeading],
                attributes: addressAttrs,
                context: nil
            )
            y += ceil(addressRect.height) + lineGap

            if !landmark.isEmpty {
                NSString(string: landmark).draw(
                    at: CGPoint(x: cardRect.minX + innerPadding, y: y),
                    withAttributes: landmarkAttrs
                )
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
