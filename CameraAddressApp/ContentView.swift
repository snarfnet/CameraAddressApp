import SwiftUI

struct ContentView: View {
    @StateObject private var camera = CameraManager()
    @StateObject private var location = LocationManager()
    @State private var showFlash = false
    @State private var showSaved = false
    @State private var showLastPhoto = false

    private var isScreenshotMode: Bool {
        ProcessInfo.processInfo.arguments.contains("-SCREENSHOT_MODE")
    }

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            VStack(spacing: 0) {
                // Camera preview
                ZStack(alignment: .bottom) {
                    if isScreenshotMode {
                        Image("DemoStreet")
                            .resizable()
                            .scaledToFill()
                            .ignoresSafeArea(edges: .top)
                    } else {
                        CameraPreview(session: camera.session)
                            .ignoresSafeArea(edges: .top)
                    }

                    // Address overlay
                    VStack(alignment: .leading, spacing: 4) {
                        if !displayPostalCode.isEmpty {
                            Text("\u{3012}\(displayPostalCode)")
                                .font(.caption)
                                .foregroundColor(.white.opacity(0.85))
                        }

                        if !displayAddress.isEmpty {
                            Text(displayAddress)
                                .font(.system(size: 16, weight: .bold))
                                .foregroundColor(.white)
                        }

                        if !displayLandmark.isEmpty {
                            HStack(spacing: 4) {
                                Image(systemName: landmarkIcon)
                                    .font(.caption)
                                Text(displayLandmark)
                                    .font(.system(size: 15, weight: .semibold))
                            }
                            .foregroundColor(.yellow)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(12)
                    .background(
                        LinearGradient(colors: [.clear, .black.opacity(0.7)],
                                       startPoint: .top, endPoint: .bottom)
                    )

                    // Flash effect
                    if showFlash {
                        Color.white.ignoresSafeArea()
                            .transition(.opacity)
                    }
                }

                // Bottom bar
                HStack {
                    // Thumbnail
                    if let photo = camera.lastPhoto {
                        Button {
                            showLastPhoto = true
                        } label: {
                            Image(uiImage: photo)
                                .resizable()
                                .scaledToFill()
                                .frame(width: 50, height: 50)
                                .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                    } else {
                        Color.clear.frame(width: 50, height: 50)
                    }

                    Spacer()

                    // Shutter button
                    Button {
                        takePhoto()
                    } label: {
                        ZStack {
                            Circle()
                                .stroke(.white, lineWidth: 4)
                                .frame(width: 70, height: 70)
                            Circle()
                                .fill(.white)
                                .frame(width: 60, height: 60)
                        }
                    }

                    Spacer()

                    Color.clear.frame(width: 50, height: 50)
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 12)
                .background(Color.black)

                // Ad banner
                BannerAdView(adUnitID: "ca-app-pub-9404799280370656/7882448349")
                    .frame(height: 50)
                    .background(Color.black)
            }

            // Saved indicator
            if showSaved {
                VStack {
                    Spacer()
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                        Text(NSLocalizedString("saved", comment: ""))
                    }
                    .font(.headline)
                    .foregroundColor(.white)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 10)
                    .background(Capsule().fill(.green.opacity(0.85)))
                    .padding(.bottom, 160)
                }
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .onAppear { if !isScreenshotMode { camera.start() } }
        .fullScreenCover(isPresented: $showLastPhoto) {
            if let photo = camera.lastPhoto {
                PhotoPreviewView(image: photo) {
                    showLastPhoto = false
                }
            }
        }
    }

    private var displayPostalCode: String {
        isScreenshotMode ? "150-0042" : location.postalCode
    }
    private var displayAddress: String {
        isScreenshotMode ? "東京都渋谷区宇田川町21-6" : location.address
    }
    private var displayLandmark: String {
        isScreenshotMode ? "渋谷駅 (280m)" : location.landmark
    }

    private var landmarkIcon: String {
        let lm = displayLandmark
        if lm.contains("駅") || lm.contains("Station") { return "tram.fill" }
        if lm.contains("公園") || lm.contains("Park") { return "leaf.fill" }
        if lm.contains("病院") || lm.contains("Hospital") { return "cross.case.fill" }
        if lm.contains("学校") || lm.contains("School") { return "building.columns.fill" }
        if lm.contains("警察") || lm.contains("Police") { return "shield.fill" }
        if lm.contains("神社") || lm.contains("Shrine") { return "house.fill" }
        if lm.contains("寺") || lm.contains("Temple") { return "house.fill" }
        return "mappin.circle.fill"
    }

    private func takePhoto() {
        withAnimation(.easeOut(duration: 0.15)) { showFlash = true }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
            withAnimation { showFlash = false }
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
                withAnimation { showSaved = true }
                DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                    withAnimation { showSaved = false }
                }
            }
        }
    }
}
