from kafka import KafkaProducer, KafkaConsumer
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
WEREABLE_SIMULATOR_TOPIC = os.getenv('WEREABLE_SIMULATOR_TOPIC')
HEALTH_RECOMMENDATIONS_TOPIC = os.getenv('HEALTH_RECOMMENDATIONS_TOPIC')
AIR_QUALITY_TOPIC = os.getenv('AIR_QUALITY_TOPIC')

# Dictionnaire to easily access topics
topics_dict = {}
topics_dict['a'] = AIR_QUALITY_TOPIC
topics_dict['h'] = HEALTH_RECOMMENDATIONS_TOPIC
topics_dict['w'] = WEREABLE_SIMULATOR_TOPIC


class KafkaProducerWrapper:
    def __init__(self, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS):
        self.bootstrap_servers = bootstrap_servers
        self.producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
        #self.consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers, auto_offset_reset='earliest', enable_auto_commit=True)

    def produce_data(self, topic, data):
        # Send message to a Kafka topic
        self.producer.send(topics_dict[topic], value=data)


class KafkaConsumerWrapper:
    def __init__(self, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS):
        self.bootstrap_servers = bootstrap_servers
        self.consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
        #self.consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers, auto_offset_reset='earliest', enable_auto_commit=True)

    def poll(self, topic, timeout_ms):
        self.consumer.subscribe([topics_dict[topic]])
        return self.consumer.poll(timeout_ms=timeout_ms)

    def consume_data(self, topic):
        # Consume messages from a Kafka topic
        self.consumer.subscribe([topics_dict[topic]])
        for msg in self.consumer:
            yield msg.value

    def close(self):
        self.consumer.close()