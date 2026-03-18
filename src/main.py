import pandas as pd
import requests
import math
import openrouteservice

# ========== CONFIG ==========
ORS_API_KEY = "YOUR_ORS_KEY"  # Replace with your actual key
SEARCH_RADIUS = 2000          # 2km Radius

class AmenityExtractor:
    def __init__(self, api_key):
        self.client = openrouteservice.Client(key=api_key)

    def get_coords(self, location_query):
        """Converts place name to Latitude and Longitude."""
        try:
            res = self.client.pelias_search(text=location_query, size=1)
            if res['features']:
                lon, lat = res['features'][0]['geometry']['coordinates']
                return lat, lon
        except Exception as e:
            print(f"Geocoding Error: {e}")
        return None, None

    def haversine_dist(self, lat1, lon1, lat2, lon2):
        """Calculates exact distance in meters between two GPS points."""
        R = 6371000 # Earth radius in meters
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def fetch_amenities(self, lat, lon):
        """Queries the Overpass API for all amenities in the radius."""
        query = f"""
        [out:json][timeout:60];
        node(around:{SEARCH_RADIUS},{lat},{lon})["amenity"];
        out body;
        """
        response = requests.post("https://overpass-api.de/api/interpreter", data={"data": query})
        return response.json().get('elements', [])

    def run(self):
        target = input("Enter Area Name (e.g., 'Andheri East, Mumbai'): ")
        lat, lon = self.get_coords(target)
        
        if not lat:
            print("❌ Location not found.")
            return

        print(f"🛰️  Targeting: {lat}, {lon} | Scanning {SEARCH_RADIUS}m radius...")
        elements = self.fetch_amenities(lat, lon)
        
        results = []
        for el in elements:
            tags = el.get('tags', {})
            dist = self.haversine_dist(lat, lon, el.get('lat'), el.get('lon'))
            
            results.append({
                "Name": tags.get('name', 'Unnamed Facility'),
                "Type": tags.get('amenity'),
                "Distance_m": round(dist, 1),
                "Lat": el.get('lat'),
                "Lon": el.get('lon')
            })

        # Convert to DataFrame and Sort by proximity
        df = pd.DataFrame(results).sort_values('Distance_m')

        print(f"\n✅ Total Found: {len(df)} amenities.")
        print("-" * 60)
        # Display first 20 results in the console
        print(df[['Name', 'Type', 'Distance_m']].head(20).to_string(index=False))
        
        # Save to CSV
        filename = f"amenities_{target.replace(' ', '_')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 Full dataset saved to: {filename}")

if __name__ == "__main__":
    extractor = AmenityExtractor(ORS_API_KEY)
    extractor.run()
