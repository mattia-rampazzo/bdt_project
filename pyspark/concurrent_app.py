import threading
import time
from kafka import KafkaConsumer
import redis
import json

# Shared variable
shared_variable = {}

# Lock for synchronizing access to the shared variable
lock = threading.Lock()

def process_stream_data(stream_data):
    # Access and modify the shared variable safely
    with lock:
        print(f"Processing stream data: {stream_data}")


def process_redis_notification(notification, redis_client):
    # Handle the notification of Redis update
    print(f"Redis updated with AQI data: {notification['data']}")
    # Access and modify the shared variable safely
    with lock:
        shared_variable['aqi_data'] = notification['data']

def stream_data_consumer(redis_client):
    consumer = KafkaConsumer(
        'wereable_simulator',
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    for message in consumer:
        stream_data = message.value
        process_stream_data(stream_data, redis_client)

def redis_update_consumer(redis_client):
    consumer = KafkaConsumer(
        'open_meteo_scraper',
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    for message in consumer:
        notification = message.value
        process_redis_notification(notification, redis_client)

def main():
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    # Create threads for concurrent consumption
    stream_thread = threading.Thread(target=stream_data_consumer, args=(redis_client,))
    notification_thread = threading.Thread(target=redis_update_consumer, args=(redis_client,))

    # Start the threads
    stream_thread.start()
    notification_thread.start()
    
    # Join the threads
    stream_thread.join()
    notification_thread.join()

if __name__ == "__main__":
    main()
