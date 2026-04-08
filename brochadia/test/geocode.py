from geopy.geocoders import Nominatim
import time
from pprint import pprint


# instantiate a new Nominatim client
app = Nominatim(user_agent="tutorial")

# get location raw data
location = app.geocode("Cairo").raw
# print raw data
print(location['lat'], location['lon'])