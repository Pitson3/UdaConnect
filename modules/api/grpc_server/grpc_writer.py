import grpc
import locations_pb2
import persons_pb2
import locations_pb2_grpc
import persons_pb2_grpc

"""
Sample implementation of a writer that can be used to write messages to gRPC.
"""

print("Sending sample payloads...")

channel = grpc.insecure_channel("localhost:5005")
location_stub = locations_pb2_grpc.LocationServiceStub(channel)
person_stub = persons_pb2_grpc.PersonServiceStub(channel)

# Update this with desired payload
locations = locations_pb2.LocationsMessage(
    person_id=3,
    creation_time='18:00 hrs GMT+2',
    latitude='iijjnnnn',
    longitude='TechNix Malawi'
)

persons = persons_pb2.PersonsMessage(
    id = 1,
    first_name = 'Pitson',
    last_name = 'Josiah',
    company_name = 'TechNix'
)


response = location_stub.Create(locations)
response = person_stub.Create(persons)
