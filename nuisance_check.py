# Import the python libraries
import collections
import datetime
import math

import pymongo
import pymongo as pymongo
from pymongo import MongoClient
import geopy.distance
from ovm import environment
from ovm.disturbanceperiod import DisturbancePeriod
from ovm.plotter import Plotter
from ovm.utils import *

# Nuisance parameters

# Christoffelkruidstraat
origin = (52.396172234741506, 4.905621078252285)
# Amsterdamse Bos
#origin = (52.311502, 4.827680)
# Assendelft
#origin = (52.469640, 4.721354)
radius = 1250
altitude = 1000
occurrences = 4
timeframe = 60

# Load environment
environment = environment.load_environment('environment.json')

# Choose the appropriate client
client = MongoClient(environment.mongodb_config.host, environment.mongodb_config.port)

# Ignore certain callsigns
ignore_callsigns = [
    'LIFELN1'
]


def ignore_callsign(callsign: str):
    for other in ignore_callsigns:
        if callsign_compare(callsign, other):
            return True

    return False


disturbance_callsigns: dict = {}
disturbance_periods = []
last_timestamp: datetime
disturbance_begin: datetime
last_disturbance: datetime
disturbance_hits = 0
in_disturbance = False
states_collection = client[environment.mongodb_config.database][environment.mongodb_config.collection]
cursor = states_collection.find({})

# Iterate through states
for document in cursor:
    timestamp_int = document['Time']
    timestamp = convert_int_to_datetime(timestamp_int)
    states = document['States']
    disturbance_in_this_timestamp = False

    for state in states:
        # Get callsign
        callsign = state['callsign']

        # Ignore grounded planes
        if state['baro_altitude'] is None:
            continue

        # Ignore specified callsigns
        if ignore_callsign(callsign):
            continue

        # Check if altitude is lower than altitude and if distance is within specified radius
        if state['baro_altitude'] < altitude:
            coord = (state['latitude'], state['longitude'])
            distance = geopy.distance.distance(origin, coord).meters
            if distance < radius:
                disturbance_hits += 1

                # Check if there already is a disturbance in this timeframe, otherwise create a new disturbance
                disturbance_in_this_timestamp = True
                if not in_disturbance:
                    in_disturbance = True
                    disturbance_begin = timestamp
                    last_disturbance = timestamp
                else:
                    diff_since_begin = timestamp - disturbance_begin
                    diff_since_last = timestamp - last_disturbance
                    last_disturbance = timestamp

                # if callsign is not already logged for this disturbance, do it now
                if callsign not in disturbance_callsigns.keys():
                    disturbance_callsigns[callsign] = timestamp_int

    # Check if disturbance has ended and if we need to generate a complaint within set parameters
    if not disturbance_in_this_timestamp:
        if in_disturbance:
            diff_since_last = timestamp - last_disturbance
            disturbance_duration = last_disturbance - disturbance_begin
            diff_since_begin = timestamp - disturbance_begin
            if (diff_since_last.seconds / 60) >= timeframe:
                if disturbance_hits >= occurrences:
                    disturbance_complaint = DisturbancePeriod(origin,
                                                              radius,
                                                              disturbance_callsigns.copy(),
                                                              disturbance_begin,
                                                              last_disturbance,
                                                              disturbance_hits)
                    disturbance_periods.append(disturbance_complaint)

                in_disturbance = False
                disturbance_begin = None
                last_disturbance = None
                disturbance_hits = 0
                disturbance_callsigns = {}

    last_timestamp = timestamp

# Handle disturbance if we finished in disturbance state
if in_disturbance:
    diff_since_last = timestamp - last_disturbance
    disturbance_duration = last_disturbance - disturbance_begin
    diff_since_begin = timestamp - disturbance_begin

    if disturbance_hits >= occurrences:
        if (disturbance_duration.seconds / 60) > timeframe:
            disturbance_complaint = DisturbancePeriod(origin,
                                                      radius,
                                                      disturbance_callsigns.copy(),
                                                      disturbance_begin,
                                                      last_disturbance,
                                                      disturbance_hits)
            disturbance_periods.append(disturbance_complaint)


# Calc trajectories for generate complaints for callsigns
index = 0
for disturbance_period in disturbance_periods:
    # Calc disturbance duration
    disturbance_duration = disturbance_period.end - disturbance_period.begin
    print('Disturbance detected. %i hits and a total duration of %i minutes\n'
          'Disturbance began at %s and ended at %s' %
          (disturbance_period.hits, (disturbance_duration.seconds / 60),
           disturbance_period.begin.__str__(), disturbance_period.end.__str__()))

    # Create trajectories for complaint
    for callsign, datetime_int in disturbance_period.disturbance_callsigns.items():
        # Gather states before and after this entry to plot a trajectory for callsign
        dictionary = {}
        items_before = states_collection.find({'Time': {'$gte': datetime_int}}).limit(4)
        items_after = states_collection.find({'Time': {'$lte': datetime_int}}).sort(
            [('Time', pymongo.DESCENDING)]).limit(4)
        for doc in items_before:
            timestamp_int = doc['Time']
            if timestamp_int not in dictionary.keys():
                dictionary[timestamp_int] = doc['States']
        for doc in items_after:
            timestamp_int = doc['Time']
            if timestamp_int not in dictionary.keys():
                dictionary[timestamp_int] = doc['States']

        # Order found states and create the trajectory of disturbance callsign
        trajectory = []
        ordered_dict = collections.OrderedDict(sorted(dictionary.items()))
        for key, value in ordered_dict.items():
            for state in value:
                if state['callsign'] == callsign:
                    coord = (state['longitude'], state['latitude'])
                    trajectory.append(coord)

        # Add it to the trajectories of this complaint
        disturbance_period.trajectories[callsign] = trajectory

    # Set the bounding box for our area of interest
    r_earth = 6378
    padding = 1000
    lat_min = disturbance_period.coord[0] - (((radius + padding) / 1000.0) / r_earth) * (180.0 / math.pi)
    lon_min = disturbance_period.coord[1] - (((radius + padding) / 1000.0) / r_earth) * (180.0 / math.pi) / math.cos(disturbance_period.coord[0] * math.pi / 180.0)
    lat_max = disturbance_period.coord[0] + (((radius + padding) / 1000.0) / r_earth) * (180.0 / math.pi)
    lon_max = disturbance_period.coord[1] + (((radius + padding) / 1000.0) / r_earth) * (180.0 / math.pi) / math.cos(disturbance_period.coord[0] * math.pi / 180.0)

    # Make plot of all callsign trajectories
    index += 1
    plotter = Plotter()
    plotter.plot_trajectories(bbox=(lat_min, lat_max, lon_min, lon_max),
                              disturbance_period=disturbance_period,
                              tile_zoom=14,
                              figsize=(10,10),
                              filename=('complaint%i.jpg' % index))
