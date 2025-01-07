from kafka import KafkaAdminClient
from kafka.admin import NewTopic
import time
import os
import uuid
import pandas as pd

from services.redis_client import RedisClient
from services.cassandra_client import CassandraClient

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
AIR_QUALITY_TOPIC = os.getenv('AIR_QUALITY_TOPIC')
WEREABLE_SIMULATOR_TOPIC = os.getenv('WEREABLE_SIMULATOR_TOPIC')
HEALTH_RECOMMENDATIONS_TOPIC = os.getenv('HEALTH_RECOMMENDATIONS_TOPIC')
USER_ID = os.getenv('USER_ID')


# Cassandra environment variables
CASSANDRA_CLUSTER = os.getenv('CASSANDRA_CLUSTER')
CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE')

# Define list of topics
TOPICS = [
    NewTopic(AIR_QUALITY_TOPIC, num_partitions=3, replication_factor=1),
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


def setup_cassandra():
    # Connect to a cluster in a session
    cassandra = CassandraClient(CASSANDRA_CLUSTER)
    
    cassandra.create_table_user()
    cassandra.create_table_municipality_weather_data()

    # Read df
    df_users = pd.read_csv('data/Users_synthetic_dataset.csv')

    # Keep firt 100
    df_users = df_users.head(100)

    # Drop PatientID: not unique
    df_users.drop(columns = ["PatientID"], inplace=True)

    # Define columns not to convert to boolean
    non_bool_columns = [
        'EducationLevel', 
        'bmi',
        'PhysicalActivity',
        'DietQuality',
        'SleepQuality',
        'PollutionExposure',
        'PollenExposure',
        'DustExposure',
        'Cad_Probability',
        'Date_of_Birth'
    ]

    # Convert relevant columns to boolean
    for col in df_users.columns:
        if col not in non_bool_columns:
            df_users[col] = df_users[col] == 1

    # Transform each row into a dictionary
    list_of_dicts = df_users.to_dict(orient='records')

    # Print the result
    for user in list_of_dicts:
        cassandra.add_user(user)
        # print(user)

    # Define a user for the simulation, assign a fixed uuid
    # 5693,1,1,25.5,0,6.6,2.8,5.5,3.0,6.3,2.2,0,1,0,0,0,0,1,1,0,1,1,0,0.02,0,0,1,0,0,1,0,1,1965-06-03
    user = {
        'user_id': uuid.UUID(USER_ID),
        'gender': True,
        'education_level': 1,
        'bmi': 25.5,
        'current_smoker': False, 
        'physical_activity': 6.6,
        'diet_quality': 2.8,
        'sleep_quality': 5.5,
        'pollution_exposure': 3.0,
        'pollen_exposure': 6.3,
        'dust_exposure': 2.2,
        'pet_allergy': False,
        'family_history_asthma': True,
        'history_of_allergies': False,
        'eczema': True,
        'hay_fever': False,
        'wheezing': False,
        'shortness_of_breath': False,
        'chest_tightness': True,
        'coughing': True,
        'nighttime_symptoms': False,
        'exercise_induced': True,
        'obesity': True,
        'cad_probability': 0.10,
        'cad': True,
        'ragweed_pollen_allergy': False,
        'grass_pollen_allergy': True,
        'mugwort_pollen_allergy': True,
        'birch_pollen_allergy': False,
        'alder_pollen_allergy': False,
        'olive_pollen_allergy': True,
        'asthma_allergy': True,
        'date_of_birth': '1965-06-03'
    }

    cassandra.add_user(user)
    print("Data inserted successfully.")

    # Shutdown the Cassandra connection
    cassandra.shutdown()


if __name__ == "__main__":

    print("Settitng up Redis")
    setup_redis()
    print("Redis ok")

    print("Settitng up Cassandra")
    setup_cassandra()
    print("Cassandra ok")

    print("Settitng up Kafka")
    setup_kafka()
    print("Kafka ok")