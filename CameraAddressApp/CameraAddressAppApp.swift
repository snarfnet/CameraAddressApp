import SwiftUI
import GoogleMobileAds
import AppTrackingTransparency

@main
struct CameraAddressAppApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .onAppear {
                    MobileAds.shared.start(completionHandler: nil)
                }
                .onReceive(NotificationCenter.default.publisher(for: UIApplication.didBecomeActiveNotification)) { _ in
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                        ATTrackingManager.requestTrackingAuthorization { _ in }
                    }
                }
        }
    }
}
