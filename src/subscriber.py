import json
import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from handlers.mongo_handlers import MongoHandler
load_dotenv()
MONGO_CLIENT_NAME = os.getenv("MONGO_CLIENT_NAME")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PSW = os.getenv("MONGO_PSW")
MQTT_BROKER_NAME = os.getenv("MQTT_BROKER_NAME")
SUBSCRIBER_NAME = os.getenv("SUBSCRIBER_NAME")
TOPIC_NAME = os.getenv("TOPIC_NAME")
COLLECTION_DELIVERYMEN=os.getenv("COLLECTION_DELIVERYMEN")
COLLECTION_PENDING=os.getenv("COLLECTION_PENDING")
COLLECTION_PROCESSED=os.getenv("COLLECTION_PROCESSED")

handler = MongoHandler(MONGO_CLIENT_NAME, MONGO_DB_NAME, MONGO_USERNAME, MONGO_PSW)

def on_message(client, userdata, msg):
    topic = msg.topic
    m_decode = msg.payload.decode("utf-8", "ignore")
    m_decode = json.loads(m_decode)
    handler.insert_element(COLLECTION_PENDING, m_decode)
    print("Message receivd on topic:",topic)


client =mqtt.Client(SUBSCRIBER_NAME)
client.connect(MQTT_BROKER_NAME)
client.on_message = on_message
print('Connected to broker ', MQTT_BROKER_NAME)
client.subscribe(TOPIC_NAME,2)
client.loop_forever()
client.disconnect()
