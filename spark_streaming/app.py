from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, from_unixtime, col, avg, expr, udf, window, first, count, mean
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, DoubleType, ArrayType, StringType
from dotenv import load_dotenv
import redis
import json
import os
import uuid

from kafka import KafkaAdminClient
import time

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, dict_factory


# Load environment variables from .env file
load_dotenv()

# Access environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_TOPIC = os.getenv('WEREABLE_SIMULATOR_TOPIC')
HEALTH_RECOMMENDATIONS_TOPIC = os.getenv('HEALTH_RECOMMENDATIONS_TOPIC')
REDIS_SERVER=os.getenv('REDIS_SERVER')
REDIS_PORT=os.getenv('REDIS_PORT')



def initialize_spark_connection():
    # Initialize Spark session
    spark =  SparkSession.builder \
        .appName("BigData") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0") \
        .getOrCreate()
    #   .master("spark://localhost:7077") \

    # Set log level to WARN to reduce verbosity, avoiding log info in console
    spark.sparkContext.setLogLevel("WARN")

    return spark

def initialize_redis_connection():
    # Initialize Redis
    return redis.Redis(host=REDIS_SERVER, port=REDIS_PORT, db=0)

def initialize_cassandra_connection():

    cluster = Cluster(['cassandra'])

    session = cluster.connect('bdt_keyspace')

    # Set the row factory to return rows as dictionaries
    session.row_factory = dict_factory

    return session


def check_topic_exists(topic_name, bootstrap_servers):
    admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
    topic_list = admin_client.list_topics()
    return topic_name in topic_list

def connect_to_kafka(spark):

    polling_interval = 5

    while not check_topic_exists(KAFKA_TOPIC, KAFKA_BOOTSTRAP_SERVERS):
        print(f"Topic {KAFKA_TOPIC} does not exist. Waiting...")
        time.sleep(polling_interval)


    spark_df = None

    # Read data from Kafka
    try:
        spark_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPIC) \
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


def get_user_from_cache(r, user_id):

    user_profile = r.get(f'user:{user_id}')
    
    if user_profile is None:
        # Handle the case where no data is found
        print("No data found for the given user_id.")
        return
    
    # Decode byte data to string
    user_profile = user_profile.decode('utf-8')

    return json.loads(user_profile)


def get_user_from_db(cassandra, user_id):
    #uid = "7fb5c3da-0099-4516-8062-9e2e426487c1"
    try:
        # Create a parameterized query to prevent SQL injection
        query = SimpleStatement("""
            SELECT * 
            FROM users 
            WHERE user_id = %s
        """)
        
        # Execute the query with the UUID parameter
        result = cassandra.execute(query, (uuid.UUID("c6155cd0-d865-4265-af3a-dfb1102c1067"),))
        
        # Fetch and return the result
        return result.one()
    
    except Exception as e:
        # Handle any exceptions (e.g., connection issues, query errors)
        print(f"An error occurred: {e}")
        return None


def get_user_profile(r, cassandra, user_id):
    
    user_data = get_user_from_cache(r, user_id)

    if not user_data:
        user_data = get_user_from_db(cassandra, user_id)
        
        # Store in Redis
        user_data["user_id"] = user_id # json.dumps dont work with UUI
        r.set(f'user:{user_id}', json.dumps(user_data))
    
    return user_data

def get_pollen_levels(r, municipality_id):
    if municipality_id:
        
        data =  r.hgetall(municipality_id)

        pollen_keys = {
            'alder_pollen', 
            'birch_pollen', 
            'grass_pollen', 
            'mugwort_pollen', 
            'olive_pollen', 
            'ragweed_pollen', 
            'temperature_2m'
        }

        # Decode keys and values from bytes to strings
        data = {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items() if k.decode('utf-8') in pollen_keys}
            
        return data

def get_closest_municipality_id(redis, lat, lng):
    closest = redis.georadius('municipalities', lng, lat, 10000, unit='km', withdist=True, count=1)
    if closest:
        municipality_id = closest[0][0].decode('utf-8')
        # distance = closest[0][1]
        return municipality_id
    else:
        return None    


