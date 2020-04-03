# -*- encoding: utf-8 -*-
"""
Command line interface for rhasspy_weather.
"""
# author: ulno
# created: 2020-03-31


import sys
import json

import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

import rhasspy_weather.globals as globals
from rhasspy_weather.data_types.config import WeatherConfig
from rhasspy_weather.data_types.report import WeatherReport

from cli_parser import parse_cli_args
from rhasspy_weather.parser.rhasspy_intent import parse_intent_message

# # hack to allow correct locale to be used in argparse - TODO: check, might me obsolete due to changes upstream
# syspath_backup = sys.path
# sys.path=[]
# for p in syspath_backup:
#     if "weather" not in p:
#         sys.path.append(p)
import argparse


# handling the steps necessary to do a forecast
def get_weather_forecast(args):
    log.info("Loading Config")
    globals.config = WeatherConfig()
    config = globals.config

    if config.status.is_error:
        return config.status.status_response()

    log.info("Parsing rhasspy intent")

    if args.json is not None:
        if args.json == "-":
            # read and parse json from stdin and send it to rhasspy_weather
            data = json.load(sys.stdin)
        else:
            data = json.loads(args.json)
        request = parse_intent_message(data)
    else:
#        request = config.parser.parse_cli_args(args)  # if the parser got moved to rhasspy_weather it would be called like this
        request = parse_cli_args(args)


    if request.status.is_error:
        return request.status.status_response()

    log.info("Requesting weather")
    forecast = config.api.get_weather(request.location)
    if forecast.status.is_error:
        return forecast.status.status_response()

    log.info("Formulating answer")
    response = WeatherReport(request, forecast).generate_report()

    return response


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--day', help='Forecast day (sunday, monday, ...) or "day month".')  # when_day
    parser.add_argument('-t', '--time', help='Forecast time')  # when_time
    parser.add_argument('-l', '--location', help='Forecast location')  # location
    parser.add_argument('-i', '--item', help='Is a specific item (like umbrella) needed/recommended.')  # item
    parser.add_argument('-c', '--condition', help='Is a specific condition active at given time.')  # condition
    parser.add_argument('-e', '--temperature', help='Temperature forecast.')  # temperature
    parser.add_argument('-j', '--json', help="Receive json in rhasspy intent event format as one parameter string or via stdin when this is set to a dash (-) and forward that to rhasspy_weather component.")

    args = parser.parse_args()
    # sys.path = syspath_backup  # restore sys path to allow local locale to be used - TODO: still necessary?
    print(get_weather_forecast(args))


if __name__ == '__main__':
    parse()