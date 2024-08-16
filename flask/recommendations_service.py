import os
import time
import json
import random

from kafka import KafkaProducer, KafkaConsumer
from dotenv import load_dotenv



from kafka import KafkaConsumer
from flask_socketio import SocketIO, emit

# Assuming you're using Flask-SocketIO
socketio = SocketIO()

def get_recommendations():
    
    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        HEALTH_RECOMMENDATIONS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )
    

    try:
        for message in consumer:
            print("Received message from Kafka.")
            
            # Print detailed information about the message
            print(f"Message key: {message.key.decode('utf-8') if message.key else 'No key'}")
            print(f"Message partition: {message.partition}")
            print(f"Message offset: {message.offset}")
            print(f"Raw message value (bytes): {message.value}")
            
            try:
                # Decode the message value
                decoded_value = message.value.decode('utf-8')
                print(f"Decoded message value (str): {decoded_value}")

                # If you need to process the string as a list, you can split or handle it accordingly
                # For example, splitting the recommendations
                recommendations = decoded_value.strip('[]').split(', ')
                for rec in recommendations:
                    print(f"Recommendation: {rec}")

                # Emit the decoded value to the client
                socketio.emit('new_recommendation', {'data': recommendations})
                    
            except UnicodeDecodeError as e:
                print(f"Unicode decode error: {str(e)}")
                socketio.emit('new_recommendation', {'data': message.value})  # Send raw data if decoding fails
                
    except Exception as e:
        print(f"Error in Kafka consumer: {str(e)}")
    finally:
        consumer.close()



# Load environment variables from .env file
load_dotenv()

# Access environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
WEREABLE_SIMULATOR_TOPIC = os.getenv('WEREABLE_SIMULATOR_TOPIC')
HEALTH_RECOMMENDATIONS_TOPIC = os.getenv('HEALTH_RECOMMENDATIONS_TOPIC')  # Second Kafka topic

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)



def generate_random_data():
    """Simulate generating random data for the dashboard."""
    data = {
        'EDA': round(random.uniform(0.5, 5.0), 2),
        'BVP': round(random.uniform(60, 100), 2),
        'TEMP': round(random.uniform(36.5, 37.5), 2),
        'HRV': round(random.uniform(50, 150), 2),
        'LAT': round(random.uniform(45.7, 47), 6),
        'LNG': round(random.uniform(10.5, 12), 6),
        'timestamp': time.time()
    }
    return data

def publish_data(data):

    producer.send(WEREABLE_SIMULATOR_TOPIC, value=data)


