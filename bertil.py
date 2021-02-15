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

giphy_token = 'api_key'
api_instance = giphy_client.DefaultApi()

UMEA = "http://www8.tfe.umu.se/weatherold/fattig.asp"

def main(args):
    lingus = Place("Lingus", 64.1659735, 20.9219466, 15)
    sikea_forecast = Forecast(lingus, "metno-locationforecast/1.0 https://github.com/apptitlig")

    start_discord_listener(args.api_key, args.channel, sikea_forecast)

async def search_gifs(query):
    try:
        response = api_instance.gifs_search_get(giphy_token,
            query, limit=10, rating='g')
        lst = list(response.data)
        gif = random.choices(lst)

        return gif[0].url

    except ApiException as e:
        return "Exception when calling DefaultApi->gifs_search_get: %s\n" % e


def start_discord_listener(api_key, subscribed_channels, sikea_forecast):
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
        supercold = ["antarctica", "polarbear", "blizzard", "snow dog"]
        somewhatcold = ["cold", "freezing", "brrr", "skiing", "snowmobile", "ice ice baby", "ice king", "gunther", "titanic", "winter", "olaf", "snowflake"]
        spring = ["thaw", "spring", "flower bud", "park"]

        patterns = re.findall("v[v]*ä[ä]*d[d]*e[e]*r[r]*", message.content.lower())

        if len(patterns) > 0:

            data_umea = requests.get(UMEA)
           
            degree_umea = data_umea.content.split()[244][8:][:5]

            sikea_forecast.update()
            gif = ""
            if (sikea_forecast.data.intervals[0].variables["air_temperature"].value < -11):
                gif = await search_gifs(random.choice(supercold))
            elif (sikea_forecast.data.intervals[0].variables["air_temperature"].value < 0):
                gif = await search_gifs(random.choice(somewhatcold))
            else:
                gif = await search_gifs(random.choice(spring))

            await message.channel.send(f"Umeå: " + degree_umea.decode("utf-8") + "\nSikeå: " + str(sikea_forecast.data.intervals[0].variables["air_temperature"].value) +"\n" +  str(gif))

    client.run(api_key)


def parse_args():
    parser = argparse.ArgumentParser(description="A Discord Ume weather bot ")
    parser.add_argument("--api-key",
                        help="Relevant Discord API key.",
                        default=os.environ.get("BERIT_API_KEY"))
    parser.add_argument("--channel",
                        action="append",
                        help="A channel which Berit listens in. May be supplied multiple times.",
                        required=True)

    args = parser.parse_args()
    if args.api_key is None:
        logging.error("API supplied neither by --api-key or env variable BERIT_API_KEY.")
        sys.exit(1)

    return args


if __name__ == "__main__":
    main(parse_args())