import base64
import json
import uuid
from datetime import datetime, timedelta
import os
from dataclasses import field
import requests
from flask import Blueprint, request, render_template
from requests import Response

from ovm.utils import convert_datetime_to_int, convert_int_to_datetime
import filehandler

# Create test api page
test_api_page = Blueprint('testapi', __name__, template_folder='templates')


class RenderDisturbance:
    file: str = field(default_factory=str)
    begin: str = field(default_factory=str)
    end: str = field(default_factory=str)
    callsigns: list = field(default_factory=list)
    plot: bool = field(default_factory=bool)


def handle_response(response: Response):
    response_json = response.json()
    if response_json['status'] != 'OK':
        raise Exception(response_json['value'])
    return json.loads(response_json['value'])


@test_api_page.route("/api_test/find_disturbances", methods=["GET", "POST"])
def find_disturbances():
    if request.method == "POST":
        try:
            d = request.form
            url = 'http://%s/api/find_disturbance/%s/%f/%f/%i/%i/%i/%i/%i/%i' % \
                  (request.host,
                   d['user'],
                   float(d['lat']),
                   float(d['lon']),
                   int(d['radius']), int(d['altitude']),
                   int(d['occurrences']),
                   int(d['timeframe']),
                   int('plot' in d),
                   int(d['zoomlevel']))
            disturbances = handle_response(requests.get(url))

            render_disturbances = []
            for user, found_disturbances in disturbances.items():
                for disturbance in found_disturbances['disturbances']:
                    render_disturbance = RenderDisturbance()
                    render_disturbance.file = ""
                    render_disturbance.begin = disturbance['begin']
                    render_disturbance.end = disturbance['end']
                    render_disturbance.callsigns = []
                    for callsign in disturbance['callsigns']:
                        render_disturbance.callsigns.append('%s : %s ' % (callsign['callsign'],
                                                                          convert_int_to_datetime(
                                                                              callsign['datetime']).__str__()))

                    if disturbance['img'] is not None and len(disturbance['img']) > 0:
                        filename = os.path.join(filehandler.temp_dir_name, '%i_%s_%s.jpg' % (uuid.uuid4().int,
                                                                                             user,
                                                                                             disturbance['begin']))
                        file_to_disk = os.path.join(filehandler.static_dir, filename)
                        with open(file_to_disk, 'wb') as fh:
                            fh.write(base64.decodebytes(bytes(disturbance['img'], "utf-8")))
                            fh.close()
                        render_disturbance.file = filename
                        render_disturbance.plot = True
                    else:
                        render_disturbance.plot = False
                    render_disturbances.append(render_disturbance)

            return render_template("api/find_disturbances_result.html",
                                   disturbances=render_disturbances)
        except Exception as ex:
            return ex.__str__()

    return render_template("api/find_disturbances.html")


@test_api_page.route("/api_test/find_flights", methods=["GET", "POST"])
def find_flights():
    if request.method == "POST":
        try:
            d = request.form
            user = d['user']
            url = 'http://%s/api/find_flights/%s/%f/%f/%i/%i/%i/%i/%i/%i' % \
                  (request.host,
                   user,
                   float(d['lat']),
                   float(d['lon']),
                   int(d['radius']),
                   int(d['altitude']),
                   convert_datetime_to_int(datetime.strptime(d['begin'], '%Y-%m-%dT%H:%M')),
                   convert_datetime_to_int(datetime.strptime(d['end'], '%Y-%m-%dT%H:%M')),
                   int('plot' in d),
                   int(d['zoomlevel']))

            disturbances = handle_response(requests.get(url))

            render_disturbances = []
            for disturbance in disturbances['disturbances']:
                render_disturbance = RenderDisturbance()
                render_disturbance.file = ""
                render_disturbance.begin = disturbance['begin']
                render_disturbance.end = disturbance['end']
                render_disturbance.callsigns = []
                for callsign in disturbance['callsigns']:
                    render_disturbance.callsigns.append('%s : %s ' % (callsign['callsign'],
                                                                      convert_int_to_datetime(
                                                                          callsign['datetime']).__str__()))

                if disturbance['img'] is not None and len(disturbance['img']) > 0:
                    filename = os.path.join(filehandler.temp_dir_name, '%i_%s_%s.jpg' % (uuid.uuid4().int,
                                                                                         user,
                                                                                         disturbance['begin']))
                    file_to_disk = os.path.join(filehandler.static_dir, filename)
                    with open(file_to_disk, 'wb') as fh:
                        fh.write(base64.decodebytes(bytes(disturbance['img'], "utf-8")))
                        fh.close()
                    render_disturbance.file = filename
                    render_disturbance.plot = True
                else:
                    render_disturbance.plot = False
                render_disturbances.append(render_disturbance)

            return render_template("api/find_flights_result.html",
                                   disturbances=render_disturbances)
        except Exception as ex:
            return ex.__str__()

    now = datetime.now()
    yesterday = now - timedelta(hours=24)
    return render_template("api/find_flights.html",
                           begin=yesterday.strftime('%Y-%m-%d %H:%M'),
                           end=now.strftime('%Y-%m-%d %H:%M'))
