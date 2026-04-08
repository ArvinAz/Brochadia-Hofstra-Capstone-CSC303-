import os
import time
from pathlib import Path

from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


def main():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    mongo_password = os.getenv("VITE_MONGO_PASSWORD")
    if not mongo_password:
        raise RuntimeError("Missing env var VITE_MONGO_PASSWORD")

    uri = (
        f"mongodb+srv://azad:{mongo_password}"
        "@dwcluster.2zyrq7o.mongodb.net/?appName=DWCluster"
    )
    client = MongoClient(uri, server_api=ServerApi("1"))
    db = client["Brochadia"]
    trips = db["Trips"]

    geocoder = Nominatim(user_agent="brochadia-geopy-trip-locations")

    locations = trips.distinct("location")
    locations = sorted([loc for loc in locations if isinstance(loc, str) and loc.strip()])

    print(f"Found {len(locations)} unique trip locations.")

    results = {}
    failures = []

    for i, loc in enumerate(locations, start=1):
        try:
            place = geocoder.geocode(loc, exactly_one=True, timeout=10)
        except Exception as e:
            failures.append((loc, f"exception: {e}"))
            print(f"[{i}/{len(locations)}] {loc} -> ERROR ({e})")
            time.sleep(1.2)
            continue

        if not place:
            failures.append((loc, "not found"))
            print(f"[{i}/{len(locations)}] {loc} -> NOT FOUND")
            time.sleep(1.2)
            continue

        coords = (place.latitude, place.longitude)
        results[loc] = coords
        print(f"[{i}/{len(locations)}] {loc} -> {coords[0]}, {coords[1]}")

        # Be polite with Nominatim usage policy (avoid rapid-fire requests).
        time.sleep(1.2)

    print("\nSummary")
    print(f"- Success: {len(results)}")
    print(f"- Failed:  {len(failures)}")

    if failures:
        print("\nFailed locations:")
        for loc, reason in failures:
            print(f"- {loc}: {reason}")


if __name__ == "__main__":
    main()

