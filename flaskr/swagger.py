from flasgger import LazyString
from flask import request

# Setup swagger template
swagger_template = dict(
    info= ***REMOVED***
        'title': LazyString(lambda: 'Air Traffic Disturbance Logger & Plotter'),
        'version': LazyString(lambda: '1.0.1'),
        'description': LazyString(lambda: 'This document describes the Air Traffic Disturbance Logger & Plotter REST API'),
  ***REMOVED***
    host=LazyString(lambda: request.host)
)

# Setup swagger config
swagger_config = ***REMOVED***
    "headers": [],
    "specs": [
        ***REMOVED***
            "endpoint": 'get_trajectory',
            "route": '/swagger/get_trajectory.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
      ***REMOVED***
        ***REMOVED***
            "endpoint": 'find_disturbances',
            "route": '/swagger/find_disturbances.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
      ***REMOVED***
        ***REMOVED***
            "endpoint": 'find_flights',
            "route": '/swagger/find_flights.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
      ***REMOVED***
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
***REMOVED***