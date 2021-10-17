import logging
from datetime import datetime, timedelta
from typing import Dict, List

from app import db
from app.udaconnect.models import Location
from app.udaconnect.schemas import LocationSchema
from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text
from kafka import KafkaProducer

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("location-api")
import json

TOPIC_NAME = 'udaconnect'
KAFKA_SERVER = 'localhost:9092'
producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)


class LocationService:
    @staticmethod
    def retrieve(location_id) -> Location:
        """"
        Provision For kafka production so as to allow the capturing of location_id for kafka_consumer processing
        """
        #producer.send(TOPIC_NAME, json.dumps(location_id).encode())
        #producer.flush()
        
        location, coord_text = (
            db.session.query(Location, Location.coordinate.ST_AsText())
            .filter(Location.id == location_id)
            .one()
        )

        # Rely on database to return text form of point to reduce overhead of conversion in app code
        location.wkt_shape = coord_text
        return location

    @staticmethod
    def create(location: Dict) -> Location:
        """"
        Capture the location data for kafka processing->Person Creation
        """
        producer.send(TOPIC_NAME, json.dumps(location).encode())
        producer.flush()
        
        #Data for REST processing
        validation_results: Dict = LocationSchema().validate(location)
        if validation_results:
            logger.warning(f"Unexpected data format in payload: {validation_results}")
            raise Exception(f"Invalid payload: {validation_results}")

        
        new_location = Location()
        new_location.person_id = location["person_id"]
        new_location.creation_time = location["creation_time"]
        new_location.coordinate = ST_Point(location["latitude"], location["longitude"])
        
        db.session.add(new_location)
        db.session.commit()

        #return new_location
        #return {'id':new_location.id, 'person_id':new_location.person_id, 'coordinate':new_location.coordinate, 'creation_time' : new_location.creation_time}
        return "Your request has been sent for processing to an external service."
