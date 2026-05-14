import SwiftUI
import GoogleMobileAds
import UIKit

struct BannerAdView: UIViewRepresentable {
    var adUnitID = "ca-app-pub-9404799280370656/7882448349"
    @ObservedObject private var adMobStartup = AdMobStartup.shared

    func makeUIView(context: Context) -> AdBannerContainer {
        let container = AdBannerContainer(adUnitID: adUnitID)
        return container
    }

    func updateUIView(_ uiView: AdBannerContainer, context: Context) {
        if adMobStartup.isReady {
            uiView.loadAdIfPossible()
        }
    }
}

class AdBannerContainer: UIView {
    private let banner: GADBannerView
    private var adLoaded = false

    init(adUnitID: String) {
        banner = GADBannerView(adSize: GADAdSizeBanner)
        banner.adUnitID = adUnitID
        super.init(frame: .zero)
        addSubview(banner)
    }

    required init?(coder: NSCoder) {
        return nil
    }

    override func didMoveToWindow() {
        super.didMoveToWindow()
        loadAdIfPossible()
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        banner.frame = bounds
        loadAdIfPossible()
    }

    func loadAdIfPossible() {
        guard !adLoaded else { return }
        guard banner.bounds.width > 0 || bounds.width > 0 else { return }

        if banner.rootViewController == nil {
            banner.rootViewController = window?.rootViewController ?? UIApplication.shared.adRootViewController
        }

        guard banner.rootViewController != nil else { return }
        banner.load(GADRequest())
        adLoaded = true
    }
}

private extension UIApplication {
    var adRootViewController: UIViewController? {
        connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first { $0.isKeyWindow }?
            .rootViewController
    }
}
