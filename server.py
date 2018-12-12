#!/usr/bin/env python3

from flask import Flask
from mapbox import Geocoder
import darksky
from columnizer import Columnizer
from ascii import arts
import sqlite3
import config
from datetime import datetime
from pytz import timezone

geocoder = Geocoder(access_token=config.mapbox_key)
app = Flask(__name__)
cache_db = sqlite3.connect("cache.sqlite", check_same_thread=False)


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
    return darksky.forecast(config.dark_sky_key, coordinates[0],
                            coordinates[1])


def weather_to_text(forecast, kind, unit):
    if kind == "daily":
        text = forecast["daily"]["summary"] + "\n\n"
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
        # today += ["", forecast["currently"]["summary"]]
        row_0.add_column(today)
        count = 1

        for i in forecast["daily"]["data"]:
            x = []
            date = datetime.fromtimestamp(i["time"],
                                          timezone(forecast["timezone"]))
            x += date.strftime("%d %B\n%A").split("\n")
            x += [*arts[i["icon"]]]
            x += [""]
            if unit == "c":
                x += ["Max: {0:.1f}°C".format(5*(i["temperatureMax"]-32)/9)]
                x += ["Min: {0:.1f}°C".format(5*(i["temperatureMin"]-32)/9)]
            else:
                x += ["Max: {0:.1f}°C".format(i["temperatureMax"])]
                x += ["Min: {0:.1f}°C".format(i["temperatureMin"])]
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


@app.route('/')
def index():
    text = ("To get the weather for a location, run curl "
            "https://sky.webionite.com/location. \n" + config.source)
    return text


def main(location, geocoder, cache_db, kind, unit):
    coordinates = get_coordinates(location, geocoder, cache_db)
    weather = get_weather(coordinates)
    text = weather_to_text(weather, kind, unit)
    return ("\n" + text + "\n\n" + config.source + "\nPowered by Dark Sky - "
            "https://darksky.net/poweredby/\n")


app.add_url_rule('/<location>', 'location', lambda location:
                 main(location, geocoder, cache_db, "daily", "c"))

app.add_url_rule('/<location>/t', 'today_location', lambda location:
                 main(location, geocoder, cache_db, "hourly", "c"))

app.add_url_rule('/f/<location>', 'location_f', lambda location:
                 main(location, geocoder, cache_db, "daily", "f"))

app.add_url_rule('/f/<location>/t', 'today_location_f', lambda location:
                 main(location, geocoder, cache_db, "hourly", "f"))
