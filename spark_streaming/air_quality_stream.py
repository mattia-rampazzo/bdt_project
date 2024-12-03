from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, from_unixtime, col
from pyspark.sql.types import StructType, StructField, IntegerType, DoubleType, StringType
from dotenv import load_dotenv
import time
import os

from kafka import KafkaAdminClient
from services.redis_client import RedisClient


# Load environment variables from .env file
load_dotenv()

# Access environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_SOURCE_TOPIC = os.getenv('AIR_QUALITY_TOPIC')


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

    # Define the schema of the incoming data
    schema = StructType([
        StructField("municipality_id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("alder_pollen", DoubleType(), True),
        StructField("birch_pollen", DoubleType(), True),
        StructField("grass_pollen", DoubleType(), True),
        StructField("mugwort_pollen", DoubleType(), True),
        StructField("olive_pollen", DoubleType(), True),
        StructField("ragweed_pollen", DoubleType(), True),
        StructField("temperature_2m", DoubleType(), True),
        StructField("timestamp", DoubleType(), True)
    ])

    # Deserialize JSON messages
    parsed_df = spark_df.select(
        col("key").cast("string").alias("municipality_id"),
        from_json(col("value").cast("string"), schema).alias("parsed_value")
    )

    # Flatten the struct
    parsed_df = parsed_df.select("parsed_value.*")

    # Parse unix to Spark timestamp
    parsed_df = parsed_df.withColumn("timestamp", from_unixtime(col("timestamp")).cast("timestamp"))

    # Add year for Cassandra buckets
    parsed_df = parsed_df.withColumn("year", col("timestamp").cast("date").substr(1, 4))

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
        .option("table", "municipality_air_quality_data") \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/checkpoints/cassandra") \
        .start()

    return query


def write_batch_to_redis(batch_df, batch_id):
    # Connect to Redis
    redis = RedisClient()

    # Write each row to Redis
    for row in batch_df.collect():
        key = f"municipality:{row.municipality_id}"
        value = {
            "timestamp": row.timestamp.isoformat(),
            "name": row.name,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "alder_pollen": row.alder_pollen,
            "birch_pollen": row.birch_pollen,
            "grass_pollen": row.grass_pollen,
            "mugwort_pollen": row.mugwort_pollen,
            "olive_pollen": row.olive_pollen,
            "ragweed_pollen": row.ragweed_pollen,
            "temperature_2m": row.temperature_2m
        }
        # Store the data as a Redis hash
        redis.hset(key, value)
    
    # Close connection
    redis.close()


def write_to_redis(spark_df):

    query = spark_df.writeStream \
        .foreachBatch(write_batch_to_redis) \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/checkpoints/redis") \
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

    # Writing to redis
    redis_query = write_to_redis(parsed_df)

    # Await termination for both
    cassandra_query.awaitTermination()
    redis_query.awaitTermination()






if __name__ == "__main__":
    main()