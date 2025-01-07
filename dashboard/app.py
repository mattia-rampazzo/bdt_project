import os
import json
import time
from threading import Lock, Event
from flask import Flask, render_template
from flask_socketio import SocketIO

from services.kafka_client import KafkaProducerWrapper, KafkaConsumerWrapper
from dashboard.utils.wereable_simulator import WereableSimulator
from dashboard.utils.map_generator import generate_pollen_risk_map

import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Simulation params
USER_ID = os.getenv('USER_ID')
LAT = os.getenv('LAT')
LNG = os.getenv('LNG')

USER_ID = "f72f5a88-30bd-46ce-97ee-63ac7528155e"
# LAT = 46.215179
# LNG = 11.119681

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


# Wereable Simulator instance
ws = WereableSimulator(individual_id=USER_ID, lat=LAT, lng=LNG)
is_simulation_running = False

# Producer for wereable data
producer = KafkaProducerWrapper()


# Globals for Thread 1
thread1 = None
thread1_lock = Lock()
thread1_event = Event()

# Globals for Thread 2
thread2 = None
thread2_lock = Lock()
thread2_event = Event()



@socketio.on('disconnect')
def stop_background_kafka_consumers():
    global thread1, thread2

    # print('dISCONNECT TRIGGERED', file=sys.stdout)

    with thread1_lock:
        # print(thread1, file=sys.stdout)
        if thread1 is not None:
            thread1_event.clear()
            thread1.join()
            thread1 = None
    
    with thread2_lock:
        if thread2 is not None:
            thread2_event.clear()
            thread2.join()
            thread2 = None

    global is_simulation_running
    global ws

    is_simulation_running = False
    ws = WereableSimulator(individual_id=USER_ID, lat=LAT, lng=LNG)

@socketio.on('connect')
def start_background_kafka_consumers():
    # print('CONNECT TRIGGERED', file=sys.stdout)

    global thread1, thread2

    with thread1_lock:
        if thread1 is None or not thread1.is_alive():
            thread1_event.set()
            thread1 = socketio.start_background_task(kafka_map_consumer, thread1_event)

    with thread2_lock:
        if thread2 is None or not thread2.is_alive():
            thread2_event.set()
            thread2 = socketio.start_background_task(kafka_recommendations_consumer, thread2_event)

def kafka_map_consumer(event):

    consumer = KafkaConsumerWrapper()
    try:
        while event.is_set():
            # Poll every 30 seconds
            # In this application having data in real time not so important
            msg = consumer.poll(topic='a', timeout_ms=30*1000)
            if not msg:
                continue

            generate_pollen_risk_map()
            socketio.emit('updated_pollen_risk_map', {'message': 'Map updated'})

            # for partition, messages in msg.items():
            #     for message in messages:
            #         try:
            #             print(f"Received message: {message.value.decode('utf-8')}")
            #         except Exception as e:
            #             print(f"Error decoding message: {e}")
    finally:
        try:
            consumer.close()
        except Exception as e:
            print(f"Error closing Kafka consumer: {e}")
        finally:
            # with thread1_lock:
            event.clear()
            global thread1
            thread1 = None

def kafka_recommendations_consumer(event):
    
    consumer = KafkaConsumerWrapper()
    received = set()
    try:
        while event.is_set():
            
            msg = consumer.poll(topic='h', timeout_ms=1000)
            if not msg:
                continue
            
            for partition, messages in msg.items():
                for message in messages:
                    try:
                        timestamp = int(message.key.decode('utf-8')) if message.key else 0
                        if(timestamp not in received):
                            received.add(timestamp)

                            decoded_value = message.value.decode('utf-8')
                            recommendations = decoded_value.strip('[]').split(', ')

                            socketio.emit('new_recommendation', {"timestamp": timestamp, "recommendations": recommendations})
                    except Exception as e:
                        print(f"Error processing message: {e}")
    finally:
        try:
            consumer.close()
        except Exception as e:
            print(f"Error closing Kafka consumer: {e}")
        finally:
            # with thread2_lock:
            event.clear()
            global thread2
            thread2 = None




# Deliver HTML
@app.route('/')
def index():
    return render_template('dashboard.html')


# When user clicks on start_simulation (Start) button
@socketio.on('start_simulation')
def start_simulation():
    # print('START SIMULATION', file=sys.stdout)
    global is_simulation_running
    is_simulation_running = True

    # Simulate wereable data
    while is_simulation_running:
        data = ws.generate_data()

        # Send data to the Dashboard
        socketio.emit('new_data', data)

        print(data['id'])
        print(data['lat'])

        # Send data to Kafka
        producer.produce_data('w', key = data['id'], value=data)

        # Wait before sending the next data
        time.sleep(1)

# When user clicks on start_simulation (Reset) button
@socketio.on('stop_simulation')
def stop_simulation():
    # print('STOP SIMULATION', file=sys.stdout)

    global is_simulation_running
    global ws

    is_simulation_running = False
    ws = WereableSimulator(individual_id=USER_ID, lat=LAT, lng=LNG)


@socketio.on('start_stress')
def start_stress():
    ws.set_stress(True)

@socketio.on('start_illness')
def start_illness():
    ws.set_illness(True)


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True) # for development