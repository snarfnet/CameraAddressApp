import SwiftUI
import UIKit

struct ContentView: View {
    @StateObject private var camera = CameraManager()
    @StateObject private var location = LocationManager()
    @State private var showFlash = false
    @State private var showSaved = false
    @State private var showLastPhoto = false
    @State private var shutterPressed = false

    private var isScreenshotMode: Bool {
        ProcessInfo.processInfo.arguments.contains("-SCREENSHOT_MODE")
    }

    var body: some View {
        ZStack {
            cameraSurface

            ViewfinderOverlay()
                .allowsHitTesting(false)

            VStack(spacing: 0) {
                topHud
                    .padding(.horizontal, 18)
                    .padding(.top, 12)

                Spacer()

                AddressPlate(
                    postalCode: displayPostalCode,
                    address: displayAddress,
                    landmark: displayLandmark,
                    landmarkIcon: landmarkIcon
                )
                .padding(.horizontal, 16)
                .padding(.bottom, 14)

                captureDock
                    .padding(.horizontal, 18)
                    .padding(.bottom, 10)

                BannerAdView(adUnitID: "ca-app-pub-9404799280370656/7882448349")
                    .frame(height: 50)
                    .background(Color.black)
            }

            if showFlash {
                Color.white
                    .ignoresSafeArea()
                    .transition(.opacity)
            }

            if showSaved {
                SavedToast()
                    .transition(.move(edge: .top).combined(with: .opacity))
            }
        }
        .background(Color.black)
        .onAppear {
            if !isScreenshotMode {
                camera.start()
            }
        }
        .fullScreenCover(isPresented: $showLastPhoto) {
            if let photo = camera.lastPhoto {
                PhotoPreviewView(image: photo) {
                    showLastPhoto = false
                }
            }
        }
    }

    @ViewBuilder
    private var cameraSurface: some View {
        if isScreenshotMode {
            Image("DemoStreet")
                .resizable()
                .scaledToFill()
                .ignoresSafeArea()
        } else {
            CameraPreview(session: camera.session)
                .ignoresSafeArea()
        }
    }

    private var topHud: some View {
        HStack(spacing: 10) {
            HudPill(icon: "location.fill", title: displayAddress.isEmpty ? "住所取得中" : "GPS住所", subtitle: displayPostalCode.isEmpty ? "測位中" : "〒\(displayPostalCode)", tint: Color(hex: "38BDF8"))

            Spacer()

            HudIconButton(systemName: "scope", tint: Color(hex: "A7F3D0"))
        }
    }

    private var captureDock: some View {
        HStack(spacing: 18) {
            Button {
                if camera.lastPhoto != nil {
                    showLastPhoto = true
                }
            } label: {
                ThumbnailView(photo: camera.lastPhoto)
            }
            .buttonStyle(.plain)
            .disabled(camera.lastPhoto == nil)
            .accessibilityLabel("最後に撮影した写真を開く")

            Spacer()

            Button {
                takePhoto()
            } label: {
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [Color.white, Color(hex: "DFF7FF")],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 82, height: 82)
                        .shadow(color: Color(hex: "38BDF8").opacity(0.45), radius: 18, y: 8)

                    Circle()
                        .stroke(Color.white.opacity(0.95), lineWidth: 4)
                        .frame(width: 94, height: 94)

                    Circle()
                        .fill(Color(hex: "0F172A"))
                        .frame(width: shutterPressed ? 38 : 44, height: shutterPressed ? 38 : 44)
                        .overlay(
                            Image(systemName: "camera.fill")
                                .font(.system(size: 18, weight: .bold))
                                .foregroundStyle(.white)
                        )
                }
                .scaleEffect(shutterPressed ? 0.92 : 1)
                .animation(.spring(response: 0.25, dampingFraction: 0.65), value: shutterPressed)
            }
            .accessibilityLabel("住所付き写真を撮影")

            Spacer()

