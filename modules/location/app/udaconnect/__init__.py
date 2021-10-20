from app.udaconnect.models import Connection, Location  # noqa
from app.udaconnect.schemas import ConnectionSchema, LocationSchema # noqa

#Routes
def register_routes(api, app, root="api"):
    from app.udaconnect.controllers import api as udaconnect_api

    api.add_namespace(udaconnect_api, path=f"/{root}")
