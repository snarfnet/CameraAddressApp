import SwiftUI
import GoogleMobileAds
import AppTrackingTransparency

final class AdMobStartup: ObservableObject {
    static let shared = AdMobStartup()

    @Published private(set) var isReady = false
    private var didStart = false
    private var didRequestTracking = false

    func startIfNeeded() {
        guard !didStart else { return }
        didStart = true

        GADMobileAds.sharedInstance().start { [weak self] _ in
            DispatchQueue.main.async {
                self?.isReady = true
            }
        }
    }

    func requestTrackingIfNeeded() {
        guard !didRequestTracking else { return }
        didRequestTracking = true

        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            ATTrackingManager.requestTrackingAuthorization { _ in }
        }
    }
}

@main
struct CameraAddressAppApp: App {
    @StateObject private var adMobStartup = AdMobStartup.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .onAppear {
                    adMobStartup.startIfNeeded()
                }
                .onReceive(NotificationCenter.default.publisher(for: UIApplication.didBecomeActiveNotification)) { _ in
                    adMobStartup.requestTrackingIfNeeded()
                }
        }
    }
}
