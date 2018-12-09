#!/usr/bin/env python3

from flask import Flask
from mapbox import Geocoder
import sqlite3
import config

geocoder = Geocoder(access_token=config.mapbox_key)
app = Flask(__name__)
cache_db = sqlite3.connect("cache.sqlite")


@app.route('/')
def index():
    text = ("To get the weather for a location, run curl "
            "https://sky.webionite.com/location. \n"
            "Source: https://gitlab.com/ceda_ei/sky\n")
    return text


def main(location, geocoder, cache_db):
    return


app.add_url_rule('/<location>', 'location', lambda location:
                 main(location, geocoder, cache_db))
