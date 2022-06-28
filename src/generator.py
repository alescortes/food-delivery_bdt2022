import time
import json
import random
import openrouteservice as ors
from handlers.mongo_handlers import MongoHandler
import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv
from functions import Generator

load_dotenv()
MONGO_CLIENT_NAME = os.getenv("MONGO_CLIENT_NAME")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MQTT_BROKER_NAME = os.getenv("MQTT_BROKER_NAME")
GENERATOR_NAME = os.getenv("GENERATOR_NAME")
TOPIC_NAME = os.getenv("TOPIC_NAME")
RESTAURANTS_FILENAME = os.getenv("RESTAURANTS_FILENAME")
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PSW = os.getenv("MONGO_PSW")
ORS_API_KEY = os.getenv("ORS_API_KEY")
COLLECTION_DELIVERYMEN=os.getenv("COLLECTION_DELIVERYMEN")
COLLECTION_PENDING=os.getenv("COLLECTION_PENDING")
COLLECTION_PROCESSED=os.getenv("COLLECTION_PROCESSED")

NUM_DELIVERYMEN = 50
TIME_GENERATOR = 90
NUM_PENDING = 70

ors_client = ors.Client(key=ORS_API_KEY)
handler = MongoHandler(MONGO_CLIENT_NAME, MONGO_DB_NAME, MONGO_USERNAME, MONGO_PSW)

# To avoid API errors, the file "restaurants.csv" is already in the repository. However, this function shows how
# such file has been generated.
#Generator.generate_restaurant_list(9.183884, 45.4673545, ors_client, "restaurants.csv")

# First run: initialize delivery men and new orders.
if handler.n_elements(COLLECTION_DELIVERYMEN) == 0:
    Generator.initialize_deliverymen(NUM_DELIVERYMEN, handler, COLLECTION_DELIVERYMEN)
if handler.n_elements(COLLECTION_PENDING) == 0:
    Generator.initialize_pending(NUM_PENDING, RESTAURANTS_FILENAME, handler, COLLECTION_PENDING)

# Connecting to the queue system...
client = mqtt.Client(GENERATOR_NAME)
client.connect(MQTT_BROKER_NAME)
print('Connected to broker ', MQTT_BROKER_NAME)
while True:
    # Keep generating random requests and publishing them
    new_req = Generator.generate_request(RESTAURANTS_FILENAME)
    message = json.dumps(new_req.to_repr())
    client.publish(TOPIC_NAME, message, qos=2)
    client.loop()
    print(new_req.to_repr())
    time.sleep(random.uniform(0, TIME_GENERATOR))
