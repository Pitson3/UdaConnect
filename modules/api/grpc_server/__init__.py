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


class LocationsServicer(locations_pb2_grpc.LocationServiceServicer):
    def Create(self, request, context):
        
        request_value = {
            "person_id": request.person_id,
            "creation_time": request.creation_time,
            "latitude": request.latitude,
            "longitude": request.longitude,
        }

        location = locations_pb2.LocationsMessage(**request_value)
        
        print("The server received the following protobuf message for committing to DB:")
        print(location)

        #DB prep and commits
        new_location = Location()
        new_location.person_id = location.person_id
        new_location.creation_time = location.creation_time
        new_location.coordinate = ST_Point(location.latitude, location.longitude)
        
        with app.app_context():
            db.session.add(new_location)
            db.session.commit()

        print("Finished committing the message")

        return location

class PersonsServicer(persons_pb2_grpc.PersonServiceServicer):
    def Create(self, request, context):
        request_value = {
            "first_name": request.first_name,
            "last_name": request.last_name,
            "company_name": request.company_name,
        }
        #print(request_value)

        person = persons_pb2.PersonsMessage(**request_value)

        print("The server received the following protobuf message for committing to DB:")
        print(person)
        #DB instances and commit
        #P.create(d_msg)
        new_person = Person()
        new_person.first_name = person.first_name
        new_person.last_name = person.last_name
        new_person.company_name = person.company_name

        #db.session.add(new_person)
        #db.session.commit()
        with app.app_context():
            db.session.add(new_person)
            db.session.commit()

        print("Finished committing the message")

        return person


# Initialize gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
locations_pb2_grpc.add_LocationServiceServicer_to_server(LocationsServicer(), server)
persons_pb2_grpc.add_PersonServiceServicer_to_server(PersonsServicer(), server)

print("Server running on port 5005...")
server.add_insecure_port("[::]:5005")
server.start()
# Keep thread alive
try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    server.stop(0)
