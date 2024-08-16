import os
import json
import time
import numpy as np
import pandas as pd
from kafka import KafkaProducer
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()
# Access environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_TOPIC = os.getenv('WEREABLE_SIMULATOR_TOPIC')
REDIS_SERVER=os.getenv('REDIS_SERVER')
REDIS_PORT=os.getenv('REDIS_PORT')

# Configure the Kafka producer
try:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
        retries=5,
        request_timeout_ms=30000,
        metadata_max_age_ms=60000,
        linger_ms=1000,
    )

except Exception as e:
    print(f"Error connecting to Kafka: {e}")
    exit(1)


def generate_eda(length=1, baseline=0.5, noise_level=0.01, spike_prob=0.01):
    eda = np.ones(length) * baseline
    spikes = np.random.rand(length) < spike_prob
    eda[spikes] += np.random.rand(np.sum(spikes)) * 0.5
    eda += np.random.randn(length) * noise_level
    return eda

def generate_bvp(length=1, hr_mean=60, hr_std=1, noise_level=0.01):
    hr = np.random.normal(hr_mean, hr_std, length)
    ibi = 60 / hr
    bvp = np.sin(np.cumsum(ibi) * 2 * np.pi / ibi.mean())
    bvp += np.random.randn(length) * noise_level
    return bvp

def generate_acc(length=1, noise_level=0.01, burst_prob=0.01):
    acc = np.random.randn(length, 3) * noise_level
    bursts = np.random.rand(length) < burst_prob
    acc[bursts] += np.random.randn(np.sum(bursts), 3) * 10
    return acc

def generate_temp(length=1, baseline=33.0, noise_level=0.1):
    temp = np.ones(length) * baseline
    temp += np.cumsum(np.random.randn(length) * noise_level)
    return temp

def generate_hrv(length=1, baseline=60, noise_level=5):
    hr = baseline + np.random.randn(length) * noise_level
    ibi = 60 / hr
    hrv = np.std(ibi)
    return hrv

# http://bboxfinder.com/#45.708406,10.458984,47.026592,12.319336
def generate_gps_coordinates():
    # Generate random GPS coordinates within a specific range
    lat = np.random.uniform(45.7, 47)
    lng = np.random.uniform(10.5, 12)
    return lat, lng

def send_data_to_kafka(producer, topic, data):
    producer.send(topic, value=data)
    producer.flush()

lat, lng = generate_gps_coordinates()
lat, lng = 46.215179, 11.119681 # Mezzocorona

# Generate and send synthetic data in real time
while True:
    eda = generate_eda()[0]
    bvp = generate_bvp()[0]
    acc = generate_acc()[0]
    temp = generate_temp()[0]
    hrv = generate_hrv()

    data = {
        'EDA': eda,
        'BVP': bvp,
        'ACC_X': acc[0],
        'ACC_Y': acc[1],
        'ACC_Z': acc[2],
        'TEMP': temp,
        'HRV': hrv,
        "LAT": lat,
        "LNG": lng,
        "timestamp": time.time()
    }

    send_data_to_kafka(producer, KAFKA_TOPIC, data)

    print(f"Sent data to Kafka: {data}")

    time.sleep(1)  # Adjust the sleep time to control the data sending rate
