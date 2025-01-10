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
USER_TOPIC = os.getenv('USER_TOPIC')

# Simulation parameters
USER_ID = os.getenv('USER_ID')
eczema = os.getenv('ECZEMA') == 'True'
hay_fever = os.getenv('HAY_FEVER') == 'True'
cad_probability = float(os.getenv('CAD_PROBABILITY'))
cad = os.getenv('CAD') == 'True'
ragweed_pollen_allergy = os.getenv('RAGWEED_POLLEN_ALLERGY') == 'True'
grass_pollen_allergy = os.getenv('GRASS_POLLEN_ALLERGY') == 'True'
mugwort_pollen_allergy = os.getenv('MUGWORT_POLLEN_ALLERGY') == 'True'
birch_pollen_allergy = os.getenv('BIRCH_POLLEN_ALLERGY') == 'True'
alder_pollen_allergy = os.getenv('ALDER_POLLEN_ALLERGY') == 'True'
olive_pollen_allergy = os.getenv('OLIVE_POLLEN_ALLERGY') == 'True'
asthma_allergy = os.getenv('ASTHMA_ALLERGY') == 'True'

# Cassandra environment variables
CASSANDRA_CLUSTER = os.getenv('CASSANDRA_CLUSTER')
CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE')

# Define list of topics
TOPICS = [
    NewTopic(AIR_QUALITY_TOPIC, num_partitions=3, replication_factor=1),
    NewTopic(WEREABLE_SIMULATOR_TOPIC, num_partitions=3, replication_factor=1),
    NewTopic(HEALTH_RECOMMENDATIONS_TOPIC, num_partitions=3, replication_factor=1),
    NewTopic(USER_TOPIC, num_partitions=3, replication_factor=1),
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

def store_pregenerated_batch_of_users(cassandra):
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

    # Store the result
    for user in list_of_dicts:
        cassandra.add_user(user)
        # print(user)

def store_simulation_user(cassandra):
    # Define a user for the simulation, assign a fixed uuid   
    # Create user dict with first batch of non configurable params
    # Note order of key value pairs is important for the cassandra query
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
    }

    # Set the configurable parameters
    user['eczema'] = eczema
    user['hay_fever'] = hay_fever

    # Update with other non configurable params
    user.update({
        'wheezing': False,
        'shortness_of_breath': False,
        'chest_tightness': True,
        'coughing': True,
        'nighttime_symptoms': False,
        'exercise_induced': True,
        'obesity': True
    })

    # Set the remainig configurable parameters
    user['cad_probability'] = float(cad_probability)
    user['cad'] = cad
    user['ragweed_pollen_allergy'] = ragweed_pollen_allergy
    user['grass_pollen_allergy'] = grass_pollen_allergy
    user['mugwort_pollen_allergy'] = mugwort_pollen_allergy
    user['birch_pollen_allergy'] = birch_pollen_allergy
    user['alder_pollen_allergy'] = alder_pollen_allergy
    user['olive_pollen_allergy'] = olive_pollen_allergy
    user['asthma_allergy'] = asthma_allergy
    user['date_of_birth'] = '1965-06-03'

    print(user)

    cassandra.add_user(user)


def setup_cassandra():
    # Connect to a cluster in a session
    cassandra = CassandraClient(CASSANDRA_CLUSTER)
    
    cassandra.create_table_user()
    cassandra.create_table_municipality_weather_data()

    # Load pregenerated user and simulation user to the db
    store_pregenerated_batch_of_users(cassandra)
    store_simulation_user(cassandra)
    
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