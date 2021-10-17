from flask import Flask
from kafka import KafkaConsumer
import time
from concurrent import futures
import grpc
import locations_pb2
import persons_pb2
import locations_pb2_grpc
import persons_pb2_grpc
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import json

from app import db
from app.udaconnect.models import Connection, Location, Person
from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text
from app.config import config_by_name

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("kafka-location-and-person-consumers-services")

app = Flask(__name__)
app.config.from_object(config_by_name["prod"])
db.init_app(app)



TOPIC_NAME = 'udaconnect'

def create_person(person):
    print("Sending received person payloads for grpc processing  while kafka commit the message to database...")

    channel = grpc.insecure_channel("localhost:5005")

    person_stub = persons_pb2_grpc.PersonServiceStub(channel)

    # Update this with desired payload
    persons = persons_pb2.PersonsMessage(
            first_name = person["first_name"],
            last_name = person["last_name"],
            company_name = person["company_name"]
        )

    person_stub.Create(persons)


def create_location(location):
        print("Sent the received location payloads for grpc processing..")

        channel = grpc.insecure_channel("localhost:5005")
        location_stub = locations_pb2_grpc.LocationServiceStub(channel)

        # Update this with desired payload
        locations = locations_pb2.LocationsMessage(
            person_id=location["person_id"],
            creation_time=location["creation_time"],
            latitude=location["latitude"],
            longitude=location["longitude"]
            )
        
        location_stub.Create(locations)
        

consumer = KafkaConsumer(TOPIC_NAME,bootstrap_servers=['localhost:9092'])

for message in consumer:
    d_msg = json.loads((message.value.decode('utf-8'))) #message.value.decode()
    
    if 'first_name' in d_msg:
        create_person(d_msg)
    elif 'latitude' in d_msg or 'longitude' in d_msg:
        create_location(d_msg)
    else:
        logger.warning ("Failed to process the message as the message was not understood for the use case.")
