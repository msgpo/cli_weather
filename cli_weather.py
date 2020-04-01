# -*- encoding: utf-8 -*-
"""
Command line interface for rhasspy_weather.
"""
# author: ulno
# created: 2020-03-31


import sys

import logging
log = logging.getLogger(__name__)

import globals
from data_types.config import WeatherConfig
from data_types.report import WeatherReport

# hack to allow correct locale to be used in argparse
syspath_backup = sys.path
sys.path=[]
for p in syspath_backup:
    if "weather" not in p:
        sys.path.append(p)
import argparse


# function being called when snips detects an intent related to the weather
def get_weather_forecast(args):
    log.info("Loading Config")
    globals.config = WeatherConfig()
    config = globals.config

    if config.status.is_error:
        return config.status.status_response()

    log.info("Parsing rhasspy intent")
    request = config.parser.parse_cli_args(args)
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
    parser.add_argument('-d', '--day', help='Forecast day.')  # when_day
    parser.add_argument('-t', '--time', help='Forecast time')  # when_time
    parser.add_argument('-l', '--location', help='Forecast location')  # location
    parser.add_argument('-i', '--item', help='Is a specific item (like umbrella) needed/recommended.')  # item
    parser.add_argument('-c', '--condition', help='Is a specific condition active at given time.')  # condition
    parser.add_argument('-e', '--temperature', help='Temperature forecast.')  # temperature

    args = parser.parse_args()
    sys.path = syspath_backup  # restore sys path to allow local locale to be used
    print(get_weather_forecast(args))


if __name__ == '__main__':
    raise Exception("cli cannot be called from here, call package")