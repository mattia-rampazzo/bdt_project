import os
import redis
import time
import json
import pandas as pd
from kafka import KafkaProducer

import openmeteo_requests
import requests_cache
from retry_requests import retry

from dotenv import load_dotenv

# Assuming df_mun is the DataFrame read from "trentino_munic.json"
df_mun = pd.read_json(os.path.join("data", "trentino_municipalities.json"))
# decomment to not waste too many apis
df_mun = df_mun.head(150) # 150 li tiene, di piu difficile, lurl dell api troppo grosso...


# Load environment variables from .env file
load_dotenv()
# Access environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_TOPIC = os.getenv('OPEN_METEO_TOPIC')
REDIS_SERVER=os.getenv('REDIS_SERVER')
REDIS_PORT=os.getenv('REDIS_PORT')




def combine_aqi_temperature_data(aqi_data, temperature_data):

    data = aqi_data
    for key in data:
        data[key].update(temperature_data[key])

    return data

# unfortunately another API call because temperature is on another endpoint
def fetch_temperature_data():
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)


    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"

    municipality_id = df_mun["istat"].to_list()
    name = df_mun["comune"].to_list()
    latitude = df_mun["lat"].to_list()
    longitude = df_mun["lng"].to_list()

    weather_variables = ["temperature_2m"]
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": weather_variables,
        "timezone": "Europe/Berlin"
    }
    responses = openmeteo.weather_api(url, params=params)

    data = dict()
    for i, response in enumerate(responses):

        # Current values. The order of variables needs to be the same as requested.
        current = response.Current()

        mun_weather_data = dict()
        # id, name latitude, longitude
        mun_weather_data["municipality_id"] = municipality_id[i]
        mun_weather_data["name"] = name[i]
        mun_weather_data["latitude"] = latitude[i]
        mun_weather_data["longitude"] = longitude[i]
        # add weather variables
        for j, variable in enumerate(weather_variables):
            mun_weather_data[variable] = current.Variables(j).Value()
        # insert in dict
        data[municipality_id[i]] = mun_weather_data

    return data

def fetch_aqi_data():
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)


    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"

    municipality_id = df_mun["istat"].to_list()
    name = df_mun["comune"].to_list()
    latitude = df_mun["lat"].to_list()
    longitude = df_mun["lng"].to_list()

    weather_variables = ["european_aqi", "us_aqi", "pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone", "aerosol_optical_depth", "dust", "uv_index", "uv_index_clear_sky", "ammonia", "alder_pollen", "birch_pollen", "grass_pollen", "mugwort_pollen", "olive_pollen", "ragweed_pollen"]
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": weather_variables,
        "timezone": "Europe/Berlin"
    }
    responses = openmeteo.weather_api(url, params=params)

    data = dict()
    for i, response in enumerate(responses):

        # Current values. The order of variables needs to be the same as requested.
        current = response.Current()

        mun_weather_data = dict()
        # id, name latitude, longitude
        mun_weather_data["municipality_id"] = municipality_id[i]
        mun_weather_data["name"] = name[i]
        mun_weather_data["latitude"] = latitude[i]
        mun_weather_data["longitude"] = longitude[i]
        # add weather variables
        for j, variable in enumerate(weather_variables):
            mun_weather_data[variable] = current.Variables(j).Value()
        # insert in dict
        data[municipality_id[i]] = mun_weather_data

    return data

def update_redis(redis_client, data):
    # Insert data into Redis
    for key, values in data.items():
        for field, value in values.items():
            redis_client.hset(f"municipality:{key}", field, value)

def notify_kafka(producer, topic, aqi_data):
    notification = {'type': 'aqi_update', 'data': aqi_data}
    producer.send(topic, notification)
    producer.flush()


def main():
    redis_client = redis.Redis(host=REDIS_SERVER, port=REDIS_PORT, db=0)
    kafka_producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    while True:
        try:
            aqi_data = fetch_aqi_data()
            temperature_data = fetch_temperature_data()
            data = combine_aqi_temperature_data(aqi_data, temperature_data)
            # print(data)
            update_redis(redis_client, data)
            print("done")
            notify_kafka(kafka_producer, KAFKA_TOPIC, data)
        except Exception as e:
            print(f"Error fetching/updating data: {e}")
        time.sleep(3600)  # Wait for 1 hour before next fetch

if __name__ == "__main__":
    main()