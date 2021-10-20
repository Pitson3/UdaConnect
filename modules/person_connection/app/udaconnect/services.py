import logging
from datetime import datetime, timedelta
from typing import Dict, List

import json
from app import db
from app.udaconnect.models import Connection, Person, Location
from app.udaconnect.schemas import ConnectionSchema, PersonSchema, LocationSchema
from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text

from kafka import KafkaProducer
from flask import jsonify

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("personal-connections-api")


TOPIC_NAME = 'udaconnect'
KAFKA_SERVER = 'kafka.default.svc.cluster.local:9092'
print("Creating a kafka producer")
producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)

print("Kafka producer initiated")


class ConnectionService:
    @staticmethod
    def find_contacts(person_id: int, start_date: datetime, end_date: datetime, meters=5
    ) -> List[Connection]:
        """
        Finds all Person who have been within a given distance of a given Person within a date range.

        This will run rather quickly locally, but this is an expensive method and will take a bit of time to run on
        large datasets. This is by design: what are some ways or techniques to help make this data integrate more
        smoothly for a better user experience for API consumers?
        """
        locations: List = db.session.query(Location).filter(
            Location.person_id == person_id
        ).filter(Location.creation_time < end_date).filter(
            Location.creation_time >= start_date
        ).all()

        # Cache all users in memory for quick lookup
        person_map: Dict[str, Person] = {person.id: person for person in PersonService.retrieve_all()}

        # Prepare arguments for queries
        data = []
        for location in locations:
            data.append(
                {
                    "person_id": person_id,
                    "longitude": location.longitude,
                    "latitude": location.latitude,
                    "meters": meters,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": (end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                }
            )

        query = text(
            """
        SELECT  person_id, id, ST_X(coordinate), ST_Y(coordinate), creation_time
        FROM    location
        WHERE   ST_DWithin(coordinate::geography,ST_SetSRID(ST_MakePoint(:latitude,:longitude),4326)::geography, :meters)
        AND     person_id != :person_id
        AND     TO_DATE(:start_date, 'YYYY-MM-DD') <= creation_time
        AND     TO_DATE(:end_date, 'YYYY-MM-DD') > creation_time;
        """
        )
        result: List[Connection] = []
        for line in tuple(data):
            for (
                exposed_person_id,
                location_id,
                exposed_lat,
                exposed_long,
                exposed_time,
            ) in db.engine.execute(query, **line):
                location = Location(
                    id=location_id,
                    person_id=exposed_person_id,
                    creation_time=exposed_time,
                )
                location.set_wkt_with_coords(exposed_lat, exposed_long)

                result.append(
                    Connection(
                        person=person_map[exposed_person_id], location=location,
                    )
                )
        #producer.send(TOPIC_NAME, result)

        return result



class PersonService:
    @staticmethod
    def create(person: Dict) -> Person:
        """"
        Capture the person data for kafka processing->Person Creation
        """
        new_person = json.dumps(person).encode()

        producer.send(TOPIC_NAME, new_person)
        producer.flush()
        
        #Capture the passed data for REST processing
        #new_person = Person()
        #new_person.first_name = person["first_name"]
        #new_person.last_name = person["last_name"]
        #new_person.company_name = person["company_name"]

        #db.session.add(new_person)
        #db.session.commit()
        
        
        
        #return new_person
        #return {'id': new_person.id, 'first_name': new_person.first_name, 'last_name': new_person.last_name, 'company_name':new_person.company_name}
        return "The request has been sent for processing to an external service."
    @staticmethod
    def retrieve(person_id: int) -> Person:
        """"
        For kafka production so as to allow the capturing of person_id for kafka_consumer processing

        Reserved for research (Will we be able to return the processed kafka values to REST for rest get endpoints)
        """
        #producer.send(TOPIC_NAME, json.dumps(person_id).encode())
        #producer.flush()

        person = db.session.query(Person).get(person_id)
        
        return person

    @staticmethod
    def retrieve_all() -> List[Person]:
        result = db.session.query(Person).all()
        
        return result