def generate_recommendations(user_profile, pollen_levels, avg_heart_rate, avg_eda, avg_skin_temp, avg_activity_levels):

    recommendations = []
    # recommendations.append(user_profile["first_name"])
    
    birch_pollen = float(pollen_levels.get('birch_pollen', 0.0))
    ragweed_pollen = float(pollen_levels.get('ragweed_pollen', 0.0))
    grass_pollen = float(pollen_levels.get('grass_pollen', 0.0))


    # Heart Rate: Recommend action if heart rate exceeds 100 bpm.
    # EDA (Stress): Suggest stress management if EDA exceeds 10 µS.
    # Skin Temperature: Advise checking for fever if temperature exceeds 37°C.

    # Recommendations based only on wearable data
    if avg_eda > 10:
        recommendations.append("Your stress levels seem high. Consider taking a break and practicing relaxation techniques.")

    if avg_heart_rate > 100:
        recommendations.append("Heart Rate: Recommend action if heart rate exceeds 100 bpm.")
    
    if avg_skin_temp > 37.5:
        recommendations.append("Your body temperature is higher than normal. Monitor for symptoms of illness and consider consulting a healthcare provider.")

    # Recommendations based on wearable data and pollen levels
    # if user_profile.get('birch_pollen') is not None and birch_pollen > 0:
    #     recommendations.append("Birch pollen levels are high. Consider staying indoors and taking preventive measures.")
    # if user_profile.get('ragweed_pollen') is not None and ragweed_pollen > 0:
    #     recommendations.append("Ragweed pollen levels are high. Consider staying indoors and taking preventive measures.")
    # if user_profile.get('grass_pollen') is not None and grass_pollen > 0:
    #     recommendations.append("Grass pollen levels are high. Consider staying indoors and taking preventive measures.")
    
    return recommendations


# Register UDF
@udf(returnType=ArrayType(StringType()))
def get_recommendations(user_id, lat, lng, avg_heart_rate, avg_eda, avg_skin_temp, avg_activity_level):

    # Each worker initialize its redism cassandra connection
    r = initialize_redis_connection()
    cassandra = initialize_cassandra_connection()

    # here we should get the risk value associated with the locality instead of 
    municipality_id = get_closest_municipality_id(r, lat, lng)

    pollen_levels = get_pollen_levels(r, municipality_id)

    user_profile = get_user_profile(r, cassandra, user_id)

    recommendations = generate_recommendations(user_profile, pollen_levels, avg_heart_rate, avg_eda, avg_skin_temp, avg_activity_level)

    return recommendations



def main():

    # Get Spark Session
    spark = initialize_spark_connection()

    # Read data from Kafka
    spark_df = connect_to_kafka(spark)

    # Parsing
    parsed_df = parse_df(spark_df)


    
    # Group by 1 minute windows + 30 second sliding
    # watermaeking of only 30 seconds because it doesnt make much sense to update results that arrive toolate
    windowed_df = parsed_df \
        .withWatermark("timestamp", "1  seconds") \
        .groupBy(
            window(col("timestamp"), "1 minutes")  # Time window of 30 seconds
        ) \
        .agg(
            first("id").alias("id"), # should be in agg but whatever
            first("lat").alias("lat"),
            first("lng").alias("lng"),
            mean("heart_rate").alias("avg_heart_rate"),
            mean("eda").alias("avg_eda"),
            mean("skin_temp").alias("avg_skin_temp"),
            mean("activity_level").alias("avg_activity_level"),
            count(expr("*")).alias("count")
        ) 

    # windowed_df.writeStream \
    # .outputMode("append") \
    # .format("console") \
    # .option("truncate", "false") \
    # .trigger(processingTime="30 seconds") \
    # .start() \
    # .awaitTermination()

    # Add pollen level
    # windowed_df = windowed_df.withColumn("pollen_levels", fetch_pollen_levels().drop("LAT", "LNG")

    # Finally get live recommendations
    recommendations_df = windowed_df.withColumn("recommendations", get_recommendations(col("id"), col("lat"), col("lng"), col("avg_heart_rate"), col("avg_eda"), col("avg_skin_temp"), col("avg_activity_level") )).select("window", "recommendations", "count")
    
    # Prepare the DataFrame with 'key' and 'value' columns for Kafka
    out_df = recommendations_df.selectExpr(
        "CAST(unix_timestamp(window.end) AS STRING) AS key",
        "CAST(recommendations AS STRING) AS value"
    )

    # Write the key-value pairs to the Kafka topic
    query = out_df.writeStream \
    .outputMode("append") \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("topic", HEALTH_RECOMMENDATIONS_TOPIC) \
    .option("checkpointLocation", "/pyspark/checkpoint/") \
    .trigger(processingTime="1 minutes") \
    .start()

    query.awaitTermination()


    # Output in console
    # output_query = recommendations_df.writeStream \
    #     .outputMode("update") \
    #     .format("console") \
    #     .start()

    # output_query.awaitTermination()


if __name__ == "__main__":
    main()