import numpy as np
import pandas as pd
import json
import time
from kafka import KafkaProducer


TOPIC_NAME = 'wereable_simulator'
KAFKA_SERVER = '172.27.32.1:9092'

# Configure the Kafka producer
try:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_SERVER,  # Adjust if your Kafka server is running elsewhere
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
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


def send_data_to_kafka(producer, topic, data):
    producer.send(topic, value=data)
    producer.flush()

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
        'HRV': hrv
    }

    send_data_to_kafka(producer, TOPIC_NAME, data)
    print(f"Sent data to Kafka: {data}")

    time.sleep(1)  # Adjust the sleep time to control the data sending rate
