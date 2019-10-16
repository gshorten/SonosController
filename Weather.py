# Module for getting weather updates, methods for updating, formatting, and displaying weather

import requests
import json
import datetime
import threading
import time
import SonosUtils

class UpdateWeather:

    def __init__(self, location_id = "5913490", auth_key = "1b2c8e00bfa16ce7a48f76c3570fd3a2",
                 disp_lines=3, disp_width=22, fcst_period = 0, update_freq = 10):
        '''
        Gets weather update from openweathermap.org, methods for converting temperature to c and getting forecast

        :param location_id:         numeric location id for openweathermap.org API. default is Calgary
        :type location_id:          int ; 7 digits
        :param auth_key:            API access key
        :type auth_key:             str
        :param disp_lines:          number of lines in the display
        :type disp_lines:           int
        :param disp_width:          number of characters to fit weather info into
        :type disp_width:           int
        :param fcst_period:         number of 3 hour periods to get forecast for; 0 is next 3 hrs; 1 is 6, etc
        :type fcst_period:          int
        :param update_freq:         time between forecast updates in minutes
        :type: update_freq:         int
        '''

        self.location_id = location_id
        self.auth_key = auth_key
        self.disp_lines = disp_lines
        self.disp_width = disp_width
        self.fcst_period = fcst_period
        self.update_freq = update_freq
        # note openweathermap.org updates weather data every 10 minutes, no need to check more often than that.
        #set up thread to run weather update loop in
        weather_loop = threading.Thread(target=self.weather_update)
        weather_loop.start()
        # make dictionary to hold weather info, see description in weather_update
        self.weather_info = {"current":{"time":0,"desc":"","temp":0,"wind":0,"wind_dir":""},
                             "forecast":{"time":0,"desc":"","temp":0,"wind":0,"wind_dir":""}}

    def weather_update(self):
        '''
        loops every update_freq and gets updated current weather and forecast from openweathermap.org
        puts weather info into a nested dictionary called weather_info
                [current][forecast]
                    [time][desc][temp][wind][wind_dir] (for both current and forecast]
                where:
                time:  time of forecast
                desc:   short text description of weather
                temp:   temperature in Kelvin
                wind:   wind speed in m/sec
                wind_dir:   wind direction in compass degrees

        '''

        while True:

            # adjust forecast period. forecasts are every 3 hours,eg 12:00, 15:00, 18:00
            # if the current time is 2 hour or less from the forecast time then make the forecast for the next period,
            # not the end of the current one.
            # get the hour of the current time
            curr_hour = datetime.datetime.now().hour
            hrs_to_nxt_fcst = 3 - divmod(curr_hour, 3)[1]
            # if there are less than 2 hours to the next forecast AND forecast period is 0 (ie, next 3 hrs),
            # then get the forecast for the following period instead. IE if it is 5pm don't get the 6pm forecast,
            # get the 9pm instead.
            if hrs_to_nxt_fcst <= 1 and self.fcst_period == 0:
                self.fcst_period = 1
            #   0 gets the end of the current 3 hour period, 1 gets the end of the next one.

            # make urls to get weather data. go to openweathermap.org for details
            current_url = "http://api.openweathermap.org/data/2.5/weather?id=" + \
                          self.location_id + "&appid=" + self.auth_key
            forecast_url = "http://api.openweathermap.org/data/2.5/forecast?id=" +\
                           self.location_id + "&appid=" + self.auth_key

            # get current weather data, json format
            current_json = requests.get(current_url).json()
            # get current weather time, put in weather_info
            current_time = datetime.datetime.fromtimestamp(current_json["dt"]).strftime('%Hh')
            self.weather_info["current"]["time"] = current_time
            self.weather_info["current"]["desc"] = current_json["weather"][0]["description"]
            self.weather_info["current"]["temp"] = round(current_json["main"]["temp"] - 273)
            self.weather_info["current"]["wind"] = round(current_json["wind"]["speed"] * 3.6)
            #   multiply by 3.6 to convert from m/sec to km/hr
            current_wind_deg = current_json["wind"]["deg"]
            # convert to cardinal
            current_wind_arrows = self.degrees_to_arrows(deg=current_wind_deg)
            self.weather_info["current"]["wind_dir"] = current_wind_arrows

            # get forecast json
            forecast_json = requests.get(forecast_url).json()
            # put forecast weather time, description, temperature and put in weather_info dictionary
            # get current time of forecast un unix utc format
            forecast_time_utc = forecast_json["list"][self.fcst_period]["dt"]
            # convert time to local and format and put into weather_info
            self.weather_info["forecast"]["time"] = datetime.datetime.fromtimestamp(forecast_time_utc).strftime('%Hh')
            # put forecast desc and temp into weather_info
            self.weather_info["forecast"]["desc"] = \
                forecast_json["list"][self.fcst_period]["weather"][0]["description"]
            self.weather_info["forecast"]["temp"] = \
                round(forecast_json["list"][self.fcst_period]["main"]["temp"] - 273)
            #   temperatures are in kelvin, subtract 273 to get celsius and round to one decimal place
            # get wind direction and speed
            self.weather_info["forecast"]["wind"] = round(forecast_json["list"][self.fcst_period]["wind"]["speed"] *3.6)
            fcst_wind_dir_deg = round(forecast_json["list"][self.fcst_period]["wind"]["deg"])
            fcst_wind_dir_arrows = self.degrees_to_arrows(deg=fcst_wind_dir_deg)
            self.weather_info["forecast"]["wind_dir"] = fcst_wind_dir_arrows

            # print values to test
            # for x in self.weather_info:
            #     print(x.upper(), " Weather:")
            #     for y in self.weather_info[x]:
            #         print(y,": ",self.weather_info[x][y])
            #     print("---------")

            # Sleep  until it's time to check the weather again
            time.sleep(self.update_freq*60)

    def degrees_to_cardinal(self,deg = 0):
        '''
        note: this is highly approximate...
        '''
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        ix = int((deg + 11.25) / 22.5-.02)
        dir_card = dirs[ix % 16]
        return dir_card

    def degrees_to_arrows(self, deg = 0):
        '''
        attempt to convert degrees into arrows
        :param deg:
        :type deg:
        :return:
        :rtype:
        '''
        # make list of unicode characters for the direction arrows
        dirs = ['\u2193','\u2199','\u2190','\u2196','\u2191','\u2197','\u2192','\u2198','\u2193']
        # make index for list based on 360 degrees, ie 45 degrees would be second item, NNE, arrow pointing down and to left
        ix = int(round(deg / 45))
        #get the right arrow from the list
        dir_card = dirs[ix % 8]

        return dir_card


    def make_weather_disp(self,line_width = 26,cpu_temp = False):
        '''
        make strings to describe weather & time, split over desired lines
        :param weather:
        :type weather:
        :return:
        :rtype:
        '''

        if self.disp_lines == 3:
            lines = ["","",""]
            #first line will be date and time, plus cpu temperature (if cpu_temp = True
            if cpu_temp:
                # add cpu temperature to first line
                lines[0] = SonosUtils.center_text(time.strftime("%b %d %I:%M %p")
                                            + str(round(SonosUtils.get_cpu_temp()))+"c",line_width)
            else:
                lines[0] = SonosUtils.center_text(time.strftime("%b %d %I:%M %p"), line_width -2)
            #second line is the current weather
            lines[1] = SonosUtils.center_text(self.weather_info["current"]["desc"]+" " +
                                              str(self.weather_info["current"]["temp"]) + "c " +
                                              str(self.weather_info["current"]["wind"])+
                                              self.weather_info["current"]["wind_dir"],line_width)
            # third line is the forecast.
            # get description and truncate it to 12 characters (to fit display better)
            description_short = self.weather_info['forecast']['desc'][:12]
            #description_short = description[:12]
            lines[2] = SonosUtils.center_text(self.weather_info["forecast"]["time"] + " " +
                                              description_short + " " +
                                              str(self.weather_info["forecast"]["temp"]) + "c " +
                                              str(self.weather_info["forecast"]["wind"]) +
                                              self.weather_info["forecast"]["wind_dir"],line_width)
        return lines

#test the class
# update = UpdateWeather(update_freq=10)
# time.sleep(2)
#
# while True:
#     display = UpdateWeather.make_weather_disp(update, line_width=27)
#     for x in display:
#         print(x)
#     print("-----------------------")
#     time.sleep(600)