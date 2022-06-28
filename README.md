# Big Data Technologies 2022

## Group 15 - Optimize the delivery of goods in the city of Milan

This is a big data system to generate fake random orders to a food delivery service and to match a set of deliverymen to deliver such orders.
The system includes a MongoDB database to st

### Architecture
There are four separated services running at the same time.
- `generator.py`: used to initialize the database with a set of deliverymen (in COLLECTION_DELIVERYMEN) and a first batch of requests (in COLLECTION_PENDING), and then to keep generating random requests. When a request is generated, it is published to the corresponding MQTT topic.
- `subscriber.py`: used to receive the messages published on the MQTT topic and to insert them into the COLLECTION_PENDING on MongoDB.
- `match_delivery_client.py`: used to assign the oldest 70 orders in COLLECTION_PENDING to the free deliverymen. When the orders are assigned, they get removed from the COLLECTION_PENDING and inserted, along with additional information, into the COLLECTION_PROCESSED.
- `flask_analytics`: used to display the map and a series of analytics on the orders and the deliverymen.

### Running the program
The code is dockerized. To run it, just clone the repository and then type from terminal <pre><code>-sudo docker-compose up</code></pre> and everything should work beautifully (at least on Linux machines).

MongoDB runs on port 27017.
Flask dashboard runs on port 5000.

### Environment variables
In each service folder, except that for mongo, a `.env` file is present, which contains environment variables needed to run each service. As a matter of fact, the only thing that should be inserted in order into each of them to run the code is the openrouteservice API key.
