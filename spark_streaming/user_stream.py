from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, from_unixtime, col
from pyspark.sql.types import StructType, StructField, IntegerType, BooleanType, FloatType, StringType, DateType
from dotenv import load_dotenv
import time
import os

from kafka import KafkaAdminClient
from services.redis_client import RedisClient


# Load environment variables from .env file
load_dotenv()

# Access environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_SOURCE_TOPIC = os.getenv('USER_TOPIC')


def initialize_spark_connection():
    # Initialize Spark session
    spark = SparkSession.builder \
        .appName("AirQualityStream") \
        .master("local[*]") \
        .config("spark.jars.packages", 
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,"  # Kafka, Cassandra connector
                "com.datastax.spark:spark-cassandra-connector_2.12:3.0.0")  \
        .config("spark.cassandra.connection.host", "cassandra") \
        .config("spark.cassandra.connection.port", "9042") \
        .getOrCreate()
    #   .master("spark://localhost:7077") \

    # Set log level to WARN to reduce verbosity, avoiding log info in console
    spark.sparkContext.setLogLevel("ERROR")

    return spark

def check_topic_exists(topic_name, bootstrap_servers):
    admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
    topic_list = admin_client.list_topics()
    return topic_name in topic_list

def connect_to_kafka(spark):

    polling_interval = 5

    while not check_topic_exists(KAFKA_SOURCE_TOPIC, KAFKA_BOOTSTRAP_SERVERS):
        print(f"Topic {KAFKA_SOURCE_TOPIC} does not exist. Waiting...")
        time.sleep(polling_interval)


    spark_df = None

    # Read data from Kafka
    try:
        spark_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_SOURCE_TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    except Exception as e:
        print(f"kafka dataframe could not be created because: {e}")

    return spark_df

def parse_df(spark_df):

    schema = StructType([
        StructField("user_id", StringType(), False),          
        StructField("gender", BooleanType(), True),           
        StructField("education_level", IntegerType(), True),  
        StructField("bmi", FloatType(), True),                
        StructField("current_smoker", BooleanType(), True),   
        StructField("physical_activity", FloatType(), True),  
        StructField("diet_quality", FloatType(), True),      
        StructField("sleep_quality", FloatType(), True),     
        StructField("pollution_exposure", FloatType(), True), 
        StructField("pollen_exposure", FloatType(), True),    
        StructField("dust_exposure", FloatType(), True),      
        StructField("pet_allergy", BooleanType(), True),      
        StructField("family_history_asthma", BooleanType(), True),
        StructField("history_of_allergies", BooleanType(), True),
        StructField("eczema", BooleanType(), True),
        StructField("hay_fever", BooleanType(), True),
        StructField("wheezing", BooleanType(), True),
        StructField("shortness_of_breath", BooleanType(), True),
        StructField("chest_tightness", BooleanType(), True),
        StructField("coughing", BooleanType(), True),
        StructField("nighttime_symptoms", BooleanType(), True),
        StructField("exercise_induced", BooleanType(), True),
        StructField("obesity", BooleanType(), True),
        StructField("cad", BooleanType(), True),
        StructField("cad_probability", FloatType(), True),
        StructField("ragweed_pollen_allergy", BooleanType(), True),
        StructField("grass_pollen_allergy", BooleanType(), True),
        StructField("mugwort_pollen_allergy", BooleanType(), True),
        StructField("birch_pollen_allergy", BooleanType(), True),
        StructField("alder_pollen_allergy", BooleanType(), True),
        StructField("olive_pollen_allergy", BooleanType(), True),
        StructField("asthma_allergy", BooleanType(), True),
        StructField("date_of_birth", DateType(), True)       
    ])


    # Deserialize JSON messages
    parsed_df = spark_df.select(
        col("key").cast("string").alias("user_id"),
        from_json(col("value").cast("string"), schema).alias("parsed_value")
    )

    # Flatten the struct
    parsed_df = parsed_df.select("parsed_value.*")
    
    return parsed_df


def write_to_console(spark_df):
    # Output in console for debugging
    query = spark_df.writeStream \
        .outputMode("append") \
        .format("console") \
        .start()

    query.awaitTermination()


def write_to_cassandra(spark_df):
    # Write the data to Cassandra
    query = spark_df.writeStream \
        .format("org.apache.spark.sql.cassandra") \
        .option("keyspace", "bdt_keyspace") \
        .option("table", "users") \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/checkpoints/cassandra") \
        .start()

    return query

def main():

    # Get Spark Session
    spark = initialize_spark_connection()

    # Read data from Kafka
    spark_df = connect_to_kafka(spark)

    # Parsing
    parsed_df = parse_df(spark_df)

    # write_to_console(parsed_df)

    # Writing to cassandra
    cassandra_query = write_to_cassandra(parsed_df)

    # Await termination for both
    cassandra_query.awaitTermination()






if __name__ == "__main__":
    main()