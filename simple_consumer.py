import redis
from kafka import KafkaConsumer


TOPIC_NAME = 'wereable_simulator'

consumer = KafkaConsumer(TOPIC_NAME)
for message in consumer:
    print(message)