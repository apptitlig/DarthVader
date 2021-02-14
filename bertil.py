import sys
import requests
import re
import discord
import logging
import argparse
import os
import random
from metno_locationforecast import Place, Forecast

UMEA = "http://www8.tfe.umu.se/weatherold/fattig.asp"

def main(args):
    lingus = Place("Lingus", 64.1659735, 20.9219466, 15)
    sikea_forecast = Forecast(lingus, "metno-locationforecast/1.0 https://github.com/apptitlig")

    start_discord_listener(args.api_key, args.channel, sikea_forecast)


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

        patterns = re.findall("v[v]*ä[ä]*d[d]*e[e]*r[r]*", message.content.lower())

        if len(patterns) > 0:

            data_umea = requests.get(UMEA)

            degree_umea = data_umea.content.split()[244][8:][:4] 
            sikea_forecast.update()
          
            await message.channel.send(f"Umeå: " + degree_umea.decode("utf-8") + "\nSikeå: " + str(sikea_forecast.data.intervals[0].variables["air_temperature"].value))

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