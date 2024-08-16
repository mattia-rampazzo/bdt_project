from kafka import KafkaAdminClient
from kafka.admin import NewTopic
import time
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
MUNICIPALITIES_AIR_QUALITY_UPDATE = os.getenv('MUNICIPALITIES_AIR_QUALITY_UPDATE')
WEREABLE_SIMULATOR_TOPIC=os.getenv('WEREABLE_SIMULATOR_TOPIC')
HEALTH_RECOMMENDATIONS_TOPIC=os.getenv('HEALTH_RECOMMENDATIONS_TOPIC')

TOPICS = [
    NewTopic(MUNICIPALITIES_AIR_QUALITY_UPDATE, num_partitions=3, replication_factor=1),
    NewTopic(WEREABLE_SIMULATOR_TOPIC, num_partitions=3, replication_factor=1),
    NewTopic(HEALTH_RECOMMENDATIONS_TOPIC, num_partitions=3, replication_factor=1),    
]

def wait_for_kafka_ready(brokers, max_retries=10, delay=10):
    admin = KafkaAdminClient(bootstrap_servers=brokers)
    for _ in range(max_retries):
        try:
            # Check if we can list topics, indicating Kafka is ready
            admin.list_topics()
            print("Kafka brokers are ready.")
            return
        except Exception as e:
            print(f"Kafka not ready yet: {e}")
            time.sleep(delay)
    raise RuntimeError("Kafka brokers did not become ready in time.")

def create_topics(brokers):
    admin = KafkaAdminClient(bootstrap_servers=brokers)
    try:
        admin.create_topics(TOPICS)
        print("Topics created successfully.")
    except Exception as e:
        print(f"Failed to create topics: {e}")

if __name__ == "__main__":
    print("Waiting for Kafka brokers to be ready...")
    wait_for_kafka_ready(KAFKA_BOOTSTRAP_SERVERS)
    print("Creating topics...")
    create_topics(KAFKA_BOOTSTRAP_SERVERS)
