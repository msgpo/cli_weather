import datetime
import logging

from rhasspy_weather import utils
from rhasspy_weather.data_types.condition import ConditionType
from rhasspy_weather.data_types.location import Location
from rhasspy_weather.data_types.request import WeatherRequest, DateType, ForecastType, Grain
from rhasspy_weather.data_types.config import get_config

#log = logging.getLogger(__name__)
log = logging.getLogger(__name__)


def parse_cli_args(args):
    intent = None

    config = get_config()

    if args.item is not None:
        intent = ForecastType.ITEM
    elif args.day is not None or args.condition is not None:
        intent = ForecastType.CONDITION
    elif args.temperature is not None:
        intent = ForecastType.TEMPERATURE
    else:
        intent = ForecastType.FULL

    today = datetime.datetime.now(config.timezone).date()

    # define default request
    new_request = WeatherRequest(DateType.FIXED, Grain.DAY, today, intent)

    # if a day was specified
    arg_day = args.day
    if arg_day is not None:
        log.debug("it was a day specified: {0}".format(arg_day))
        arg_day = arg_day.lower()
        named_days_lowercase = [x.lower() for x in config.locale.named_days]
        weekdays_lowercase = [x.lower() for x in config.locale.weekday_names]
        # is it a named day (tomorrow, etc.)?
        if arg_day in named_days_lowercase:
            log.debug("  named day detected")
            index = named_days_lowercase.index(arg_day)
            key = list(config.locale.named_days.keys())[index]
            value = list(config.locale.named_days.values())[index]
            if isinstance(value, datetime.date):
                log.debug("    named day seems to be a date")
                new_request.status.set_status(StatusCode.NOT_IMPLEMENTED_ERROR)
            elif isinstance(value, int):
                log.debug("    named day seems to be an offset from today")
                new_request.request_date = datetime.date.today() + datetime.timedelta(value)
                new_request.date_specified = key
        # is a weekday named?
        elif arg_day in weekdays_lowercase:
            log.debug("  weekday detected")
            index = weekdays_lowercase.index(arg_day)
            name = config.locale.weekday_names[index]
            for x in range(7):
                new_date = today + datetime.timedelta(x)
                if arg_day.lower() == weekdays_lowercase[new_date.weekday()]:
                    new_request.request_date = new_date
                    new_request.date_specified = config.locale.format_userdefined_date(name)
                    break
        # was a date specified (specified by rhasspy as "daynumber monthname")? TODO: also detect month day?
        elif ' ' in arg_day:
            log.debug("  date detected")
            day, month = arg_day.split()
            day = day.lower()
            month = month.lower()
            months_lowercase = [x.lower() for x in config.locale.month_names]
            if month.lower() in months_lowercase:
                index = months_lowercase.index(month)
                name = config.locale.month_names[index]
                new_request.date_specified = config.locale.format_userdefined_date(day + ". " + name)
                # won't work when the year changes, fix that sometime
                try:
                    new_request.request_date = datetime.date(datetime.date.today().year, index + 1, int(day))
                except ValueError:
                    new_request.status.set_status(StatusCode.DATE_ERROR)

        # if a time was specified - this is only evaluated if day was given - TODO: why? decouple!
        arg_time = args.time
        if arg_time is not None:
            arg_time = arg_time.lower()
            log.debug("it was a time specified: {0}".format(arg_time))
            new_request.grain = Grain.HOUR

            named_times_lowercase = [x.lower() for x in config.locale.named_times]
            named_times_synonyms_lowercase = [x.lower() for x in config.locale.named_times_synonyms]
            named_times_combined = named_times_lowercase + named_times_synonyms_lowercase
            # was something like midday specified (listed in locale.named_times or in locale.named_times_synonyms)?
            if arg_time in named_times_combined:
                log.debug("  named time frame detected: {0}".format(arg_time))
                if arg_time in named_times_synonyms_lowercase:
                    index = named_times_synonyms_lowercase.index(arg_time)
                    name = list(config.locale.named_times_synonyms.keys())[index]
                    value = config.locale.named_times[config.locale.named_times_synonyms[name]]
                else:
                    index = named_times_lowercase.index(arg_time)
                    name = list(config.locale.named_times.keys())[index]
                    value = list(config.locale.named_times.values())[index]
                log.debug(value)
                if isinstance(value, datetime.time):
                    log.debug("    named time seems to be a certain time")
                    new_request.start_time = value
                    new_request.time_specified = name
                elif isinstance(value, tuple):
                    log.debug("    named time seems to be an interval")
                    new_request.date_type = DateType.INTERVAL
                    new_request.start_time = value[0]
                    new_request.end_time = value[1]
                    new_request.time_specified = name
            # was it hours and minutes (specified as "HH MM" by rhasspy intent)?
            elif ' ' in arg_time:
                log.debug("    hours and minutes detected")
                new_request.start_time = datetime.datetime.strptime(arg_time, '%H %M').time()
                new_request.time_specified = config.locale.format_userdefined_time(new_request.start_time.hour, new_request.start_time.minute)
            # is it only an hour (no way to only specify minutes, if it is an int, it is hours)?
            elif arg_time.isdigit():
                log.debug("    hours detected")
                new_request.start_time = datetime.time(int(arg_time), 0)
                new_request.time_specified = config.locale.format_userdefined_time(new_request.start_time.hour)
            else:
                new_request.grain = Grain.DAY
        else:
            log.debug("no time specified, getting weather for the full day")
    else:
        log.debug("no day specified, using today as default")

    # requested
    requested = None
    arg_condition = args.condition
    arg_item = args.item
    arg_temperature = args.temperature
    log.debug("intent: {}".format(intent))
    if intent == ForecastType.CONDITION:
        arg_condition = arg_condition.lower()
        log.debug("condition requested: {}".format(arg_condition))
        if arg_condition in config.locale.requested_condition:
            requested = config.locale.requested_condition[arg_condition]
        else:
            requested = ConditionType.UNKNOWN
        log.debug("condition type derived: {}".format(requested))
    elif intent == ForecastType.ITEM:
        log.debug("item requested: {}".format(arg_item))
        requested = arg_item.lower() # uses capitalize in rhasspy_intent -> TODO: report consistency problem - using lower, works for English
    elif intent == ForecastType.TEMPERATURE:
        arg_temperature = arg_temperature.lower()
        log.debug("temperature condition requested: {}".format(arg_temperature))
        if arg_temperature in config.locale.requested_temperature:
            requested = config.locale.requested_temperature[arg_temperature]
        log.debug("temperature condition selected: {}".format(requested))

    if requested is not None:
        log.debug("there was a special request made")
        new_request.requested = requested

    # location
    arg_location = args.location
    if arg_location is not None:
        log.debug("a location was specified")
        new_request.location = Location(arg_location)

    return new_request
