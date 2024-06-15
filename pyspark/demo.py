from pyspark.sql import SparkSession
from pyspark.sql.functions import *

if __name__ == "__main__":
    import os
    print(os.getcwd())
    spark = SparkSession \
        .builder \
        .appName("Demo") \
        .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem") \
        .getOrCreate()

    flight_time_df1 = spark.read.json("data/d1/")
    flight_time_df2 = spark.read.json("data/d2/")

    join_df = flight_time_df1.join(broadcast(flight_time_df2), "id", "inner") \
        .hint("COALESCE", 5)

    join_df.show()
    print("Number of Output Partitions:" + str(join_df.rdd.getNumPartitions()))

    spark.stop()
