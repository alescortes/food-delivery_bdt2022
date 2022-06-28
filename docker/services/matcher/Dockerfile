FROM python:3.8

# create and set working directory
RUN mkdir -p /opt/food-delivery
WORKDIR /opt/generator

ADD src/requirements.txt .

# install libraries
RUN pip install -r requirements.txt

# add sourcecode and settings
ADD src .

# running the food-delivery with "-u" flag so that every request gets printed exactly when it is generated.

CMD ["python", "-u", "match_delivery_client.py"]
