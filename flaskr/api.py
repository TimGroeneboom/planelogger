import json
from datetime import datetime, timedelta
from flask import Blueprint
from ovm.complainant import Complainant
from ovm.disturbancefinder import DisturbanceFinder
from ovm.environment import load_environment
from ovm.utils import DataclassJSONEncoder, convert_int_to_datetime

# Create api page
api_page = Blueprint('api', __name__, template_folder='templates')

# Load environment
environment = load_environment('environment.json')


@api_page.route('/api/find_disturbance/<string:user>/'
                '<float:lat>/<float:lon>/'
                '<int:radius>/<int:altitude>/'
                '<int:occurrences>/<int:timeframe>/'
                '<int:plot>/<int:zoomlevel>')
def find_disturbance(user,
                     lat,
                     lon,
                     radius,
                     altitude,
                     occurrences,
                     timeframe,
                     plot,
                     zoomlevel):
    complainants = [Complainant(user=user,
                                origin=(lat, lon),
                                radius=radius,
                                altitude=altitude,
                                occurrences=occurrences,
                                timeframe=timeframe)]

    now = datetime.now()
    disturbance_finder: DisturbanceFinder = DisturbanceFinder(environment)
    disturbances = disturbance_finder.find_disturbances(begin=now - timedelta(hours=24),
                                                        end=now,
                                                        complainants=complainants,
                                                        zoomlevel=zoomlevel,
                                                        plot=plot)
    return json.dumps(disturbances, cls=DataclassJSONEncoder, indent=4)


@api_page.route('/api/find_flights/<string:user>/'
                '<float:lat>/<float:lon>/'
                '<int:radius>/<int:altitude>/'
                '<int:begin>/<int:end>/'
                '<int:plot>/<int:zoomlevel>')
def find_flights(user,
                 lat,
                 lon,
                 radius,
                 altitude,
                 begin,
                 end,
                 plot,
                 zoomlevel):
    disturbance_finder: DisturbanceFinder = DisturbanceFinder(environment)
    flights = disturbance_finder.find_flights(origin=(lat, lon),
                                              begin=convert_int_to_datetime(begin),
                                              end=convert_int_to_datetime(end),
                                              radius=radius,
                                              altitude=altitude,
                                              title=user,
                                              plot=plot,
                                              zoomlevel=zoomlevel)
    return json.dumps(flights, cls=DataclassJSONEncoder, indent=4)
