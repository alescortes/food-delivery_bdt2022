import csv
import random
import pandas as pd
from datetime import datetime
from handlers.mongo_handlers import MongoHandler
import numpy as np
from scipy.optimize import linear_sum_assignment

class Request:
    """
    Class used to handle the simulated requests generated by the generator.
    """
    def __init__(self, client_coords: tuple, client_name: str, client_surname: str, restaurant_coords: tuple,
                 restaurant_name: str, restaurant_type: str, order: str, timestamp: datetime) -> None:
        self.client_coords = client_coords
        self.client_name = client_name
        self.client_surname = client_surname
        self.restaurant_coords = restaurant_coords
        self.restaurant_name = restaurant_name
        self.restaurant_type = restaurant_type
        self.order = order
        self.timestamp = timestamp

    def to_repr(self) -> dict:
        dizionario = {}
        client_subdiz = {}
        rest_subdiz = {}
        client_subdiz['client_coords'] = self.client_coords
        client_subdiz['client_name'] = self.client_name
        client_subdiz['client_surname'] = self.client_surname
        rest_subdiz['restaurant_coords'] = self.restaurant_coords
        rest_subdiz['restaurant_name'] = self.restaurant_name
        rest_subdiz['restaurant_type'] = self.restaurant_type
        rest_subdiz['order'] = self.order
        dizionario['timestamp'] = self.timestamp.isoformat()
        dizionario["client"] = client_subdiz
        dizionario["restaurant"] = rest_subdiz
        return dizionario

class Deliveryman:
    """
    Class used to handle each deliveryman.
    """
    def __init__(self, cur_position: tuple, name: str, surname: str) -> None:
        self.name = name
        self.surname = surname
        self.cur_position = cur_position

    def to_repr(self) -> dict:
        temp_dict = {}
        temp_dict['current_coords'] = self.cur_position
        temp_dict['name'] = self.name
        temp_dict['surname'] = self.surname
        return temp_dict

