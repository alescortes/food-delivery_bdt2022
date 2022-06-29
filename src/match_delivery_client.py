from functions import Scheduler
from handlers.mongo_handlers import MongoHandler
import os
import time
from dotenv import load_dotenv
import openrouteservice as ors

load_dotenv()
MONGO_CLIENT_NAME = os.getenv("MONGO_CLIENT_NAME")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PSW = os.getenv("MONGO_PSW")
ORS_API_KEY = os.getenv("ORS_API_KEY")
COLLECTION_DELIVERYMEN=os.getenv("COLLECTION_DELIVERYMEN")
COLLECTION_PENDING=os.getenv("COLLECTION_PENDING")
COLLECTION_PROCESSED=os.getenv("COLLECTION_PROCESSED")

TIME_SCHEDULER = 120
OPTIMIZER_BATCH_SIZE = 70

ors_client = ors.Client(key=ORS_API_KEY)
handler = MongoHandler(MONGO_CLIENT_NAME, MONGO_DB_NAME, MONGO_USERNAME, MONGO_PSW)

# Wait a bit before assigning orders at the beginning!
time.sleep(10)


while True:
    free_deliverymen = handler.free_deliverymen(COLLECTION_DELIVERYMEN,COLLECTION_PROCESSED)
    # Because of API limits we just take the oldest 70 requests, otherwise the program would crash while
    # computing the optimization matrix.
    pending_requests = handler.return_n_oldest_entries(COLLECTION_PENDING, OPTIMIZER_BATCH_SIZE)
    if len(free_deliverymen) == 0:
        print("No free deliverymen at the moment!")
        time.sleep(TIME_SCHEDULER)
    elif len(pending_requests) == 0:
        print("No pending requests to process at the moment!")
        time.sleep(TIME_SCHEDULER)
    else:
        matches_list = Scheduler.scheduler(free_deliverymen, pending_requests, ors_client, handler, COLLECTION_PENDING,
                                           COLLECTION_PROCESSED, COLLECTION_DELIVERYMEN)
        times_list = [match[2] for match in matches_list]
        time.sleep(Scheduler.optimize_time(times_list, 25))