            VStack(spacing: 5) {
                Image(systemName: "text.viewfinder")
                    .font(.system(size: 21, weight: .bold))
                Text("焼き込み")
                    .font(.caption2.weight(.bold))
            }
            .foregroundStyle(.white.opacity(0.9))
            .frame(width: 62, height: 62)
            .background(.black.opacity(0.34), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(.white.opacity(0.18), lineWidth: 1)
            )
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 14)
        .background(.black.opacity(0.42), in: RoundedRectangle(cornerRadius: 30, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 30, style: .continuous)
                .stroke(.white.opacity(0.16), lineWidth: 1)
        )
    }

    private var displayPostalCode: String {
        isScreenshotMode ? "150-0042" : location.postalCode
    }

    private var displayAddress: String {
        isScreenshotMode ? "東京都渋谷区宇田川町21-6" : location.address
    }

    private var displayLandmark: String {
        isScreenshotMode ? "渋谷駅 約280m" : location.landmark
    }

    private var landmarkIcon: String {
        let landmark = displayLandmark
        if landmark.contains("駅") || landmark.contains("Station") { return "tram.fill" }
        if landmark.contains("公園") || landmark.contains("Park") { return "leaf.fill" }
        if landmark.contains("病院") || landmark.contains("Hospital") { return "cross.case.fill" }
        if landmark.contains("学校") || landmark.contains("School") { return "building.columns.fill" }
        if landmark.contains("警察") || landmark.contains("Police") { return "shield.fill" }
        if landmark.contains("神社") || landmark.contains("Shrine") { return "house.fill" }
        if landmark.contains("寺") || landmark.contains("Temple") { return "building.columns.fill" }
        return "mappin.circle.fill"
    }

    private func takePhoto() {
        shutterPressed = true
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()

        withAnimation(.easeOut(duration: 0.12)) {
            showFlash = true
        }

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.16) {
            withAnimation(.easeOut(duration: 0.22)) {
                showFlash = false
                shutterPressed = false
            }
        }

        camera.capture { image in
            guard let image else { return }
            DispatchQueue.main.async {
                camera.lastPhoto = image
                CameraManager.saveWithOverlay(
                    image: image,
                    address: location.address,
                    landmark: location.landmark,
                    postalCode: location.postalCode
                )
                UINotificationFeedbackGenerator().notificationOccurred(.success)
                withAnimation(.spring(response: 0.35, dampingFraction: 0.78)) {
                    showSaved = true
                }
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.2) {
                    withAnimation(.easeInOut(duration: 0.25)) {
                        showSaved = false
                    }
                }
            }
        }
    }
}

private struct AddressPlate: View {
    let postalCode: String
    let address: String
    let landmark: String
    let landmarkIcon: String

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "mappin.and.ellipse")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundStyle(Color(hex: "67E8F9"))
                Text("ADDRESS STAMP")
                    .font(.caption.weight(.black))
                    .foregroundStyle(.white.opacity(0.72))
                Spacer()
                if !postalCode.isEmpty {
                    Text("〒\(postalCode)")
                        .font(.caption.weight(.bold))
                        .foregroundStyle(.white.opacity(0.8))
                }
            }

            Text(address.isEmpty ? "現在地の住所を取得しています" : address)
                .font(.system(.title3, design: .rounded).weight(.heavy))
                .foregroundStyle(.white)
                .lineLimit(2)
                .minimumScaleFactor(0.78)

            if !landmark.isEmpty {
                HStack(spacing: 8) {
                    Image(systemName: landmarkIcon)
                        .font(.system(size: 13, weight: .bold))
                    Text(landmark)
                        .font(.subheadline.weight(.bold))
                        .lineLimit(1)
                        .minimumScaleFactor(0.8)
                }
                .foregroundStyle(Color(hex: "FDE68A"))
                .padding(.horizontal, 10)
                .padding(.vertical, 7)
                .background(Color.white.opacity(0.12), in: Capsule())
            }
        }
        .padding(16)
        .background(
            LinearGradient(
                colors: [Color.black.opacity(0.58), Color(hex: "082F49").opacity(0.46)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            ),
            in: RoundedRectangle(cornerRadius: 24, style: .continuous)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .stroke(.white.opacity(0.18), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.35), radius: 24, y: 12)
    }
}

