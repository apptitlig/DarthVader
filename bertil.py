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
import datetime as dt
import statistics as s
import locale
import calendar

api_instance = giphy_client.DefaultApi()



def main(args):
    
    lingus = Place("Lingus", 64.1659735, 20.9219466, 15)    
    sikea_forecast = Forecast(lingus, "metno-locationforecast/1.0 https://github.com/apptitlig")

    umea = Place("Umee", 63.8390388, 20.3381108, 16)    
    umea_forecast = Forecast(umea, "metno-locationforecast/1.0 https://github.com/apptitlig")

    mittemellan = Place("mittemellan", 63.9262669, 20.4252715, 16)    
    mittemellan_forecast = Forecast(umea, "metno-locationforecast/1.0 https://github.com/apptitlig")

    start_discord_listener(args.api_key, args.api_key_giphy, args.channel, args.user, sikea_forecast, umea_forecast, mittemellan_forecast)

async def search_gifs(query, api_key_giphy):
    try:
        response = api_instance.gifs_search_get(api_key_giphy,
            query, limit=5, rating='g')
        lst = list(response.data)
        gif = random.choices(lst)
        return gif[0].url

    except ApiException as e:
        return "Exception when calling DefaultApi->gifs_search_get: %s\n" % e
    except IndexError as e:
        response = api_instance.gifs_search_get(api_key_giphy,
            "possum", limit=5, rating='g')
        lst = list(response.data)
        gif = random.choices(lst)
        return gif[0].url

async def dot_aligned(seq):
    snums = [str(seq)]
    dots = [s.find('.') for s in snums]
    return [' '*(3 - d) + s for s, d in zip(snums, dots)][0]

async def forecastDay(f,days, i):
    temp, nb, blast, start, end = await getValuesWithList(f, i)

    alignedtemp = await dot_aligned(temp)
    
    forecast_string = start +  " - " + end + ": "  + '{:7}'.format(str(alignedtemp)) + '{:6}'.format(str(blast))  + str(nb) + "\n" 
    return forecast_string

async def forecast2day(f, days, time):
    time0 = f[time].start_time
    time1 = f[time].end_time
    
    temp, nb, blast, _, _ = await getValuesWithList(f, time)

    alignedtemp = await dot_aligned(temp)
    
    forecast_string = str(time0.time())[0:5] +  " - " + str(time1.time())[0:5] + ": "  + "{:5.1f}".format(float(alignedtemp)) + "{:5.1f}".format(blast)  + "   " + str(nb) + "\n" 
    return forecast_string


async def forecast1day(f, days, start, end):
    temp = 0
    nb = 0
    blast = 0
    time0 = f[start].start_time
    time1 = f[end].end_time
    
    for j in range(start, end):
        temp1, nb1, blast1, _, _ = await getValuesWithList(f, j)

        temp = temp + temp1 
        nb = nb + nb1
        blast = blast + blast1

    temp = temp/(end - start)
    nb = nb/(end - start)
    blast = blast/(end - start)

    alignedtemp = await dot_aligned(temp)
    
    forecast_string = str(time0.time())[0:5] +  " - " + str(time1.time())[0:5] + ": "  + "{:5.1f}".format(float(alignedtemp)) + "{:5.1f}".format(blast)  + "   " + str(nb) + "\n" 
    return forecast_string

async def minMaxDay(f):
    min = f[0].variables["air_temperature"].value 
    max = f[0].variables["air_temperature"].value 

    for i in range(len(f)):
        t = f[i].variables["air_temperature"].value
        if t > max:
            max = t
        if t < min:
            min = t

    alignedmax = await dot_aligned(max)
    alignedmin = await dot_aligned(min)
    return '{:10}'.format(str(alignedmin) + "  " + str(alignedmax))

async def getValuesWithList(forecast, i):
    temp  = forecast[i].variables["air_temperature"].value
    nb    = forecast[i].variables["precipitation_amount"].value
    blast = forecast[i].variables["wind_speed"].value 
    start = forecast[i].start_time
    end = forecast[i].end_time 

    return temp, nb, blast, str(start.time())[0:5], str(end.time())[0:5]


async def getValuesWithData(forecast, i):
    temp  = forecast.data.intervals[i].variables["air_temperature"].value
    nb    = forecast.data.intervals[i].variables["precipitation_amount"].value
    blast = forecast.data.intervals[i].variables["wind_speed"].value 
    start = forecast.data.intervals[i].start_time
    end = forecast.data.intervals[i].end_time 

    return temp, nb, blast, str(start.time())[0:5], str(end.time())[0:5]

async def addWeekday(days):

    d = calendar.day_name[days.weekday()]

    return '{:9}'.format(str(d))

async def prognosMinMax(forecast, length):
    forecast.update()
    forecast_string = "```Dag             Min    Max \n";
    
    for i in range(1, length+1):
      
        days = dt.date.today() + dt.timedelta(days=i)
        f = forecast.data.intervals_for(days)
        day = f[0].start_time 
    
        forecast_string = forecast_string + str(day.day) +  " " + await addWeekday(days) + "  " +  await minMaxDay(f)
        forecast_string = forecast_string + "\n"

    return forecast_string + "```"

