# import os
# import json
# import subprocess
# from flask import Flask, render_template, request, redirect, url_for, jsonify
# from kafka import KafkaConsumer
# from dotenv import load_dotenv

# app = Flask(__name__)

# # Load environment variables from .env file
# load_dotenv()

# # Access environment variables
# # KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
# KAFKA_TOPIC = os.getenv('WEREABLE_SIMULATOR_TOPIC')
# KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')


# # Initialize simple Kafka consumer
# # Initialize the Kafka consumer
# consumer = KafkaConsumer(
#     KAFKA_TOPIC,
#     bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
#     auto_offset_reset='earliest',  # Start reading at the earliest message
#     enable_auto_commit=True,  # Automatically commit message offsets
#     value_deserializer=lambda x: x.decode('utf-8')  # Assuming your messages are encoded in UTF-8
# )


# user_data = {}

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         # Handle form data
#         user_data['name'] = request.form.get('name')
#         user_data['surname'] = request.form.get('surname')
#         user_data['gender'] = request.form.get('gender')
#         user_data['age'] = request.form.get('age')
#         user_data['Height_cm'] = request.form.get('Height_cm')
#         user_data['Weight_kg'] = request.form.get('Weight_kg')
#         user_data['hypertension'] = request.form.get('hypertension')
#         user_data['heart_disease'] = request.form.get('heart_disease')
#         user_data['ever_married'] = request.form.get('ever_married')
#         user_data['work_type'] = request.form.get('work_type')
#         user_data['Residence_type'] = request.form.get('Residence_type')
#         user_data['stroke'] = request.form.get('stroke')
#         user_data['Current_Smoker'] = request.form.get('Current_Smoker')
#         user_data['EX_Smoker'] = request.form.get('EX_Smoker')
#         user_data['Obesity'] = request.form.get('Obesity')
#         user_data['Cad'] = request.form.get('Cad')
#         user_data['Hay_Fever'] = request.form.get('Hay_Fever')
#         user_data['Asthma'] = request.form.get('Asthma')
#         user_data['Birch_Pollen'] = '1' if request.form.get('Birch_Pollen') else '0'
#         user_data['Ragweed_Pollen'] = '1' if request.form.get('Ragweed_Pollen') else '0'
#         user_data['Grass_Pollen'] = '1' if request.form.get('Grass_Pollen') else '0'

#         return redirect(url_for('user_info'))

#     return render_template('index.html')

# @app.route('/user_info')
# def user_info():
#     return render_template('user_info.html', user=user_data)

# @app.route('/start_simulation', methods=['POST'])
# def start_simulation():
#     try:
#         # Launch the external Python script
#         subprocess.Popen(["python", "../wereable_simulator/wereable_simulator.py "])
#         return "Simulation started!", 200
#     except Exception as e:
#         return str(e), 500

# @app.route('/consume')
# def consume():
#     # This route will display Kafka messages
#     messages = []
#     for message in consumer:
#         msg = message.value
#         messages.append(msg)
#         if len(messages) >= 10:  # Limit to 10 messages for display
#             break
#     return jsonify(messages)

# if __name__ == '__main__':
#     app.run(debug=True)


import time
from threading import Thread
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit


from recommendations_service import generate_random_data, publish_data, get_recommendations
from wereable_simulator import generate_data
from map_generator import generate_pollen_risk_map


app = Flask(__name__)
socketio = SocketIO(app)



from kafka import KafkaConsumer
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
WEREABLE_SIMULATOR_TOPIC = os.getenv('WEREABLE_SIMULATOR_TOPIC')
HEALTH_RECOMMENDATIONS_TOPIC = os.getenv('HEALTH_RECOMMENDATIONS_TOPIC')
MUNICIPALITIES_AIR_QUALITY_UPDATE = os.getenv('MUNICIPALITIES_AIR_QUALITY_UPDATE')


def get_recommendations():

    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        HEALTH_RECOMMENDATIONS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='latest',
        enable_auto_commit=True
    )
    
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

def kafka_map_consumer():

    print("lol")
    
    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        MUNICIPALITIES_AIR_QUALITY_UPDATE,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='latest',
        enable_auto_commit=True
    )

    try:
        for message in consumer:

            # Process the message and generate an updated map
            # message_value = msg.value().decode('utf-8')
            print(f'Received message: {message}')
            
            generate_pollen_risk_map()

            # Emit a message to the client
            socketio.emit('updated_pollen_risk_map', {'message': 'Map updated'})
                
    except Exception as e:
        print(f"Error in Kafka consumer: {str(e)}")
    finally:
        consumer.close()




@app.route('/')
def index():
    return render_template('dashboard.html')

@socketio.on('start_simulation')
def start_simulation():

    # Launch a Thread to listen to HealthRecommendation topic
    t = Thread(target=get_recommendations)
    t.start()

    # Simulate wereable data
    while True:
        data = generate_data()
        # Send data to the client
        socketio.emit('new_data', data)
        # Send data to Kafka
        publish_data(data)
        
        # Wait before sending the next data
        time.sleep(1)


@socketio.on('connect')
def live_pollen_risk_map():
    # Launch a Thread to listen to HealthRecommendation topic
    t = Thread(target=kafka_map_consumer)
    t.start()


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True) # for development