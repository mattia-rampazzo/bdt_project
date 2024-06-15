# how to

## install dependencies
better if you create a venv first
pip install requirements.txt

## launch dockers

### first time (create a container)
- docker run --name zookeeper -p 2181:2181 zookeeper
- docker run --name kafka -p 9092:9092 -e KAFKA_ZOOKEEPER_CONNECT=172.27.32.1:2181 -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://172.27.32.1:9092 -e KAFKA_OFFSET_TOPIC_REPLICATION_FACTOR=1 confluentinc/cp-kafka
- docker run --name redis -d redis

### successive times (just run it)
- docker start zookeeper -i
- docker start kafka -i
- docker start redis -i


## run open_meteo_scraper
python open_meteo_scraper/open_meteo_scraper.py 

## run wereable_simulator
python wereable_simulator/wereable_simulator.py 

- to display results pyton simple_consumer.py