import os
import time
import json
import pandas as pd

import openmeteo_requests
import requests_cache
from retry_requests import retry
from dotenv import load_dotenv

from services.redis_client import RedisClient
from services.kafka_client import KafkaProducerWrapper, KafkaConsumerWrapper


SIMULATION_TIME = "2024-06-01T14:00"


def update_redis(r, data):
    # Insert data into Redis
    for key, values in data.items():
        for field, value in values.items():
            r.hset(f"municipality:{key}", field, value)

def send_to_kafka(kafka, topic, aqi_data):
    payload = {'type': 'aqi_update', 'data': aqi_data}
    value=json.dumps(payload).encode('utf-8')
    kafka.produce_data(topic, value)

# merge the two datasets
def combine_aqi_temperature_data(aqi_data, temperature_data):

    data = aqi_data
    for key in data:
        data[key].update(temperature_data[key])

    return data

def api_call(df_mun, url, weather_variables):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)


    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    # url = f"https://air-quality-api.open-meteo.com/v1/{endpoint}"


    municipality_id = df_mun["istat"].to_list()
    name = df_mun["comune"].to_list()
    latitude = df_mun["lat"].to_list()
    longitude = df_mun["lng"].to_list()

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": weather_variables,
        "start_hour": SIMULATION_TIME,
        "end_hour": SIMULATION_TIME,
        "timezone": "Europe/Berlin"
    }
    responses = openmeteo.weather_api(url, params=params)
    
    # # Process first location. Add a for-loop for multiple locations or weather models
    # response = responses[0]
    # print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    # print(f"Elevation {response.Elevation()} m asl")
    # print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    # print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # # Process hourly data. The order of variables needs to be the same as requested.
    # hourly = response.Hourly()

    # hourly_data = {"date": pd.date_range(
    #     start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
    #     end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
    #     freq = pd.Timedelta(seconds = hourly.Interval()),
    #     inclusive = "left"
    # )}

    # for j, variable in enumerate(weather_variables):
    #     hourly_data[variable] = hourly.Variables(j).ValuesAsNumpy()

    # hourly_dataframe = pd.DataFrame(data = hourly_data)
    # print(hourly_dataframe)


    data = dict()
    for i, response in enumerate(responses):

        # Process hourly data. The order of variables needs to be the same as requested.
        # In this case its only 1 hour since its simulate current
        hourly = response.Hourly()
        #current = response.Current()

        mun_weather_data = dict()
        # id, name latitude, longitude
        mun_weather_data["municipality_id"] = municipality_id[i]
        mun_weather_data["name"] = name[i]
        mun_weather_data["latitude"] = latitude[i]
        mun_weather_data["longitude"] = longitude[i]
        # add weather variables
        for j, variable in enumerate(weather_variables):
            mun_weather_data[variable] = hourly.Variables(j).Values(0)
        # insert in dict
        data[municipality_id[i]] = mun_weather_data


    return data

def fetch_data(df_mun):
    # Variables we are interested in
    pollen_variables = ["alder_pollen", "birch_pollen", "grass_pollen", "mugwort_pollen", "olive_pollen", "ragweed_pollen"]
    weather_variables = ["temperature_2m"]

    split_size = 150 # we want at most 150 locations for each API call
    aqi_data = dict()
    temperature_data = dict()

    num_splits = len(df_mun) // split_size + (1 if len(df_mun) % split_size != 0 else 0)
    
    for i in range(num_splits):
        split_df = df_mun.iloc[i * split_size:(i + 1) * split_size]

        # unfortunately two API calls to retrieve all the data
        aqi_data.update(api_call(split_df, "https://air-quality-api.open-meteo.com/v1/air-quality", pollen_variables))
        temperature_data.update(api_call(split_df, "https://api.open-meteo.com/v1/forecast", weather_variables))


    data = combine_aqi_temperature_data(aqi_data, temperature_data)
    return data
    


def main():

    # time.sleep(30)  # Wait for 30 seconds before executing

    # Load municipalities data: ['istat', 'comune', 'lng', 'lat']
    df_mun = pd.read_csv(os.path.join("..", "data", "Trentino-AltoAdige_municipalities.csv"))
    # decomment to not waste too many apis
    # df_mun = df_mun.head(150) # 150 li tiene, di piu difficile, lurl dell api troppo grosso...

    # Setup redis and kafka
    r = RedisClient()
    kafka = KafkaProducerWrapper()

    while True:
        try:
            print("Fetching data...")
            data = fetch_data(df_mun)
            print("Done")
        except Exception as e:
            print(f"Error fetching data: {e}")
        
        try:
            print("Updating Redis...")
            update_redis(r, data)
            print("Done")
            print("Sending to Kafka...")
            send_to_kafka(kafka, 'a', data)
            print("Done...")
        except Exception as e:
            print(f"Error updating data: {e}")

        time.sleep(3600)  # Wait for 1 hour before next fetch

if __name__ == "__main__":
    main()