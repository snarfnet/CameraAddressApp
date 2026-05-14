import SwiftUI
import GoogleMobileAds
import AppTrackingTransparency
import UIKit

final class AdMobStartup: ObservableObject {
    static let shared = AdMobStartup()

    @Published private(set) var isReady = false
    @Published private(set) var trackingFlowCompleted = false
    private var didStart = false
    private var didRequestTracking = false

    private func startIfNeeded() {
        guard !didStart else { return }
        didStart = true

        GADMobileAds.sharedInstance().start { [weak self] _ in
            DispatchQueue.main.async {
                self?.isReady = true
            }
        }
    }

    func requestTrackingThenStartAdsIfNeeded() {
        guard !didRequestTracking else {
            if trackingFlowCompleted {
                startIfNeeded()
            }
            return
        }
        guard UIApplication.shared.applicationState == .active else { return }
        didRequestTracking = true

        guard #available(iOS 14, *),
              ATTrackingManager.trackingAuthorizationStatus == .notDetermined else {
            trackingFlowCompleted = true
            startIfNeeded()
            return
        }

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) { [weak self] in
            guard UIApplication.shared.applicationState == .active else {
                self?.didRequestTracking = false
                return
            }
            ATTrackingManager.requestTrackingAuthorization { _ in
                DispatchQueue.main.async {
                    self?.trackingFlowCompleted = true
                    self?.startIfNeeded()
                }
            }
        }
    }
}

@main
struct CameraAddressAppApp: App {
    @StateObject private var adMobStartup = AdMobStartup.shared
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            Group {
                if adMobStartup.trackingFlowCompleted {
                    ContentView()
                } else {
                    TrackingPermissionLaunchView()
                }
            }
            .onAppear {
                DispatchQueue.main.async {
                    adMobStartup.requestTrackingThenStartAdsIfNeeded()
                }
            }
            .onChange(of: scenePhase) { newPhase in
                guard newPhase == .active else { return }
                adMobStartup.requestTrackingThenStartAdsIfNeeded()
            }
        }
    }
}

private struct TrackingPermissionLaunchView: View {
    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            VStack(spacing: 14) {
                Image(systemName: "camera.viewfinder")
                    .font(.system(size: 38, weight: .bold))
                    .foregroundStyle(Color(hex: "5EEAD4"))
                Text("CameraAddress")
                    .font(.system(size: 28, weight: .black, design: .rounded))
                    .foregroundStyle(.white)
                Text("起動準備中")
                    .font(.subheadline.weight(.bold))
                    .foregroundStyle(.white.opacity(0.62))
            }
        }
    }
}
