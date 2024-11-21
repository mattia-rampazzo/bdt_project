import os
import json
import time
from threading import Thread, Event
from flask import Flask, render_template
from flask_socketio import SocketIO

from services.kafka_client import KafkaProducerWrapper, KafkaConsumerWrapper
from dashboard.utils.wereable_simulator import WereableSimulator
from dashboard.utils.map_generator import generate_pollen_risk_map


app = Flask(__name__)
socketio = SocketIO(app)


# Wereable Simulator instance
ws = WereableSimulator()
is_simulation_running = False

# Producer for wereable data
producer = KafkaProducerWrapper()

# List of threads
threads = []
# Flag to control thread stopping
stop_event = Event()


def kafka_recommendations_consumer():

    # Initialize Kafka consumer
    consumer = KafkaConsumerWrapper()
    
    try:
        for message in consumer:
            
            try:

                # Decode key as a unix timestamp and format it
                timestamp = int(message.key.decode('utf-8'))
                formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

                # Decode the message value
                decoded_value = message.value.decode('utf-8')
                # print(f"Decoded message value (str): {decoded_value}")
                recommendations = decoded_value.strip('[]').split(', ')
                # for rec in recommendations:
                #     print(f"Recommendation: {rec}")

                # Emit to the client
                socketio.emit('new_recommendation', {"time": formatted_time, "recommendations" : recommendations})
                    
            except UnicodeDecodeError as e:
                print(f"Unicode decode error: {str(e)}")
                socketio.emit('new_recommendation', {'data': message.value})  # Send raw data if decoding fails
                
    except Exception as e:
        print(f"Error in Kafka consumer: {str(e)}")
    finally:
        consumer.close()


# Listen to updates in air data
# When new data arrive generate new map
def kafka_map_consumer():
    # Set up Kafka consumer
    consumer = KafkaConsumerWrapper()

    try:
        while not stop_event.is_set():
            # Use a timeout to periodically check if the stop event is set
            msg = consumer.poll(timeout_ms=1000)  # Timeout in milliseconds

            if not msg:  # No messages received in the timeout period
                continue

            generate_pollen_risk_map()

            # Alert the dashboard a new map is available
            socketio.emit('updated_pollen_risk_map', {'message': 'Map updated'})
            

            for partition, messages in msg.items():
                for message in messages:
                    # Process the received message
                    print(f"Received message: {message.value.decode('utf-8')}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        consumer.close()
        print("Kafka consumer thread stopped.")


# Deliver HTML
@app.route('/')
def index():
    return render_template('dashboard.html')


# When user clicks on start_simulation (Start) button
@socketio.on('start_simulation')
def start_simulation():
    global is_simulation_running

    is_simulation_running = True

    # Simulate wereable data
    while is_simulation_running:
        payload = ws.generate_data()
        data=json.dumps(payload).encode('utf-8')
        # Send data to Kafka
        producer.produce_data('w', data)
        # publish_data(data)
        # Send data to the client
        socketio.emit('new_data', data)

        
        # Wait before sending the next data
        time.sleep(1)

# When user clicks on start_simulation (Reset) button
@socketio.on('stop_simulation')
def stop_simulation():
    global is_simulation_running
    global ws

    is_simulation_running = False
    ws = WereableSimulator()


@socketio.on('start_stress')
def start_stress():
    ws.set_stress(True)

@socketio.on('start_illness')
def start_illness():
    ws.set_illness(True)


# When a client connects (Load page)
@socketio.on('connect')
def live_pollen_risk_map():
    # Launch a Thread to listen to HealthRecommendation topic
    t = Thread(target=kafka_map_consumer)
    t.start()
    threads.append(t)

    # Launch a Thread to listen to HealthRecommendation topic
    t = Thread(target=kafka_recommendations_consumer)
    t.start()
    threads.append(t)

# When a client connects (Reload page)
@socketio.on('disconnect')
def disc():
    stop_event.set()

    for t in threads:
        t.join()  # Wait for thread to finish

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True) # for development