# Big Data Technologies 2022

## Group 15 - Optimize the delivery of goods in the city of Milan

This is a big data system to generate fake random orders to a food delivery service and to match a set of deliverymen to deliver such orders.
The system includes a MongoDB database to store in three different collections the deliverymen, the pending orders, and the processed orders and a MQTT queue which acts as a buffer in the data ingestion phase. The result of the program is a flask dashboard which displays a map and a series of analytics. 

### Architecture
There are four separated services continuously running at the same time.
- `generator.py`: used to initialize the database with a set of deliverymen (in COLLECTION_DELIVERYMEN) and a first batch of requests (in COLLECTION_PENDING), and then to keep generating random requests. When a request is generated, it is published to the corresponding MQTT topic.
- `subscriber.py`: used to receive the messages published on the MQTT topic and to insert them into the COLLECTION_PENDING on MongoDB.
- `match_delivery_client.py`: used to assign the orders in COLLECTION_PENDING to the free deliverymen. When the orders are assigned, they get removed from the COLLECTION_PENDING and inserted, along with additional information, into the COLLECTION_PROCESSED.
- `flask_analytics`: used to display the map and a series of analytics on the orders and the deliverymen.

### The Openrouteservice API
The system relies on the [openrouteservice API](https://openrouteservice.org/) in three separate instances:
1) when the generator is run for the first time, the [Points of Interest API ](https://openrouteservice.org/dev/#/api-docs/pois/post) is used to generate a `restaurants.csv` file, containing information about the location of real restaurants in Milan. Nonetheless, to avoid (seemingly frequent) API errors, such file is already provided in the repository.
2) in the optimization phase, the [Matrix API](https://openrouteservice.org/dev/#/api-docs/matrix) is used to compute two origin-destination matrices, to find the best deliveryman-order match and to compute for each order the length of the trip. Such matrices are limited to 3500 cells.
3) in the analytics phase, to plot the routes on the map, several calls are made to the [Direction API](https://openrouteservice.org/dev/#/api-docs/v2/directions). 

### Running the program
The code is dockerized. To run it, just clone the repository and then type from terminal <pre><code>-sudo docker-compose up</code></pre> and everything should work beautifully (at least on Linux machines, perhaps less beautifully on MacOs).

MongoDB runs on port 27017.
Flask dashboard runs on port 5000.
To see the dashboard, go to `127.0.0.1:5000/`. Roughly a minute should pass before refreshing the dashboard each time, otherwise you could incurr in errors with the openrouteservice API.

### Environment variables
In each of the services folders, a `.env` file is present. This contains environment variables needed to run each service. As a matter of fact, the only thing that should be inserted into each of them in order to run the code is the openrouteservice API key.
