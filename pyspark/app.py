from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf
from pyspark.sql.types import StructType, StructField, StringType, FloatType
import redis

# Initialize Spark session
spark = SparkSession.builder \
    .appName("KafkaSparkConsumer") \
    .getOrCreate()

# Set log level to WARN to reduce verbosity, avoiding log info in console
spark.sparkContext.setLogLevel("WARN")

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
    StructField("LNG", FloatType(), True)
])

# Connect to Redis
def get_closest_municipality(lat, lng):
    r = redis.Redis(host='redis', port=6379, db=0)
    closest = r.georadius('municipalities', lng, lat, 10000, unit='km', withdist=True, count=1)
    if closest:
        municipality_id = closest[0][0].decode('utf-8')
        distance = closest[0][1]
        details = r.hgetall(municipality_id)
        return details
    else:
        return None

# Register UDF
@udf(returnType=StringType())
def closest_municipality(lat, lng):
    # here we should get the risk value associated with the locality instead of 
    result = get_closest_municipality(lat, lng)
    if result:
        return f"{result[b'name']}"
    else:
        return "No municipality found"

# Read data from Kafka
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka-1:19092,kafka-2:29092,kafka-3:39092") \
    .option("subscribe", "wereable_simulator") \
    .load()

# Deserialize JSON messages
value_df = df.select(from_json(col("value").cast("string"), schema).alias("parsed_value"))

closest = closest_municipality(col("parsed_value.LAT"), col("parsed_value.LNG")).alias("closest_municipality")

# Select the fields and add the closest municipality
result_df = value_df.select(
    "parsed_value.EDA",
    "parsed_value.BVP",
    "parsed_value.ACC_X",
    "parsed_value.ACC_Y",
    "parsed_value.ACC_Z",
    "parsed_value.TEMP",
    "parsed_value.HRV",
    "parsed_value.LAT",
    "parsed_value.LNG",
    closest
)

# Define a query that prints the results to the console
query = result_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

# Wait for the termination of the query
query.awaitTermination()
