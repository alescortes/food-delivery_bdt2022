from random import random
from functions import *
import folium
import os
from handlers.mongo_handlers import MongoHandler
from dotenv import load_dotenv
load_dotenv()
MONGO_CLIENT_NAME = os.getenv("MONGO_CLIENT_NAME")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
ORS_API_KEY = os.getenv("ORS_API_KEY")
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PSW = os.getenv("MONGO_PSW")
handler = MongoHandler(MONGO_CLIENT_NAME, MONGO_DB_NAME, MONGO_USERNAME, MONGO_PSW)

def create_map(list_current_orders: list, client):
    """
    Function used to render the map on the Flask dashboard. Notice that, because of API limits,
    only 40 deliverymen can be plotted at most.
    """

    color_list = ['red', 'blue', 'green', 'purple', 'orange','darkred',
                  'darkblue', 'darkgreen', 'cadetblue','pink',
                  'lightblue', 'lightgreen','gray', 'black']

    m = folium.Map(location=[45.4673545, 9.183883], tiles='cartodbpositron', zoom_start=13)

    for el in list_current_orders[:40]:
        # Just keeping the coordinates here so later we can feed them into the Directions API
        triplet = []
        triplet.append(el["deliveryman"]["current_coords"])
        triplet.append(el["request"]["restaurant"]["restaurant_coords"])
        triplet.append(el["request"]["client"]["client_coords"])

        fatt_name = el["deliveryman"]["name"]
        fatt_surname = el["deliveryman"]["surname"]

        rest_name = el["request"]["restaurant"]["restaurant_name"]
        rest_type = el["request"]["restaurant"]["restaurant_type"]

        client_name = el["request"]["client"]["client_name"]
        client_surname = el["request"]["client"]["client_surname"]

        folium.Marker(location=list(reversed(triplet[0])), icon=folium.Icon(icon='bicycle', prefix='fa'),
                      popup=folium.Popup(f"Deliveryman: {fatt_name} {fatt_surname}\n{triplet[0]}")).add_to(m)
        folium.Marker(location=list(reversed(triplet[1])), icon=folium.Icon(icon='cutlery', prefix='fa', color='green'),
                      popup=folium.Popup(f"Restaurant: {rest_name}, Type: {rest_type}\n{triplet[1]}")).add_to(m)
        folium.Marker(location=list(reversed(triplet[2])), icon=folium.Icon(icon='user', prefix='fa', color='orange'),
                      popup=folium.Popup(f"Client: {client_name} {client_surname}\n{triplet[2]}")).add_to(m)

        # For each triplet of coordinates calculate route and append it to map
        route = client.directions(
            coordinates=triplet,
            profile='cycling-regular',
            format='geojson',
            validate=False
        )
        # Choose a random color for the route and plot it
        rand_col = random.randint(0, len(color_list) - 1)
        folium.PolyLine(locations=[list(reversed(coord))
                                   for coord in
                                   route['features'][0]['geometry']['coordinates']],
                        color = color_list[rand_col],
                        weight = 10,
                        opacity = 0.5).add_to(m)

    return m
