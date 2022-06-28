import time
import os, sys
import openrouteservice as ors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Flask, render_template
from create_map import create_map
from handlers.mongo_handlers import MongoHandler

from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
MONGO_CLIENT_NAME = os.getenv("MONGO_CLIENT_NAME")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PSW = os.getenv("MONGO_PSW")
ORS_API_KEY = os.getenv("ORS_API_KEY")
COLLECTION_DELIVERYMEN = os.getenv("COLLECTION_DELIVERYMEN")
COLLECTION_PENDING = os.getenv("COLLECTION_PENDING")
COLLECTION_PROCESSED = os.getenv("COLLECTION_PROCESSED")
ors_client = ors.Client(key=ORS_API_KEY)

handler = MongoHandler(MONGO_CLIENT_NAME, MONGO_DB_NAME, MONGO_USERNAME, MONGO_PSW)

@app.route('/')
def index():
    # Get the analytics information from the processed orders collection
    chart = handler.orders_dict(COLLECTION_PROCESSED)
    occupied_men = handler.occupied_deliverymen(COLLECTION_PROCESSED)
    avg_wait = handler.avg_wait_time(COLLECTION_PROCESSED)
    n_pending = handler.n_elements(COLLECTION_PENDING)
    n_processed = handler.n_elements(COLLECTION_PROCESSED)
    current_orders = handler.current_orders(COLLECTION_PROCESSED)

    folium_map = create_map(current_orders, ors_client)
    folium_map.save('./dashboard/templates/map.html')
    return render_template('index.html', chart = chart, occupied_men = occupied_men, n_occupied = len(occupied_men),
                           avg_wait = avg_wait, n_pending = n_pending, n_processed = n_processed)

@app.route('/map')
def map():
    return render_template('map.html')

# Wait a bit before starting the analytics, so that the first batch of orders is optimized.
time.sleep(12)

if __name__ == '__main__':
    app.run("0.0.0.0")