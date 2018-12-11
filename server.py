#!/usr/bin/env python3

from flask import Flask
from mapbox import Geocoder
import sqlite3
import config

geocoder = Geocoder(access_token=config.mapbox_key)
app = Flask(__name__)
cache_db = sqlite3.connect("cache.sqlite")


def get_coordinates(location, geocoder, cache_db):
    row = cache_db.execute("select lat,lon from location where name = ?;",
                           (location,)).fetchone()

    if row is not None:
        return (row[0], row[1])

    loc = geocoder.forward(location)
    coordinates = loc.geojson()['features'][0]['center']
    cache_db.execute("insert into location(name, lat, lon) values(?,?,?)",
                     (location, *coordinates))
    return tuple(coordinates)


def get_weather(coordinates):
    return coordinates


def weather_to_text(text):
    return str(text)


@app.route('/')
def index():
    text = ("To get the weather for a location, run curl "
            "https://sky.webionite.com/location. \n" + config.source)
    return text


def main(location, geocoder, cache_db):
    coordinates = get_coordinates(location, geocoder, cache_db)
    weather = get_weather(coordinates)
    text = weather_to_text(weather)
    return text + "\n" + config.source


app.add_url_rule('/<location>', 'location', lambda location:
                 main(location, geocoder, cache_db))
