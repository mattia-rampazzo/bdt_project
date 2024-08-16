from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, from_unixtime, col, mean, expr, udf, window, first, count
from pyspark.sql.types import StructType, StructField, StringType, FloatType, DoubleType, MapType, ArrayType
from dotenv import load_dotenv
import redis
import os

from kafka import KafkaAdminClient
import time

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


def get_pollen_levels(redis, municipality_id):
    if municipality_id:
        # return {"Birch": 12.5, "Oak": 15.3, "Ragweed": 8.9, "Grass": 5.0}
        data =  redis.hgetall(municipality_id)

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

# Register UDF
@udf(returnType=MapType(StringType(), FloatType()))
def fetch_pollen_levels(lat, lng):

    # Each worker initialize its redis connection
    redis = initialize_redis_connection()

    # here we should get the risk value associated with the locality instead of 
    municipality_id = get_closest_municipality_id(redis, lat, lng)

    pollen_levels = get_pollen_levels(redis, municipality_id)

    if pollen_levels:
        return pollen_levels
    else:
        return "No data found"
    


# Register UDF
@udf(returnType=ArrayType(StringType()))
def generate_recommendations(pollen_levels):

    # Example user profile
    user_profile = {
        'gender': 'Male',
        'age': 30,
        'Height_cm': 175,
        'Weight_kg': 70,
        'bmi': 22.9,
        'hypertension': 0,
        'heart_disease': 0,
        'ever_married': 'Yes',
        'work_type': 'Private',
        'Residence_type': 'Urban',
        'stroke': 0,
        'Current Smoker': 0,
        'EX-Smoker': 0,
        'Obesity': 0,
        'Cad': 0,
        'Hay Fever': 1,
        'Asthma': 0,
        'Birch Pollen': 1,
        'Ragweed Pollen': 0,
        'Grass Pollen': 1,
        'Oak Pollen': 0,
        'Cedar Pollen': 0,
        'Maple Pollen': 0,
        'Pine Pollen': 0,
        'Nettle Pollen': 0
    }

    recommendations = []

    # Extract wearable data and pollen levels from the dictionary
    eda_mean = pollen_levels.get('eda_mean', 0.0)
    acc_mean = pollen_levels.get('acc_mean', 0.0)
    temp_mean = pollen_levels.get('temp_mean', 0.0)
    hrv_mean = pollen_levels.get('hrv_mean', 0.0)
    
    birch_pollen = pollen_levels.get('Birch Pollen', 0.0)
    ragweed_pollen = pollen_levels.get('Ragweed Pollen', 0.0)
    grass_pollen = pollen_levels.get('Grass Pollen', 0.0)

    # Recommendations based only on wearable data
    if eda_mean > 0.6:
        recommendations.append("Your stress levels seem high. Consider taking a break and practicing relaxation techniques.")
    if acc_mean < 0.1:
        recommendations.append("You have been inactive for a while. Consider going for a short walk or doing some exercises.")
    if temp_mean > 37.5:
        recommendations.append("Your body temperature is higher than normal. Monitor for symptoms of illness and consider consulting a healthcare provider.")
    if hrv_mean < 30:
        recommendations.append("Your heart rate variability is low. Engage in activities that improve cardiovascular health such as regular exercise, adequate sleep, and stress management.")
    
    # Recommendations based on wearable data and pollen levels
    if birch_pollen > 3 and user_profile['Birch Pollen']:
        recommendations.append("Birch pollen levels are high. Consider staying indoors and taking preventive measures.")
    if ragweed_pollen > 3 and user_profile['Ragweed Pollen']:
        recommendations.append("Ragweed pollen levels are high. Consider staying indoors and taking preventive measures.")
    if grass_pollen > 3 and user_profile['Grass Pollen']:
        recommendations.append("Grass pollen levels are high. Consider staying indoors and taking preventive measures.")
    
    return recommendations

def check_topic_exists(topic_name, bootstrap_servers):
    admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
    topic_list = admin_client.list_topics()
    return topic_name in topic_list

def main():

    # Define schema for the JSON data
    schema = StructType([
        StructField("EDA", FloatType(), True),
        StructField("BVP", FloatType(), True),
        StructField("ACC_X", FloatType(), True),
        StructField("ACC_Y", FloatType(), True),
        StructField("ACC_Z", FloatType(), True),
        StructField("TEMP", FloatType(), True),
        StructField("HRV", FloatType(), True),
        StructField("LAT", FloatType(), True),
        StructField("LNG", FloatType(), True),
        StructField("timestamp", DoubleType(), True)
    ])

    # Get Spark Session
    spark = initialize_spark_connection()

    polling_interval = 5

    while not check_topic_exists(KAFKA_TOPIC, KAFKA_BOOTSTRAP_SERVERS):
        print(f"Topic {KAFKA_TOPIC} does not exist. Waiting...")
        time.sleep(polling_interval)

    # Read data from Kafka
    kafka_df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .load()

    # Deserialize JSON messages
    parsed_df = kafka_df.select(from_json(col("value").cast("string"), schema).alias("parsed_value"))
    # Flatten the struct
    parsed_df = parsed_df.select("parsed_value.*")
    # Parse unix to Spark timestamp
    parsed_df = parsed_df.withColumn("timestamp", from_unixtime(col("timestamp")).cast("timestamp"))

    # Group by 1 minute windows + 30 second sliding
    # watermaeking of only 30 seconds because it doesnt make much sense to update results that arrive toolate
    windowed_df = parsed_df \
        .withWatermark("timestamp", "1 seconds") \
        .groupBy(window(col("timestamp"), "30 seconds")) \
        .agg(
            first("LAT").alias("LAT"),
            first("LNG").alias("LNG"),
            mean("EDA").alias("EDA_mean"),
            expr("sqrt(avg(ACC_X * ACC_X + ACC_Y * ACC_Y + ACC_Z * ACC_Z))").alias("ACC_magnitude_mean"),
            mean("TEMP").alias("TEMP_mean"),
            mean("HRV").alias("HRV_mean"),
            count(expr("*")).alias("count")
        ) 

    # Add pollen level
    windowed_df = windowed_df.withColumn("pollen_levels", fetch_pollen_levels(col("LAT"), col("LNG"))).drop("LAT", "LNG")

    # Finally get live recommendations
    recommendations_df = windowed_df.withColumn("recommendation", generate_recommendations(col("pollen_levels"))).select("window", "recommendation", "count")
    
    # Prepare the DataFrame with 'key' and 'value' columns for Kafka
    out_df = recommendations_df.selectExpr(
        "CAST(unix_timestamp(window.end) AS STRING) AS key",
        "CAST(count AS STRING) AS value"
    )

    # Write the key-value pairs to the Kafka topic
    query = out_df.writeStream \
    .outputMode("append") \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("topic", HEALTH_RECOMMENDATIONS_TOPIC) \
    .option("checkpointLocation", "/pyspark/checkpoint/") \
    .trigger(processingTime="30 seconds") \
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