private struct HudPill: View {
    let icon: String
    let title: String
    let subtitle: String
    let tint: Color

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: icon)
                .font(.system(size: 14, weight: .black))
                .foregroundStyle(.black)
                .frame(width: 30, height: 30)
                .background(tint, in: Circle())

            VStack(alignment: .leading, spacing: 1) {
                Text(title)
                    .font(.caption.weight(.black))
                    .foregroundStyle(.white)
                Text(subtitle)
                    .font(.caption2.weight(.bold))
                    .foregroundStyle(.white.opacity(0.68))
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .background(.black.opacity(0.38), in: Capsule())
        .overlay(Capsule().stroke(.white.opacity(0.14), lineWidth: 1))
    }
}

private struct HudIconButton: View {
    let systemName: String
    let tint: Color

    var body: some View {
        Image(systemName: systemName)
            .font(.system(size: 17, weight: .black))
            .foregroundStyle(tint)
            .frame(width: 46, height: 46)
            .background(.black.opacity(0.38), in: Circle())
            .overlay(Circle().stroke(.white.opacity(0.14), lineWidth: 1))
    }
}

private struct ThumbnailView: View {
    let photo: UIImage?

    var body: some View {
        ZStack {
            if let photo {
                Image(uiImage: photo)
                    .resizable()
                    .scaledToFill()
            } else {
                LinearGradient(
                    colors: [Color.white.opacity(0.18), Color.white.opacity(0.06)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                Image(systemName: "photo.on.rectangle.angled")
                    .font(.system(size: 20, weight: .bold))
                    .foregroundStyle(.white.opacity(0.7))
            }
        }
        .frame(width: 62, height: 62)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(.white.opacity(photo == nil ? 0.18 : 0.95), lineWidth: photo == nil ? 1 : 2)
        )
    }
}

private struct SavedToast: View {
    var body: some View {
        VStack {
            HStack(spacing: 10) {
                Image(systemName: "checkmark.seal.fill")
                    .foregroundStyle(Color(hex: "86EFAC"))
                VStack(alignment: .leading, spacing: 2) {
                    Text("保存しました")
                        .font(.headline.weight(.heavy))
                    Text("住所付きでフォトライブラリに保存しました")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.white.opacity(0.72))
                }
            }
            .foregroundStyle(.white)
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(.black.opacity(0.72), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(.white.opacity(0.16), lineWidth: 1)
            )
            .padding(.top, 18)

            Spacer()
        }
    }
}

private struct ViewfinderOverlay: View {
    var body: some View {
        GeometryReader { proxy in
            let width = proxy.size.width
            let height = proxy.size.height

            ZStack {
                LinearGradient(colors: [.black.opacity(0.46), .clear, .black.opacity(0.52)], startPoint: .top, endPoint: .bottom)
                    .ignoresSafeArea()

                Path { path in
                    let inset: CGFloat = 28
                    let top = height * 0.22
                    let bottom = height * 0.68
                    let corner: CGFloat = 34

                    path.move(to: CGPoint(x: inset, y: top + corner))
                    path.addLine(to: CGPoint(x: inset, y: top))
                    path.addLine(to: CGPoint(x: inset + corner, y: top))

                    path.move(to: CGPoint(x: width - inset - corner, y: top))
                    path.addLine(to: CGPoint(x: width - inset, y: top))
                    path.addLine(to: CGPoint(x: width - inset, y: top + corner))

                    path.move(to: CGPoint(x: inset, y: bottom - corner))
                    path.addLine(to: CGPoint(x: inset, y: bottom))
                    path.addLine(to: CGPoint(x: inset + corner, y: bottom))

                    path.move(to: CGPoint(x: width - inset - corner, y: bottom))
                    path.addLine(to: CGPoint(x: width - inset, y: bottom))
                    path.addLine(to: CGPoint(x: width - inset, y: bottom - corner))
                }
                .stroke(.white.opacity(0.36), style: StrokeStyle(lineWidth: 2.2, lineCap: .round, lineJoin: .round))
            }
        }
    }
}
