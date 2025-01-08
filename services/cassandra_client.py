import os
import uuid
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, dict_factory
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Cassandra environment variables
CASSANDRA_CLUSTER = os.getenv('CASSANDRA_CLUSTER')
CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE')

class CassandraClient:
    def __init__(self, cluster=CASSANDRA_CLUSTER, keyspace=CASSANDRA_KEYSPACE):
        self.cluster = Cluster([cluster])  # Use the IP of your Cassandra node
        self.session = self.cluster.connect()
        self._create_keyspace(keyspace)


    def _create_keyspace(self, keyspace):
        query = f"""
            CREATE KEYSPACE IF NOT EXISTS {keyspace}
            WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
        """
        
        # Execute the query
        self.session.execute(query)
        self.session.set_keyspace(keyspace)

        print(f"Keyspace '{keyspace}' created successfully.")
    
    def create_table_user(self):

        # Create the 'users' table
        # query = """
        # CREATE TABLE IF NOT EXISTS users (
        #     user_id UUID PRIMARY KEY,
        #     username TEXT,
        #     email TEXT
        # );
        # """
        query = """
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY,          -- Patient ID (assuming integer)
            gender BOOLEAN,                          -- Gender (assuming 1 for Male, 2 for Female, etc.)
            education_level INT,                 -- Education Level
            bmi FLOAT,                           -- Body Mass Index
            current_smoker BOOLEAN,              -- Current Smoker (0 or 1)
            physical_activity FLOAT,             -- Physical Activity
            diet_quality FLOAT,                  -- Diet Quality
            sleep_quality FLOAT,                 -- Sleep Quality
            pollution_exposure FLOAT,            -- Pollution Exposure
            pollen_exposure FLOAT,               -- Pollen Exposure
            dust_exposure FLOAT,                 -- Dust Exposure
            pet_allergy BOOLEAN,                 -- Pet Allergy (true/false)
            family_history_asthma BOOLEAN,       -- Family History of Asthma (true/false)
            history_of_allergies BOOLEAN,        -- History of Allergies (true/false)
            eczema BOOLEAN,                      -- Eczema (true/false)
            hay_fever BOOLEAN,                   -- Hay Fever (true/false)
            wheezing BOOLEAN,                    -- Wheezing (true/false)
            shortness_of_breath BOOLEAN,         -- Shortness of Breath (true/false)
            chest_tightness BOOLEAN,             -- Chest Tightness (true/false)
            coughing BOOLEAN,                    -- Coughing (true/false)
            nighttime_symptoms BOOLEAN,          -- Nighttime Symptoms (true/false)
            exercise_induced BOOLEAN,            -- Exercise Induced (true/false)
            obesity BOOLEAN,                     -- Obesity (true/false)
            cad BOOLEAN,                         -- Coronary Artery Disease (true/false)
            cad_probability FLOAT,               -- Coronary Artery Disease Probability
            ragweed_pollen_allergy BOOLEAN,     -- Ragweed Pollen Allergy (true/false)
            grass_pollen_allergy BOOLEAN,       -- Grass Pollen Allergy (true/false)
            mugwort_pollen_allergy BOOLEAN,     -- Mugwort Pollen Allergy (true/false)
            birch_pollen_allergy BOOLEAN,       -- Birch Pollen Allergy (true/false)
            alder_pollen_allergy BOOLEAN,       -- Alder Pollen Allergy (true/false)
            olive_pollen_allergy BOOLEAN,       -- Olive Pollen Allergy (true/false)
            asthma_allergy BOOLEAN,              -- Asthma Allergy (true/false)
            date_of_birth DATE                  -- Date of Birth
        );
        """

        # Execute the query
        self.session.execute(query)
        print("Users table created successfully.")

    def create_table_municipality_weather_data(self):

        # Create the 'municipality_air_quality_data' table
        query = """
        CREATE TABLE IF NOT EXISTS municipality_air_quality_data (
            municipality_id INT,
            year INT,
            timestamp TIMESTAMP,
            name TEXT,
            latitude DOUBLE,
            longitude DOUBLE,
            european_aqi DOUBLE,
            us_aqi DOUBLE,
            pm10 DOUBLE,
            pm2_5 DOUBLE,
            carbon_monoxide DOUBLE,
            carbon_dioxide DOUBLE,
            nitrogen_dioxide DOUBLE,
            sulphur_dioxide DOUBLE,
            ozone DOUBLE,
            aerosol_optical_depth DOUBLE,
            dust DOUBLE,
            uv_index DOUBLE,
            uv_index_clear_sky DOUBLE,
            ammonia DOUBLE,
            alder_pollen DOUBLE,
            birch_pollen DOUBLE,
            grass_pollen DOUBLE,
            mugwort_pollen DOUBLE,
            olive_pollen DOUBLE,
            ragweed_pollen DOUBLE,
            temperature_2m DOUBLE,
            relative_humidity_2m DOUBLE,
            precipitation DOUBLE,
            rain DOUBLE,
            cloud_cover DOUBLE,
            cloud_cover_low DOUBLE,
            cloud_cover_mid DOUBLE,
            cloud_cover_high DOUBLE,
            wind_speed_10m DOUBLE,
            soil_temperature_0_to_7cm DOUBLE,
            PRIMARY KEY ((municipality_id, year), timestamp)
        ) WITH CLUSTERING ORDER BY (timestamp DESC);

        """
        # Execute the query
        self.session.execute(query)
        print("municipality_air_quality_data table created successfully.")

    def get_user(self, id):

        # Return a dict
        self.session.row_factory = dict_factory

        # Parameterized query to prevent SQL injection
        query = SimpleStatement("""
            SELECT * 
            FROM users 
            WHERE user_id = %s
        """)

        # Execute the query with the UUID parameter
        result = self.session.execute(query, (id,))
        
        # Fetch and return the result
        return result.one()
     
    def add_user(self, user):

        query = """
            INSERT INTO users (
                user_id, gender, education_level, bmi, current_smoker, physical_activity, 
                diet_quality, sleep_quality, pollution_exposure, pollen_exposure, dust_exposure,
                pet_allergy, family_history_asthma, history_of_allergies, eczema, hay_fever,
                wheezing, shortness_of_breath, chest_tightness, coughing, nighttime_symptoms, 
                exercise_induced, obesity, cad_probability, cad, ragweed_pollen_allergy,
                grass_pollen_allergy, mugwort_pollen_allergy, birch_pollen_allergy, alder_pollen_allergy,
                olive_pollen_allergy, asthma_allergy, date_of_birth

            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
        """

        # If it does not have a UUID add it 
        if 'user_id' in user:
            user_id = user['user_id']
            values = tuple(user.values())
        else:
            # Generate a UUID
            user_id = uuid.uuid4()
            values = (user_id,) + tuple(user.values())

        self.session.execute(query, values)
        print(f"User {user_id} added successfully.")

       

    def shutdown(self):
        return self.cluster.shutdown()