class Generator:
    """
    Class used to organize all the functions which have to do with the generation of fake data (both
    requests and deliverymen).
    """
    @staticmethod
    def generate_client():
        lon, lat = Generator.generate_coords_bbox((9.141998, 45.437294), (9.222679, 45.488545))
        return lon, lat

    @staticmethod
    def generate_order():
        order_list = ["Pizza margherita", "Kebab no onion", "Hamburger XXL", "Spicy noodles", "Ramen",'Poke with tuna',
                      'Poke with salmon', 'Uramaki salmon','Sushi boat','Chocolate ice cream']
        order = order_list[random.randint(0,len(order_list)-1)]
        return order

    @staticmethod
    def generate_name():
        name_list = ['Antonio', 'Benedetta', 'Calogero', 'Damiano', 'Elena', 'Francesca', 'Giacomino', 'Hubert', 'Ilario',
                     'Jordan','Karl','Lamberto','Mohammed','Nicola','Orietta','Patrizia','Quentin','Riccardo','Stefano','Tullio',
                     'Umberta','Veronica','Walter','Zeno']
        surname_list = ['Antonacci', 'Brambilla', 'Chiericati', 'Damilano','Esposito','Fumagalli', 'Grimaldelli', 'Hyvoz','Illy',
                        'Johnson','Koala','Lampredotti','Maculan','Otranto','Pasquinucci','Quorum','Romboidi','Scanagatta',
                        'Turandotti','Uliveto','Verstappen','Williamson','Zambrotta']
        client_name = name_list[random.randint(0, len(name_list)-1)]
        client_surname = surname_list[random.randint(0, len(surname_list)-1)]
        return client_name, client_surname

    @staticmethod
    def generate_restaurant(filename: str):
        restaurant_df = pd.read_csv(filename)
        random_sample = restaurant_df.sample()
        restaurant_coords = (random_sample.iloc[0,0], random_sample.iloc[0,1])
        restaurant_name = random_sample.iloc[0,2]
        restaurant_type = random_sample.iloc[0,3]
        return restaurant_coords, restaurant_name, restaurant_type

    @staticmethod
    def generate_request(filename: str):
        client_coords = Generator.generate_client()
        order = Generator.generate_order()
        client_name, client_surname = Generator.generate_name()
        restaurant_coords, restaurant_name, restaurant_type = Generator.generate_restaurant(filename)
        ts = datetime.now()
        to_ret = Request(client_coords, client_name, client_surname, restaurant_coords, restaurant_name, restaurant_type, order, ts)
        return to_ret

    @staticmethod
    def initialize_deliverymen(n_fattorini: int, handle: MongoHandler, collection_deliverymen: str):
        """
        Initialize n_fattorini deliverymen on the corresponding collection.
        """
        for i in range(n_fattorini):
            lon, lat = Generator.generate_coords_bbox((9.141998, 45.437294), (9.222679, 45.488545))
            name, surname = Generator.generate_name()
            tmp_fattorino = Deliveryman((lon,lat), name, surname).to_repr()
            handle.insert_element(collection_deliverymen, tmp_fattorino)
        print("Inserted ",n_fattorini," deliverymen in the DB!")

    @staticmethod
    def initialize_pending(n_requests: int, filename: str, handler: MongoHandler, collection_pending: str):
        """
        Initialize n_requests pending requests on the corresponding collection so that the simulation can start straightaway.
        """
        for i in range(n_requests):
            my_req = Generator.generate_request(filename).to_repr()
            handler.insert_element(collection_pending, my_req)
        print("Inserted ", n_requests, "initial requests in the DB!")

    @staticmethod
    def generate_restaurant_list(lon, lat, client, filename):
        """
        This function generates a document called "restaurants.csv", which contains a list of all the coordinates, names
        and types of restaurants in a radius of 2000m of a specified point, using the Openrouteservice API.
        """

        geojson = {"type": "point", "coordinates": [lon, lat]}
        # Get places of interest
        pois = client.places(request='pois',
                             geojson=geojson,
                             # buffer searches (in meters) around specified point. 2000m is the maximum radius allowed by the API.
                             buffer=2000,
                             # Only 5 categories are allowed at the time. We selected these:
                             # 561: bar
                             # 564: cafe
                             # 566: fast food
                             # 568: ice cream
                             # 570: restaurant
                             filter_category_ids=[561, 564, 566, 568, 570])
        # Parsing the result...
        restaurant_list = []
        for poi in pois['features']:
            restaurant = []
            # Coordinates
            restaurant.append(poi['geometry']['coordinates'][0])
            restaurant.append(poi['geometry']['coordinates'][1])

            # Restaurant name
            if 'osm_tags' in poi['properties'] and 'name' in poi['properties']['osm_tags']:
                restaurant.append(poi['properties']['osm_tags']['name'])
            else:
                restaurant.append("Unknown name")

            # Restaurant type
            if poi['properties']['category_ids'] == {'561': {'category_name': 'bar', 'category_group': 'sustenance'}}:
                case = 'bar'
            elif poi['properties']['category_ids'] == {
                '564': {'category_name': 'cafe', 'category_group': 'sustenance'}}:
                case = 'cafe'
            elif poi['properties']['category_ids'] == {
                '566': {'category_name': 'fast_food', 'category_group': 'sustenance'}}:
                case = 'fast food'
            elif poi['properties']['category_ids'] == {
                '568': {'category_name': 'ice_cream', 'category_group': 'sustenance'}}:
                case = 'ice cream'
            else:
                case = 'restaurant'
            restaurant.append(case)
            restaurant_list.append(restaurant)

        # Create a csv file of all the fetched restaurants
        with open(filename, 'w') as f:
            write = csv.writer(f)
            write.writerow(["lon", "lat", "name", "type"])
            write.writerows(restaurant_list)

        print("Fetched restaurant list!")

    @staticmethod
    def generate_coords_bbox(bottomleft: tuple, topright: tuple):
        """
        Generate a random tuple of longitude and latitude from a bounding box
        """
        #   (9.141998, 45.437294) (9.222679, 45.488545) are the coordinates of the bounding box chosen for Milan
        lon = random.uniform(bottomleft[0], topright[0])
        lat = random.uniform(bottomleft[1], topright[1])
        return lon, lat


