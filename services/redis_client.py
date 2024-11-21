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
    def __init__(self, host=REDIS_SERVER, port=REDIS_PORT, db=0):
        """
        Initializes the Redis connection.
        :param host: Redis server hostname (default is localhost)
        :param port: Redis server port (default is 6379)
        :param db: Redis database index (default is 0)
        """
        self.client = redis.Redis(host=host, port=port, db=db)

    def exists(self, key):
        """
        Check if a key exists in Redis.
        :param key: Key name
        :return: True if the key exists, False otherwise
        """
        return self.client.exists(key) > 0

    def keys(self, pattern="*"):
        """
        Get all keys matching a pattern.
        :param pattern: Pattern to match (default is all keys)
        :return: List of matching keys
        """
        return [key.decode() for key in self.client.keys(pattern)]

    def hset(self, name, key, value):
        """
        Set a field in a hash.
        :param name: Hash name
        :param key: Field name
        :param value: Value to set
        """
        self.client.hset(name, key, value)

    def hget(self, name, key):
        """
        Get the value of a field in a hash.
        :param name: Hash name
        :param key: Field name
        :return: Value of the field
        """
        return self.client.hget(name, key).decode()

    def hgetall(self, name):
        """
        Get all fields and values in a hash.
        :param name: Hash name
        :return: Dictionary of fields and values
        """
        return {key.decode(): value.decode() for key, value in self.client.hgetall(name).items()}
    
    def geoadd(self, key, value):
        self.client.geoadd(key, value)