async def prognosN(forecast, length):
    forecast.update()
    forecast_string = "```Tid            Temp   Blåst Nederbörd\n";
    
    for i in range(1, length+1):
        days = dt.date.today() + dt.timedelta(days=i)
        f = forecast.data.intervals_for(days)
        
        forecast_string = forecast_string + await addWeekday(days) + "\n"
        if len(f) == 24:
            forecast_string = forecast_string + await forecast1day(f, days, 0, 5) + await forecast1day(f, days, 6, 11) + await forecast1day(f ,days, 12, 17) + await forecast1day(f, days, 18, 23)  
        elif len(f) == 19:
            forecast_string = forecast_string + await forecast1day(f, days, 0, 5) + await forecast1day(f, days, 6, 11) + await forecast1day(f ,days, 12, 17) + await forecast2day(f, days, 18) 
        elif len(f) == 14:
            forecast_string = forecast_string + await forecast1day(f, days, 0, 5) + await forecast1day(f, days, 6, 11) + await forecast2day(f, days, 12) + await forecast2day(f, days, 13) 
        else:
            forecast_string = forecast_string + await forecastDay(f, days, 0) + await forecastDay(f, days, 1) + await forecastDay(f, days, 2) + await forecastDay(f,days, 3)  
        forecast_string = forecast_string + "\n"

    return forecast_string + "```"
         
async def prognos(forecast):
    forecast.update()
    forecast_string = "```Tid            Temp   Blåst Nederbörd\n";

    for i in range(5):
        temp, nb, blast, start, end = await getValuesWithData(forecast, i)
        alignedtemp = await dot_aligned(temp)
        forecast_string = forecast_string + start +  " - " + end + ": "  + '{:7}'.format(str(alignedtemp)) + '{:6}'.format(str(blast))  + str(nb) + "\n" 

    temp, nb, blast, start, end = await getValuesWithData(forecast, 0)
    time = int(start[0:2])
    symbol = forecast.data.intervals[0].symbol_code

    emoji = ''
    if (symbol == 'cloudy'):
        emoji = emoji + random.choice([":cloud: "]) 
    if (symbol == 'clearsky' or symbol == 'fair' or symbol == "clearsky_day"):
        emoji = emoji + random.choice([":sun_with_face: ", ":sunny: "]) 
    if (symbol == 'fog'):
        emoji = emoji + random.choice([":fog: "]) 
    if (symbol.find('rain') > 1 or symbol.find('sleet') > 1):
        emoji = emoji + random.choice([":rain_cloud: ", ":white_sun_rain_cloud: "]) 
    if (symbol.find('thunder') > 1):
        emoji = emoji + random.choice([":cloud_lightning: "]) 
    if (symbol.find('snow') > 1):
        emoji = emoji + random.choice([":cloud_snow: ", ":snowflake: ",":snowman: ", ":snowman2: "]) 
    if (symbol.find('night') > 1):
        emoji = emoji + random.choice([":star:", ":star2:"])

    if (blast >= 4):
        emoji = emoji + random.choice([":dash:", ":wind_blowing_face:"])
    if (blast > 14):
        emoji = emoji + ":cloud_tornado:"

    forecast_string = forecast_string + "```\n" + emoji

    return forecast_string

def start_discord_listener(api_key, api_key_giphy, subscribed_channels, user, sikea_forecast, umea_forecast, mittemellan_forecast):
    client = discord.Client()
    global points 
    points = 10

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
        global points 
        if (str(message.author) == str(user[0]) and (points > 5)):
            isprognosorvader = message.content.split()[0].lower()
            
            if ((isprognosorvader == "prognos") and (len( message.content.split()) > 1 ) ):
                tosearchfor = message.content.split()[1].lower()
                if(tosearchfor != "umeå" and tosearchfor != "sikeå" and tosearchfor != "u" and tosearchfor != "s"):
                    gif = await search_gifs(tosearchfor, api_key_giphy)
                    
                    await message.channel.send(str(gif))
                    points = points - 5

        
        if len(patternsVader) > 0 or len(patternsVadret) > 0 or len(patternsVadur) > 0 :

            points = points + 2

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
            points = points + 2
            ans =  await prognos(sikea_forecast)
            await message.channel.send(ans)

        patternsUmea = re.findall("prognos u", message.content.lower())

        if len(patternsUmea) > 0:
            points = points + 2
            ans =  await prognos(umea_forecast)
            await message.channel.send(ans)

        patternsN = re.findall("prognos [1-9][1-9]*", message.content.lower())

        if len(patternsN) > 0:
            points = points + 2
            splitmessage = message.content.lower().split()
            days = int(splitmessage[1])
            if days < 5:
                ans =  await prognosN(mittemellan_forecast, days)
            else:
                ans =  await prognosMinMax(mittemellan_forecast, days)
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
    parser.add_argument("--user",
                        action="append",
                        help="A user to joke with.",
                        required=True)                    

    args = parser.parse_args()
    if args.api_key is None:
        logging.error("API supplied neither by --api-key or env variable BERTIL_API_KEY.")
        sys.exit(1)

    return args


if __name__ == "__main__":
    main(parse_args())