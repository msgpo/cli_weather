# cli_weather
A command line client to give you a written weather forecast for different requests. This forecast can then be piped into a speech to text tool and played via a voice assistant or smart speaker.

It depends on https://github.com/ulno/rhasspy_weather which is forked from https://github.com/Daenara/rhasspy_weather

To use clone the following way: 
```bash
git clone --recursive https://github.com/ulno/cli_weather
```
Don't forget to use ``--recursive`` to get the dependencies.

To run, run
```bash
python3 cli_weather.py --help
```

TODO: list options+explanations here

## Notes

- Do not forget to configure config.ini in rhasspy_weather
- Make sure to have all dependencies installed: dependency on arch (for rhasspy weather): python-suntime (AUR), python-pytz
- If you want to send the event message from rhasspy out of node-red to an exec node, use a JSONata change with content ``"'" & json_message & "'"``. Put ``python3 <install_path>/cli_weather/cli_weather.py --json `` as command into the exec node and check to append the payload.