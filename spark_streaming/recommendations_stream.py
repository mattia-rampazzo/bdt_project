from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, from_unixtime, col, avg, expr, udf, window, first, count, mean
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, DoubleType, ArrayType, StringType
from dotenv import load_dotenv
import uuid
import time
import os
from datetime import date

from kafka import KafkaAdminClient

from services.redis_client import RedisClient
from services.cassandra_client import CassandraClient

from spark_streaming.utils.recommendation import process_data


# Load environment variables from .env file
load_dotenv()

# Access environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_SOURCE_TOPIC = os.getenv('WEREABLE_SIMULATOR_TOPIC')
KAFKA_SINK_TOPIC = os.getenv('HEALTH_RECOMMENDATIONS_TOPIC')
REDIS_SERVER=os.getenv('REDIS_SERVER')
REDIS_PORT=os.getenv('REDIS_PORT')



def initialize_spark_connection():
    # Initialize Spark session
    spark = SparkSession.builder \
        .appName("BigData") \
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
        StructField("heart_rate", FloatType(), True),
        StructField("ibi", FloatType(), True),
        StructField("eda", FloatType(), True),
        StructField("skin_temp", FloatType(), True),
        StructField("activity_level", FloatType(), True),
        StructField("id", StringType(), True),
        StructField("lat", FloatType(), True),
        StructField("lng", FloatType(), True),
        StructField("timestamp", DoubleType(), True)
    ])

    # Deserialize JSON messages
    parsed_df = spark_df.select(from_json(col("value").cast("string"), schema).alias("parsed_value"))
    # Flatten the struct
    parsed_df = parsed_df.select("parsed_value.*")
    # Parse unix to Spark timestamp
    parsed_df = parsed_df.withColumn("timestamp", from_unixtime(col("timestamp")).cast("timestamp"))

    return parsed_df

def get_user_profile(user_id):

    # Get user from Cassandra
    cassandra = CassandraClient()
    user_data = cassandra.get_user(uuid.UUID(user_id))
    cassandra.shutdown()
    
    return user_data

def write_to_console(spark_df):
    # Output in console for debugging
    query = spark_df.writeStream \
        .outputMode("complete") \
        .format("console") \
        .trigger(processingTime="1 minutes") \
        .start()

    query.awaitTermination()

def write_to_kafka(spark_df):
    query = spark_df.writeStream \
    .outputMode("complete") \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("topic", KAFKA_SINK_TOPIC) \
    .option("checkpointLocation", "/pyspark/checkpoint/") \
    .trigger(processingTime="1 minutes") \
    .start()

    query.awaitTermination()

# def generate_recommendations(user_data, environmental_data, avg_heart_rate, avg_eda, avg_skin_temp, avg_activity_levels):

#     recommendations = []

#     # print(f"User name: {user_data['username']}" )    
#     # print(f"Pollen levels: {municipality_data['grass_pollen']}")
    
#     # Heart Rate: Recommend action if heart rate exceeds 100 bpm.
#     # EDA (Stress): Suggest stress management if EDA exceeds 10 µS.
#     # Skin Temperature: Advise checking for fever if temperature exceeds 37°C.

#     # Recommendations based only on wearable data
#     if avg_eda > 10:
#         recommendations.append("Your stress levels seem high. Consider taking a break and practicing relaxation techniques.")

#     if avg_heart_rate > 100:
#         recommendations.append("Heart Rate: Recommend action if heart rate exceeds 100 bpm.")
    
#     if avg_skin_temp > 37.5:
#         recommendations.append("Your body temperature is higher than normal. Monitor for symptoms of illness and consider consulting a healthcare provider.")

#     # Recommendations based on wearable data and pollen levels
#     # if user_profile.get('birch_pollen') is not None and birch_pollen > 0:
#     #     recommendations.append("Birch pollen levels are high. Consider staying indoors and taking preventive measures.")
#     # if user_profile.get('ragweed_pollen') is not None and ragweed_pollen > 0:
#     #     recommendations.append("Ragweed pollen levels are high. Consider staying indoors and taking preventive measures.")
#     # if user_profile.get('grass_pollen') is not None and grass_pollen > 0:
#     #     recommendations.append("Grass pollen levels are high. Consider staying indoors and taking preventive measures.")
#     recommendations.append(f"User has allergy: {user_data['grass_pollen_allergy']}, Grass pollen : {environmental_data['grass_pollen']}" )

#     return recommendations


# Register UDF
@udf(returnType=ArrayType(StringType()))
def get_recommendations(user_id, lat, lng, avg_heart_rate, avg_ibi, avg_eda, avg_skin_temp, avg_activity_level):

    # Initialize Redis connection
    r = RedisClient()

    # Look in Redis for data we need
    municipality_id = r.get_closest_municipality(lng, lat, 10000)
    environmental_data = r.hgetall(municipality_id)
    user_data = r.get(f'user:{user_id}')
    

    if not user_data:
        # Look in Cassandra
        user_data = get_user_profile(user_id)
        # json.dumps dont work with UUI and Date
        user_data["user_id"] = user_id 
        # if isinstance(user_data.get("date_of_birth"), date):
        user_data["date_of_birth"] = str(user_data["date_of_birth"])
        # print(user_data["date_of_birth"])
        # Store in Redis
        r.set(f'user:{user_id}', user_data)

    # Close Connection
    r.close()

    data = process_data(user_data, environmental_data, avg_heart_rate, avg_ibi, avg_eda, avg_skin_temp, avg_activity_level)

    # print(data)

    return data['recommendations']



def main():

    # Get Spark Session
    spark = initialize_spark_connection()

    # Read data from Kafka
    spark_df = connect_to_kafka(spark)

    # Parsing
    parsed_df = parse_df(spark_df)

    # Group by 1 minute windows
    # watermaeking of only 1 seconds because it doesnt make much sense to update results that arrive toolate
    windowed_df = parsed_df \
        .withWatermark("timestamp", "0  seconds") \
        .groupBy(
            window(col("timestamp"), "1 minutes")  # Time window of 30 seconds
        ) \
        .agg(
            first("id").alias("id"),
            first("lat").alias("lat"),
            first("lng").alias("lng"),
            mean("heart_rate").alias("avg_heart_rate"),
            mean("ibi").alias("avg_ibi"),
            mean("eda").alias("avg_eda"),
            mean("skin_temp").alias("avg_skin_temp"),
            mean("activity_level").alias("avg_activity_level"),
            count(expr("*")).alias("count")
        )

    # Finally get live recommendations
    recommendations_df = windowed_df.withColumn("recommendations", get_recommendations(col("id"), col("lat"), col("lng"), col("avg_heart_rate"),col("avg_ibi"), col("avg_eda"), col("avg_skin_temp"), col("avg_activity_level") )).select("window", "recommendations", "count")
    
    # Prepare the DataFrame with 'key' and 'value' columns for Kafka
    out_df = recommendations_df.selectExpr(
        "CAST(unix_timestamp(window.end) AS STRING) AS key",
        "CAST(recommendations AS STRING) AS value"
    )

    # Write the key-value pairs to the Kafka topic
    write_to_kafka(out_df)

    # write_to_console(out_df)


if __name__ == "__main__":
    main()