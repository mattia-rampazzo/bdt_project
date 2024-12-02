import os
import json
import redis

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Redis connection
REDIS_SERVER=os.getenv('REDIS_SERVER')
REDIS_PORT=os.getenv('REDIS_PORT')


class RedisClient:
    _pool = None

    def __init__(self, host=REDIS_SERVER, port=REDIS_PORT, db=0):
        if RedisClient._pool is None:
            RedisClient._pool = redis.ConnectionPool(host=host, port=port, db=db, decode_responses=True)
        self.client = redis.Redis(connection_pool=RedisClient._pool)

    def exists(self, key):
        return self.client.exists(key) > 0

    def keys(self, pattern="*"):
        return [key for key in self.client.keys(pattern)]
    
    def get(self, key):
        tmp = self.client.get(key)
        if tmp is None:
            # Handle the case where no data is found
            print(f"No data found for the given key {key}.")
            return tmp

        return json.loads(tmp)
    
    def set(self, key, value):
        self.client.set(key, json.dumps(value))
    

    def hset(self, name, key, value):
        self.client.hset(name, key, value)

    def hget(self, name, key):
        value = self.client.hget(name, key)
        return value.decode() if value else None

    def hgetall(self, name):
        return {key: value for key, value in self.client.hgetall(name).items()}

    def geoadd(self, key, value):
        self.client.geoadd(key, value)

    def get_closest_municipality(self, longitude, latitude, radius):

        if not self.exists('municipalities'):
            return None

        closest = self.client.georadius(name="municipalities", longitude=longitude, latitude=latitude, radius=radius, unit='km', withdist=True, count=1)
        if closest:
            municipality = closest[0][0]
            # distance = closest[0][1]
            return municipality
        else:
            return None 
    
    def close(self):
        self.client.close()