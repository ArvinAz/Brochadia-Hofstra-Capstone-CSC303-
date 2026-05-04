import geopandas as gpd
import random
from shapely.geometry import Point

def get_random_coordinates(country_name, num_points=3):
    """
    Generates random (latitude, longitude) pairs within a specified country.
    """
    # 1. Load the built-in low-resolution world map from geopandas
    # Note: Depending on your geopandas version, you may see a deprecation warning 
    # for get_path, but it remains the standard built-in dataset for this purpose.
    url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    world = gpd.read_file(url)

    # 2. Filter the dataset for the requested country
    country_data = world[world['NAME'] == country_name]

    if country_data.empty:
        raise ValueError(f"Country '{country_name}' not found. Please check your spelling (e.g., 'United States of America' instead of 'USA').")

    # 3. Extract the geometry (Polygon or MultiPolygon) for the country
    country_geom = country_data.geometry.iloc[0]

    # 4. Get the bounding box coordinates of the country (min_lon, min_lat, max_lon, max_lat)
    minx, miny, maxx, maxy = country_geom.bounds

    valid_points = []
    
    print(f"Generating {num_points} points inside {country_name}...")

    # 5. Loop until we find the requested number of valid points
    while len(valid_points) < num_points:
        # Generate a random longitude (x) and latitude (y) within the bounding box
        random_lon = random.uniform(minx, maxx)
        random_lat = random.uniform(miny, maxy)
        
        # Create a Shapely Point object
        point = Point(random_lon, random_lat)

        # 6. Check if the randomly generated point is actually inside the country's borders
        if country_geom.contains(point):
            # Append as (Latitude, Longitude)
            valid_points.append((random_lat, random_lon))

    return valid_points

# --- Example Usage ---
if __name__ == "__main__":
    # Change this to any country in the naturalearth dataset
    target_country = "France" 
    
    try:
        coordinates = get_random_coordinates(target_country, num_points=3)
        
        print("\nResults:")
        for i, (lat, lon) in enumerate(coordinates, 1):
            print(f"Point {i}: Latitude {lat:.6f}, Longitude {lon:.6f}")
            
    except ValueError as e:
        print(f"Error: {e}")