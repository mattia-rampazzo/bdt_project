import os
import redis
import pandas as pd

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

df_municipalities = pd.read_json(os.path.join("data", "trentino_municipalities.json"))
# decomment to not waste too many apis
df_municipalities = df_municipalities.head(150) # 150 li tiene, di piu difficile, lurl dell api troppo grosso...


for index, row in df_municipalities.iterrows():
    r.geoadd('municipalities', (row['lng'], row['lat'], f"municipality:{row['istat']}"))

# # Function to get municipalities within a radius
# def get_municipalities_within_radius(center_key, radius, unit='km'):
#     nearby_municipalities = r.georadiusbymember('municipalities', center_key, radius, unit=unit, withdist=True)
#     results = []
#     for municipality in nearby_municipalities:
#         municipality_id = municipality[0].decode('utf-8')
#         distance = municipality[1]
#         details = r.hgetall(municipality_id)
#         print(municipality_id)
#         print(details)

#         # results.append({
#         #     'municipality_id': int(details[b'municipality_id']),
#         #     'name': details[b'name'].decode('utf-8'),
#         #     'latitude': float(details[b'latitude']),
#         #     'longitude': float(details[b'longitude']),
#         #     'distance': distance
#         # })
#     return results

# def get_closest_municipality(center_key):
#     # Use a large radius and limit the result to 1
#     # closest_municipality = r.georadiusbymember('municipalities', center_key, 10000, unit='km', withdist=True, count=10)
#     closest_municipality = r.georadius('municipalities',  11.119681, 46.215179, 10000, unit='km', withdist=True, count=10)

#     if not closest_municipality:
#         return None
#     municipality_id = closest_municipality[0][0].decode('utf-8')
#     distance = closest_municipality[0][1]
#     for closesr in closest_municipality:
#         details = r.hgetall(closesr[0])
#         print(details)
    
#     details = r.hgetall(b'municipality:22047')
#     print(details)

# # Example usage: Find all municipalities within 50 km of Aldino (istat 21001)
# center_key = 'municipality:21001'
# radius = 10  # radius in kilometers
# closest_municipality = get_closest_municipality(center_key)