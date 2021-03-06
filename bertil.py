import sys
import requests
import re
import discord
import logging
import argparse
import os
import random
from metno_locationforecast import Place, Forecast
import random
import giphy_client
from giphy_client.rest import ApiException
import xml.etree.ElementTree as ET

api_instance = giphy_client.DefaultApi()

def main(args):
    lingus = Place("Lingus", 64.1659735, 20.9219466, 15)    
    sikea_forecast = Forecast(lingus, "metno-locationforecast/1.0 https://github.com/apptitlig")

    umea = Place("Umee", 63.8390388, 20.3381108, 16)    
    umea_forecast = Forecast(umea, "metno-locationforecast/1.0 https://github.com/apptitlig")

    start_discord_listener(args.api_key, args.api_key_giphy, args.channel, sikea_forecast, umea_forecast)

async def search_gifs(query, api_key_giphy):
    try:
        response = api_instance.gifs_search_get(api_key_giphy,
            query, limit=10, rating='g')
        lst = list(response.data)
        gif = random.choices(lst)

        return gif[0].url

    except ApiException as e:
        return "Exception when calling DefaultApi->gifs_search_get: %s\n" % e

async def dot_aligned(seq):
    snums = [str(seq)]
    dots = [s.find('.') for s in snums]
    return [' '*(3 - d) + s for s, d in zip(snums, dots)]

async def prognos(forecast):
    forecast.update()

    forecast_string = "```Tid            Temp   Blåst Nederbörd\n";

    for i in range(5):
        time0 = str(forecast.data.intervals[i])[28:][:5] 
        time1 = str(forecast.data.intervals[i])[52:][:5] 

        temp  = forecast.data.intervals[i].variables["air_temperature"].value
        nb    = forecast.data.intervals[i].variables["precipitation_amount"].value
        blast    = forecast.data.intervals[i].variables["wind_speed"].value

        alignedtemp = await dot_aligned(temp)

        forecast_string = forecast_string + str(time0) + " - " + str(time1) + ": "  + '{:7}'.format(str(alignedtemp[0])) + '{:6}'.format(str(blast))  + str(nb) + "\n" 

    temp  = forecast.data.intervals[0].variables["air_temperature"].value
    nb    = forecast.data.intervals[0].variables["precipitation_amount"].value
    blast = forecast.data.intervals[0].variables["wind_speed"].value
    time  = str(forecast.data.intervals[i])[28:][:2]


    emoji = ''
    if (temp < 0 and nb > 0):
        emoji = emoji + random.choice([":cloud_snow:", ":snowflake:", ":snowman:", ":snowman2:"])
    if (temp > 0 and nb > 0):
        emoji = emoji + random.choice([":cloud_rain:", ":white_sun_rain_cloud:", ":umbrella:", ":umbrella2:"])
    if (blast >= 4):
        emoji = emoji + random.choice([":dash:", ":wind_blowing_face:"])
    if (blast > 14):
        emoji = emoji + ":cloud_tornado:"
    if (temp > 10):
        emoji = emoji + random.choice([":sunny:", ":white_sun_small_cloud:"])
    if(int(time) > 22 or int(time) < 6):
        emoji = emoji + random.choice([":star:", ":star2:"])

    if emoji == "":
        emoji = ":rainbow:"


    forecast_string = forecast_string + "```\n" + emoji

    return forecast_string

def start_discord_listener(api_key, api_key_giphy, subscribed_channels, sikea_forecast, umea_forecast):
    client = discord.Client()

    @client.event
    async def on_ready():
        logging.info(f"Logged in as {client.user}")

    @client.event
    async def on_message(message):
        if message.author == client.user:
            logging.debug(f"Ignoring message sent by myself.")
            return

        if str(message.channel) not in subscribed_channels:
            logging.debug(f"Ignoring message sent in channel other than {subscribed_channels}.")
            return
            
        supercold = ["antarctica", "polarbear", "blizzard", "snow dog", "icy", "polar"]
        somewhatcold = ["cold", "freezing", "brrr", "skiing", "snowmobile", "ice ice baby", "ice king", "gunther", "titanic", "winter", "olaf", "snowflake", "frost", "chill", "below zero"]
        spring = ["thaw", "spring", "flower bud", "daffodil", "butterfly", "tulip", "puddles", "kid (baby goat)", "daisy", "bird nest" ]

        patternsVader = re.findall("v[v]*ä[ä]*d[d]*e[e]*r[r]*", message.content.lower())
        patternsVadret = re.findall("v[v]*ä[ä]*d[d]*r[r]*e[e]*t[t]*", message.content.lower())
        patternsVadur = re.findall("v[v]*ä[ä]*d[d]*u[u]*r[r]*", message.content.lower())

        if len(patternsVader) > 0 or len(patternsVadret) > 0 or len(patternsVadur) > 0 :

            data_umea = requests.get("http://www8.tfe.umu.se/vadertjanst/service1.asmx/Temp")
            root = ET.fromstring(data_umea.content)
            
            degree_umea = root.text
            sikea_forecast.update()
          
            search_string = ""
            if (sikea_forecast.data.intervals[0].variables["air_temperature"].value < -11):
                search_string = random.choice(supercold)
            elif (sikea_forecast.data.intervals[0].variables["air_temperature"].value < 0):
                 search_string = random.choice(somewhatcold)
            else:
                 search_string = random.choice(spring)

            gif = await search_gifs(search_string, api_key_giphy)

            await message.channel.send(f"Umeå: " + str(degree_umea) + "\nSikeå: " + str(sikea_forecast.data.intervals[0].variables["air_temperature"].value) +"\n" +  str(gif))


        patternsSikea = re.findall("prognos s", message.content.lower())

        if len(patternsSikea) > 0:
           ans =  await prognos(sikea_forecast)
           await message.channel.send(ans)

        patternsUmea = re.findall("prognos u", message.content.lower())

        if len(patternsUmea) > 0:
           ans =  await prognos(umea_forecast)
           await message.channel.send(ans)




    client.run(api_key)


def parse_args():
    parser = argparse.ArgumentParser(description="A Discord Ume weather bot ")
    parser.add_argument("--api-key",
                        help="Relevant Discord API key.",
                        default=os.environ.get("BERTIL_API_KEY"))
    parser.add_argument("--api-key-giphy",
                        help="Relevant Giphy API key.",
                        default=os.environ.get("BERTIL_API_KEY_GIPHY"))
    parser.add_argument("--channel",
                        action="append",
                        help="A channel which Berit listens in. May be supplied multiple times.",
                        required=True)

    args = parser.parse_args()
    if args.api_key is None:
        logging.error("API supplied neither by --api-key or env variable BERTIL_API_KEY.")
        sys.exit(1)

    return args


if __name__ == "__main__":
    main(parse_args())