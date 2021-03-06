#!/usr/bin/env python3
"Sky - A simple weather monitor"

import re
import sqlite3
from datetime import datetime
from textwrap import wrap

import darksky
from flask import Flask
from mapbox import Geocoder
from pytz import timezone

import config
from columnizer import Columnizer
from ascii import arts

GEOCODER = Geocoder(access_token=config.mapbox_key)
APP = Flask(__name__)
CACHE_DB = sqlite3.connect("cache.sqlite", check_same_thread=False)


def get_coordinates(location, geocoder, cache_db):
    "Returns the coordinates for a given location"
    row = cache_db.execute("select lat,lon,full_name from location where "
                           "name = ?", (location,)).fetchone()

    if row is not None:
        return (row[0], row[1], row[2])

    loc = geocoder.forward(location)
    coordinates = loc.geojson()['features'][0]['center']
    name = loc.geojson()['features'][0]['place_name']
    cache_db.execute("insert into location(name, lon, lat, full_name) values("
                     "?,?,?,?)", (location, *coordinates, name))
    return (coordinates[1], coordinates[0], name)


def get_weather(coordinates):
    "Returns the forecast from the coordinates"
    return darksky.forecast(config.dark_sky_key, coordinates[0],
                            coordinates[1])


def summary_to_c(summary):
    "Converts Fahrenheits to Celsius in a string"
    # pylint: disable=invalid-name
    for i in re.findall(r"[\d.]+°F", summary):
        f = float(i[:-2])
        c = 5 * (f - 32)/9
        summary = re.sub(i, f"{c:3.3}°C", summary)
    return summary


def weather_to_text(forecast, kind, unit, name):
    "Converts the forecast to text"
    text = name + "\n"
    if unit == "c":
        text += summary_to_c(forecast[kind]["summary"]) + "\n\n"
    else:
        text += forecast[kind]["summary"] + "\n\n"
    row_0 = Columnizer()
    row_1 = Columnizer()
    # Add today
    today = [
        "Current",
        "",
        *arts[forecast["currently"]["icon"]],
        ""
    ]
    if unit == "c":
        today += ["{0:.1f}°C".format(
            5*(forecast["currently"]["temperature"]-32)/9)]
    else:
        today += [str(forecast["currently"]["temperature"]) + "°F"]
    today += [""]
    if kind == "daily":
        today += [""]
    today += wrap(forecast["currently"]["summary"], 18)
    row_0.add_column(today)
    count = 1
    if kind == "daily":
        diff = 1
    elif kind == "hourly":
        diff = 3
    for j in range(0, len(forecast[kind]["data"]), diff):
        i = forecast[kind]["data"][j]
        x = []
        date = datetime.fromtimestamp(i["time"],
                                      timezone(forecast["timezone"]))
        if kind == "daily":
            x += date.strftime("%d %B\n%A").split("\n")
        elif kind == "hourly":
            x += [date.strftime("%H:%M"), ""]
        x += [*arts[i["icon"]]]
        x += [""]
        if unit == "c":
            if kind == "daily":
                x += ["Max: {0:.1f}°C".format(5*(i["temperatureMax"]-32)/9)]
                x += ["Min: {0:.1f}°C".format(5*(i["temperatureMin"]-32)/9)]
            elif kind == "hourly":
                x += ["Temp: {0:.1f}°C".format(5*(i["temperature"]-32)/9)]
        else:
            if kind == "daily":
                x += ["Max: {0:.1f}°F".format(i["temperatureMax"])]
                x += ["Min: {0:.1f}°F".format(i["temperatureMin"])]
            elif kind == "hourly":
                x += ["Temp: {0:.1f}°F".format(i["temperature"])]
        x += [""]
        x += wrap(i["summary"], 18)
        if count < 4:
            row_0.add_column(x)
        elif count < 8:
            row_1.add_column(x)
        else:
            break
        count += 1
    for i in forecast[kind]["data"]:
        x = []
        date = datetime.fromtimestamp(i["time"],
                                      timezone(forecast["timezone"]))
        x += date.strftime("%d %B\n%A").split("\n")
        x += [*arts[i["icon"]]]
        x += [""]
        if unit == "c":
            if kind == "daily":
                x += ["Max: {0:.1f}°C".format(5*(i["temperatureMax"]-32)/9)]
                x += ["Min: {0:.1f}°C".format(5*(i["temperatureMin"]-32)/9)]
            elif kind == "hourly":
                x += ["Temp: {0:.1f}°C".format(5*(i["temperature"]-32)/9)]
        else:
            if kind == "daily":
                x += ["Max: {0:.1f}°F".format(i["temperatureMax"])]
                x += ["Min: {0:.1f}°F".format(i["temperatureMin"])]
            elif kind == "hourly":
                x += ["Temp: {0:.1f}°F".format(i["temperature"])]
        # x += [i["summary"]]
        if count < 4:
            row_0.add_column(x)
        elif count < 8:
            row_1.add_column(x)
        else:
            break
        count += 1
    text += str(row_0) + "\n" + str(row_1)
    return text


@APP.route('/')
def index():
    "/ - Gives the default index page"
    text = ("\nSky - A simple weather monitor\n\n"
            "Usage\n\n"
            "To check weather for your location simply run the following "
            "command in a terminal\n\n"
            "In Celsius\n"
            "+ Weather for one week - curl sky.webionite.com/location \n"
            "+ Weather for today - curl sky.webionite.com/location/t\n\n"
            "In Fahrenheit\n"
            "+ Weather for one week - curl sky.webionite.com/f/location \n"
            "+ Weather for today - curl sky.webionite.com/f/location/t\n\n"
            "Replace sky.webionite.com/ with sky.webionite.com/p/ on "
            "Windows \n\n"
            + config.source + "\n")
    return text


def main(location, geocoder, cache_db, kind, unit):
    "Main function that returns the weather based on parameters"
    try:
        coordinates = get_coordinates(location, geocoder, cache_db)
    except (IndexError, KeyError):
        return "Location Not found"
    weather = get_weather(coordinates)
    text = weather_to_text(weather, kind, unit, coordinates[2])
    return ("\n" + text + "\n\n" + config.source + "\nPowered by Dark Sky - "
            "https://darksky.net/poweredby/\n")


def strip_colors(text):
    "Strips ANSI colors from a string"
    return re.sub('\033\\[[0-9;]+?m', '', text)


@APP.route('/<path:path>')
def url_parser(path):
    "Parses the URL"
    location = ''
    unit = 'c'
    plain = False
    frequency = 'daily'
    for part in path.strip('/').split('/'):
        if part == 'f':
            unit = 'f'
        elif part == 'p':
            plain = True
        elif part == 't':
            frequency = 'hourly'
        else:
            location = part
    if plain:
        return strip_colors(main(location, GEOCODER, CACHE_DB, frequency,
                                 unit))
    return main(location, GEOCODER, CACHE_DB, frequency, unit)


@APP.after_request
def after(response):
    "Sets content type to text/plain"
    response.headers['Content-Type'] = "text/plain; charset=utf-8"
    return response
