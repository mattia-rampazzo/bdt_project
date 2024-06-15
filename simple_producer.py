from kafka import KafkaProducer

TOPIC_NAME = 'air'
KAFKA_SERVER = '172.27.32.1:9092'

producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)

producer.send(TOPIC_NAME, b'Test')
producer.flush()