class Scheduler:
    """
    Class used to group all the functions that deal with matching a deliveryman with a pending order.
    """
    @staticmethod
    def compute_matrix(coords_source: list, coords_destination: list, client):
        """
        Function that takes as input a list of source coordinates and a list of destination coordinates and outputs
        a numpy source-destination matrix through the use of the openrouteservice API. The various cells of the matrix
        correspond to the time needed to go from source to destination by bike.
        """
        coordinates = coords_source + coords_destination

        matrix = client.distance_matrix(
            locations=coordinates,
            sources=[i for i in range(len(coords_source))],  # fattorini
            destinations=[j for j in range(len(coords_source), len(coordinates))],  # ristoranti
            profile='cycling-regular',
            metrics=['duration'],
            validate=False,
            optimized=True
        )
        return np.array(matrix['durations'])

    @staticmethod
    def scheduler(free_deliverymen: list, pending_requests: list, ors_client, mongo_handler: MongoHandler,
                  collection_pending: str, collection_processed: str, collection_deliverymen: str):
        """
        This function takes a list of free deliverymen and a list of pending requests and outputs a list of lists.
        Each sublist is composed by a deliveryman, its matched request and its duration. This is forwarded, in the
        architecture of the program, to two functions:
        1) process_request, which deletes the matched requests from the pending_requests collection, inserts them
        with additional data onto the processed_requests collection and updates the position of the deliverymen
        in the deliverymen collection.
        2) create_map, which is separated in create_map.py and is used to render the map on the flask interface.
        """

        # Return the coordinates of the restaurants of not-yet-processed orders and of the deliverymen
        rest_coords = [list(el['restaurant']['restaurant_coords']) for el in pending_requests]
        free_deliverymen_coords = [el['current_coords'] for el in free_deliverymen]

        # Calculate the origin-destination matrix
        deliveryman_rist_duration_matrix = Scheduler.compute_matrix(free_deliverymen_coords, rest_coords, ors_client)
        # Find the optimal solution for the linear sum assignment problem
        row_ind, col_ind = linear_sum_assignment(deliveryman_rist_duration_matrix)
        # Create a list of lists, each one containing the deliveryman, the order it has been assigned to,
        # and the duration of the first leg of the trip in seconds
        matches_list = [[free_deliverymen[i],pending_requests[j],deliveryman_rist_duration_matrix[i][j]] for i,j in list(zip(row_ind, col_ind))]

        # Return the coordinates of the restaurants and of the clients
        sel_rest_coords = [el[1]['restaurant']['restaurant_coords'] for el in matches_list]
        sel_client_coords = [el[1]['client']['client_coords'] for el in matches_list]
        # Calculate another origin-destination matrix for the second leg of the trip
        rist_user_duration_matrix = Scheduler.compute_matrix(sel_rest_coords, sel_client_coords, ors_client)
        # This time no optimization is involved. We just need to get the time of the second leg of the trip in seconds
        rist_user_durations_list = list(rist_user_duration_matrix.diagonal())
        # Updating the value in matches_list with the full duration of the trip
        for i in range(len(matches_list)):
            matches_list[i][2] += rist_user_durations_list[i]
        # Processing the request
        Scheduler.process_requests(matches_list, mongo_handler, collection_pending,
                                   collection_processed,collection_deliverymen)

        return matches_list

    @staticmethod
    def process_requests(matches_list: list, mongo_handler: MongoHandler, collection_pending: str,
                         collection_processed: str, collection_deliverymen: str):
        """
        This function deletes the matched requests from the pending_requests collection, inserts them
        with additional data and a modified structure onto the processed_requests collection
        and updates the position of the deliverymen in the deliverymen collection.
        """
        for match in matches_list:
            completed_time = datetime.fromtimestamp(datetime.now().timestamp() + round(match[2]))

            tmp_dict = {}
            timestamps = {}

            timestamps['req_sent'] = datetime.fromisoformat(match[1]['timestamp'])
            timestamps['req_processed'] = datetime.now()
            timestamps['req_delivered'] = completed_time

            tmp_dict['deliveryman'] = match[0] # Starting coordinates of the deliveryman
            del match[1]['timestamp'] # We delete this field since it would be a duplicate information in the processed collection.
            tmp_dict['request'] = match[1]
            tmp_dict['duration'] = round(match[2])
            tmp_dict['timestamps'] = timestamps
            # Insert processed order into the processed collection
            mongo_handler.insert_element(collection_processed,tmp_dict)
            # Delete the corresponding request from the pending collection
            id_deliveryman = match[0]['_id']
            mongo_handler.update_pos_deliveryman(collection_deliverymen, id_deliveryman, match[1]['client']['client_coords'])

        matched_requests_id = [match[1]['_id'] for match in matches_list]
        mongo_handler.delete_elements_from_id(collection_pending, matched_requests_id)
        print(f"{len(matches_list)} delivery men have been assigned.")

    @staticmethod
    def optimize_time(list_ttl: list, percentile: int):
        """
        Determine after how many seconds the next matcher should run.
        The cumulative distribution of current matched orders is taken into consideration. The order which
        corresponds to the highest difference quotient is taken as the next time. If this time is higher than
        the specified percentile, then the next run will happen at the time of the specified percentile.
        """
        list_ttl.sort()
        x, counts = np.unique(list_ttl, return_counts=True)
        cusum = np.cumsum(counts)
        cumulative_distr = x, (cusum / cusum[-1])
        times = cumulative_distr[0]
        probs = cumulative_distr[1]

        difference_quotient_list = [(y1)/(x1) for x1, y1 in zip(times, probs)]
        max_value = max(difference_quotient_list)
        time_new_run = int(round(times[difference_quotient_list.index(max_value)]))
        perc_time = int(round(np.percentile(list_ttl, percentile)))

        print("Optimized time:", time_new_run, f" {percentile} percentile time: ", perc_time)
        if time_new_run <= perc_time:
            print(f"New scheduling will be in {time_new_run}s.")
            return time_new_run + 1
        else:
            print(f"New scheduling will be in {perc_time}s.")
            return perc_time + 1
