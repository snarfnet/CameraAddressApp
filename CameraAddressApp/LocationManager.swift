import CoreLocation
import Combine

class LocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    private let geocoder = CLGeocoder()

    @Published var address: String = ""
    @Published var landmark: String = ""
    @Published var postalCode: String = ""
    @Published var coordinate: CLLocationCoordinate2D?

    private var lastGeocodedLocation: CLLocation?

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.requestWhenInUseAuthorization()
        manager.startUpdatingLocation()
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        coordinate = location.coordinate

        if let last = lastGeocodedLocation, location.distance(from: last) < 10 {
            return
        }
        lastGeocodedLocation = location

        geocoder.cancelGeocode()
        geocoder.reverseGeocodeLocation(location) { [weak self] placemarks, _ in
            guard let self, let pm = placemarks?.first else { return }
            self.buildAddress(from: pm)
            self.fetchNearbyLandmark(lat: location.coordinate.latitude, lon: location.coordinate.longitude)
        }
    }

    private func buildAddress(from pm: CLPlacemark) {
        var parts: [String] = []
        if let admin = pm.administrativeArea { parts.append(admin) }
        if let locality = pm.locality { parts.append(locality) }
        if let subLocality = pm.subLocality { parts.append(subLocality) }
        if let thoroughfare = pm.thoroughfare { parts.append(thoroughfare) }
        if let subThoroughfare = pm.subThoroughfare { parts.append(subThoroughfare) }
        address = parts.joined()
        postalCode = pm.postalCode ?? ""
    }

    func fetchNearbyLandmark(lat: Double, lon: Double) {
        let query = """
        [out:json][timeout:5];
        (
          node["railway"="station"](around:500,\(lat),\(lon));
          way["railway"="station"](around:500,\(lat),\(lon));
          node["leisure"="park"](around:200,\(lat),\(lon));
          way["leisure"="park"](around:200,\(lat),\(lon));
          relation["leisure"="park"](around:200,\(lat),\(lon));
          node["amenity"~"hospital|school|police|fire_station"](around:300,\(lat),\(lon));
          way["amenity"~"hospital|school|police|fire_station"](around:300,\(lat),\(lon));
          node["tourism"~"museum|temple|shrine"](around:300,\(lat),\(lon));
          way["tourism"~"museum|temple|shrine"](around:300,\(lat),\(lon));
          node["historic"](around:300,\(lat),\(lon));
        );
        out center 5;
        """

        guard let url = URL(string: "https://overpass-api.de/api/interpreter") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.httpBody = "data=\(query)".addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed)?.data(using: .utf8)
        request.timeoutInterval = 8

        URLSession.shared.dataTask(with: request) { [weak self] data, _, _ in
            guard let data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let elements = json["elements"] as? [[String: Any]] else {
                return
            }

            var best: (name: String, dist: Double, type: String)?
            for el in elements {
                guard let tags = el["tags"] as? [String: String],
                      let name = tags["name"] ?? tags["name:ja"] else { continue }

                var elLat: Double
                var elLon: Double
                if let center = el["center"] as? [String: Double] {
                    elLat = center["lat"] ?? 0
                    elLon = center["lon"] ?? 0
                } else {
                    elLat = el["lat"] as? Double ?? 0
                    elLon = el["lon"] as? Double ?? 0
                }

                let dist = self?.distance(lat1: lat, lon1: lon, lat2: elLat, lon2: elLon) ?? 9999

                let type: String
                if tags["railway"] == "station" { type = "station" }
                else if tags["leisure"] == "park" { type = "park" }
                else { type = "facility" }

                if best == nil || dist < best!.dist {
                    best = (name, dist, type)
                }
            }

            DispatchQueue.main.async {
                if let best {
                    let suffix: String
                    switch best.type {
                    case "station":
                        let distM = Int(best.dist)
                        suffix = distM < 100 ? "\(best.name)駅" : "\(best.name)駅 約\(distM)m"
                    case "park":
                        suffix = "\(best.name)"
                    default:
                        suffix = "\(best.name) 付近"
                    }
                    self?.landmark = suffix
                } else {
                    self?.landmark = ""
                }
            }
        }.resume()
    }

    private func distance(lat1: Double, lon1: Double, lat2: Double, lon2: Double) -> Double {
        let loc1 = CLLocation(latitude: lat1, longitude: lon1)
        let loc2 = CLLocation(latitude: lat2, longitude: lon2)
        return loc1.distance(from: loc2)
    }
}
