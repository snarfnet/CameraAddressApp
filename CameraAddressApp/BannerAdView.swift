import SwiftUI
import GoogleMobileAds

struct BannerAdView: UIViewRepresentable {
    var adUnitID = "ca-app-pub-9404799280370656/7882448349"

    func makeUIView(context: Context) -> AdBannerContainer {
        let container = AdBannerContainer(adUnitID: adUnitID)
        return container
    }

    func updateUIView(_ uiView: AdBannerContainer, context: Context) {}
}

class AdBannerContainer: UIView {
    private let banner: BannerView
    private var adLoaded = false

    init(adUnitID: String) {
        banner = BannerView(adSize: AdSizeBanner)
        banner.adUnitID = adUnitID
        super.init(frame: .zero)
        addSubview(banner)
    }

    required init?(coder: NSCoder) { fatalError() }

    override func didMoveToWindow() {
        super.didMoveToWindow()
        guard !adLoaded, let window else { return }
        if let rootVC = window.windowScene?.keyWindow?.rootViewController {
            banner.rootViewController = rootVC
            banner.load(Request())
            adLoaded = true
        }
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        banner.frame = bounds
    }
}
