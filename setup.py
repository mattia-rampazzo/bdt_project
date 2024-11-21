from kafka import KafkaAdminClient
from kafka.admin import NewTopic
import time
import os
import pandas as pd

from services.redis_client import RedisClient

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
MUNICIPALITIES_AIR_QUALITY_UPDATE = os.getenv('MUNICIPALITIES_AIR_QUALITY_UPDATE')
WEREABLE_SIMULATOR_TOPIC = os.getenv('WEREABLE_SIMULATOR_TOPIC')
HEALTH_RECOMMENDATIONS_TOPIC = os.getenv('HEALTH_RECOMMENDATIONS_TOPIC')

# Define list of topics
TOPICS = [
    NewTopic(MUNICIPALITIES_AIR_QUALITY_UPDATE, num_partitions=3, replication_factor=1),
    NewTopic(WEREABLE_SIMULATOR_TOPIC, num_partitions=3, replication_factor=1),
    NewTopic(HEALTH_RECOMMENDATIONS_TOPIC, num_partitions=3, replication_factor=1),
]

def wait_for_kafka_ready(bootstrap_servers, max_retries=10, delay=10):
    """Wait for Kafka brokers to be ready by checking if we can list topics."""
    admin = None
    for _ in range(max_retries):
        try:
            admin = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
            # Check if we can list topics, indicating Kafka is ready
            admin.list_topics()
            print("Kafka brokers are ready.")
            return admin
        except Exception as e:
            print(f"Kafka not ready yet: {e}")
            time.sleep(delay)
    raise RuntimeError("Kafka brokers did not become ready in time.")

def create_topics(admin):
    """Create topics in Kafka."""
    try:
        admin.create_topics(TOPICS)
        print("Topics created successfully.")
    except Exception as e:
        print(f"Failed to create topics: {e}")

def setup_kafka():
    # Wait for Kafka to be ready
    admin = wait_for_kafka_ready(KAFKA_BOOTSTRAP_SERVERS)
    
    # Create topics
    create_topics(admin)



def initialize_municipalities(r, df_mun):

    if not r.exists('municipalities'):
        # Create geospatial index
        print("Creating municipalities geospatial index...")
        for index, row in df_mun.iterrows():
            r.geoadd('municipalities', (row['lng'], row['lat'], f"municipality:{row['istat']}"))

def setup_redis():

    r = RedisClient()

    df_mun = pd.read_csv('data/Trentino-AltoAdige_municipalities.csv')

    initialize_municipalities(r, df_mun)




if __name__ == "__main__":

    print("Settitng up Redis")

    setup_redis()

    print("rEDIS oK")
    # setup_cassandra()

    print("Settitng up Kafka")
    setup_kafka()
    
    print("cass")
    print()



