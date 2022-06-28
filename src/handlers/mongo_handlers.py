from datetime import datetime
import pymongo
from pymongo import MongoClient


class MongoHandler:
    """
    A class to interface with MongoDB, using the pymongo library.
    """
    def __init__(self, client_name: str, db_name: str, username: str, password: str):
        self.client = MongoClient(client_name, username=username,
                                  password=password, authSource=db_name, authMechanism='SCRAM-SHA-256')
        self.db = self.client[db_name]

    def insert_element(self, collection_name, element):
        """
        Insert an element into a collection
        """
        my_collection = self.db[collection_name]
        my_collection.insert_one(element)

    def print_entries(self, collection_name):
        """
        Print entries of a collection
        """
        my_collection = self.db[collection_name]
        for el in my_collection.find():
            print(el)

    def drop_collection(self, collection_name):
        """
        Drop a collection
        """
        my_collection = self.db[collection_name]
        my_collection.drop()

    def return_entries(self, collection_name):
        """
        Return a list of all the entries of a collection
        """
        my_collection = self.db[collection_name]
        list_to_ret = []
        for el in my_collection.find():
            list_to_ret.append(el)
        return list_to_ret

    def return_n_oldest_entries(self, collection_name, n_entries):
        """
        Return a list of all the n oldest entries of a collection. Used when running the optimizer, in order
        to process first the oldest requests.
        """
        my_collection = self.db[collection_name]
        list_to_ret = []
        for el in my_collection.find().sort([("timestamp", pymongo.ASCENDING)]).limit(n_entries):
            list_to_ret.append(el)
        return list_to_ret

    def update_pos_deliveryman(self, collection_name, id_deliveryman, new_pos):
        """
        Update the position of each deliveryman with the final position (i.e. that of the client).
        """
        my_collection = self.db[collection_name]
        query = {"_id": id_deliveryman}
        new_value = {"$set": {"current_coords": new_pos}}
        my_collection.update_one(query, new_value)

    def delete_elements_from_id(self, collection_name: str, element_id_list: list):
        """
        Remove the requests which have been matched from the pending_requests collection
        """
        my_collection = self.db[collection_name]
        my_collection.delete_many({'_id': {'$in': element_id_list}})

    def n_elements(self, collection_name: str):
        """
        Return the number of elements in a collection
        """
        my_collection = self.db[collection_name]
        cursor = my_collection.count_documents({})
        return cursor

    def orders_dict(self, collection_name: str):
        """
        Return a dictionary with the frequences of the various orders in the processed_orders collection. Used
        for the flask analytics interface.
        """
        my_collection = self.db[collection_name]
        order_list = ["Pizza margherita", "Kebab no onion", "Hamburger XXL", "Spicy noodles", "Ramen", 'Poke with tuna',
                      'Poke with salmon', 'Uramaki salmon', 'Sushi boat', 'Chocolate ice cream']
        to_ret = {}
        for food in order_list:
            to_ret[food] = my_collection.count_documents({"request.restaurant.order": food})

        return {k: v for k, v in sorted(to_ret.items(), key=lambda item: item[1], reverse=True)}

    def current_orders(self, collection_name: str):
        """
        Return a list of all the processed orders which have a timestamp of delivery greater than the current time
        (i.e. orders which are currently being processed).
        """
        my_collection = self.db[collection_name]
        ora = datetime.now()
        cursor = my_collection.find({"timestamps.req_delivered": {"$gt": ora}})
        return [el for el in cursor]

    def occupied_deliverymen(self, collection_name: str):
        """
        Return a list of all the occupied deliverymen. Used for the flask interface.
        """
        my_collection = self.db[collection_name]
        current_orders = self.current_orders(collection_name)
        to_ret = []
        for el in current_orders:
            sublist = []
            sublist.append(el["deliveryman"]["name"])
            sublist.append(el["deliveryman"]["surname"])
            sublist.append(
                [round(el["deliveryman"]["current_coords"][0], 6), round(el["deliveryman"]["current_coords"][1], 6)])
            to_ret.append(sublist)
        return to_ret

    def free_deliverymen(self, collection_deliverymen: str, collection_processed: str):
        """
        Return a list of all the free deliverymen. Used in the optimization phase.
        """
        my_collection = self.db[collection_deliverymen]

        all_deliverymen_id = [el["_id"] for el in self.return_entries(collection_deliverymen)]
        occupied_deliverymen_id = [el["deliveryman"]["_id"] for el in self.current_orders(collection_processed)]
        free_deliverymen_id = [x for x in all_deliverymen_id if x not in occupied_deliverymen_id]

        cursor = my_collection.find({ "_id" : { "$in" : free_deliverymen_id} })
        return [free_del for free_del in cursor]

    def avg_wait_time(self, collection_name: str):
        """
        Return the average waiting time. Used in the flask interface.
        """
        my_collection = self.db[collection_name]
        cursor = my_collection.aggregate(
            [
                {
                    "$group":
                        {
                            "_id" : "null",
                            "averageTime":
                                {
                                    "$avg":
                                        {
                                            "$dateDiff":
                                                {
                                                    "startDate": "$timestamps.req_sent",
                                                    "endDate": "$timestamps.req_delivered",
                                                    "unit": "minute"
                                                }
                                        }
                                }
                        }
                },
                {
                    "$project":
                        {
                            "_id":0
                        }
                }
            ]
        )
        to_ret = list(cursor)
        return round(to_ret[0]["averageTime"],2)