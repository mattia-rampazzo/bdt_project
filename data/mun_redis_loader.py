import os
import redis
import pandas as pd

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

df_municipalities = pd.read_json(os.path.join("data", "trentino_municipalities.json"))

for index, row in df_municipalities.iterrows():
    r.geoadd('municipalities', (row['lng'], row['lat'], f"municipality:{row['istat']}"))