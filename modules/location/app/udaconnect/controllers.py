from datetime import datetime

from app.udaconnect.models import Location
from app.udaconnect.schemas import (
    LocationSchema,
)
from app.udaconnect.services import  LocationService
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from flask import request
from typing import Optional, List


DATE_FORMAT = "%Y-%m-%d"

api = Namespace("UdaConnect", description="Connections via geolocation.")  # noqa


# TODO: This needs better exception handling


@api.route("/locations")
@api.route("/locations/<location_id>")
@api.param("location_id", "Unique ID for a given Location", _in="query")
class LocationResource(Resource):
    #@accepts(schema=LocationSchema)
    #@responds(schema=LocationSchema)
    def post(self) -> Location:
        payload = {'person_id': request.args.get('person_id'), 'creation_time':request.args.get('creation_time'), 'latitude': request.args.get('latitude'), 'longitude': request.args.get('longitude')} #request.get_json()
        location: Location = LocationService.create(payload)
        return location

    #@responds(schema=LocationSchema)
    def get(self, location_id) -> Location:
        location: Location = LocationService.retrieve(location_id)
        return location

