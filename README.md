# how to

## install dependencies
- optionally create venv
```
pip install -r requirements.txt
```

## launch dockers
```
docker compose down

docker compose up -d
```



## load municipalities geohash
```
python data/mun_redis_loader.py 
```

## run open_meteo_scraper
```
python open_meteo_api_caller/open_meteo_api_caller.py 
```

## run wereable_simulator
```
python wereable_simulator/wereable_simulator.py 
```
## run spark streaming

```
docker cp pyspark/app.py spark-master:/tmp/app.py

docker exec -it spark-master bash -c "pip install redis" 

docker exec -it spark-worker bash -c "pip install redis" 

docker exec -it spark-master /opt/bitnami/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \
  /tmp/app.py
```

