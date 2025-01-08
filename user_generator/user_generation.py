import os
import time
import pandas as pd
import uuid

from services.kafka_client import KafkaProducerWrapper
        

def main():

    time.sleep(10)  # Wait 10 seconds other services are up and running

    # Setup kafka
    kafka = KafkaProducerWrapper()

    # Read df
    df_users = pd.read_csv(os.path.join("..", "data", "Users_synthetic_dataset.csv"))

    # Drop first 100
    df_users = df_users.iloc[100:]

    # Drop PatientID: not unique
    df_users.drop(columns = ["PatientID"], inplace=True)

    # Define columns not to convert to boolean
    non_bool_columns = [
        'EducationLevel', 
        'bmi',
        'PhysicalActivity',
        'DietQuality',
        'SleepQuality',
        'PollutionExposure',
        'PollenExposure',
        'DustExposure',
        'Cad_Probability',
        'Date_of_Birth'
    ]

    # Convert relevant columns to boolean
    for col in df_users.columns:
        if col not in non_bool_columns:
            df_users[col] = df_users[col] == 1

    # Transform each row into a dictionary
    list_of_dicts = df_users.to_dict(orient='records')

    # Print the result
    for user in list_of_dicts:

        user_id = uuid.uuid4()
        user_id = str(user_id)
        user['user_id'] = user_id
        
        print("Sending to Kafka")
        kafka.produce_data(
            topic='u',
            key=user_id,
            value=user
        )
        print("Waiting 30 seconds to send next user")

        time.sleep(30) 

if __name__ == "__main__":
    main()