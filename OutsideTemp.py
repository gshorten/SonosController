import requests
import json
import datetime

def get_outside_temp(city_key = "5913490", api_key="1b2c8e00bfa16ce7a48f76c3570fd3a2", forecast_period = 1):

    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = base_url + "id=" + city_key  +"&appid=" + api_key
    forecast_url = "http://api.openweathermap.org/data/2.5/forecast?id=" + city_key + "&APPID=" + api_key
    #forecast_url = "http://api.openweathermap.org/data/2.5/forecast?id=" + city_key + "&APPID=" + 3737ab7cb34ad6cdee5f7217dd568b13id
    response = requests.get(complete_url)
    forecast_response = requests.get(forecast_url)
    fx = forecast_response.json()

    # x = response.json()

    #print (f_time)
    f_list = fx["list"][forecast_period]
    f_time = f_list['dt']
    #f_utc_time = f_time.utcfromtimestamp()
    f_local_time = datetime.datetime.fromtimestamp(f_time)
    #f_local_time = f_utc_time.astimezone()
    f_local_time_formatted = f_local_time.strftime('%H:%M:%S')
    print("Forecast time:",f_local_time_formatted)
    f_temp_k = f_list['main']['temp']
    f_temp_c = round(f_temp_k - 273)
    f_desc = f_list['weather'][0]['description']
    print(f_desc)
    #print("Current Temperature is:", f_temp_c)
    return(str(f_temp_c))

temp = get_outside_temp(forecast_period=0)
print("Forecast temperature is:", temp)


def convert_local(unix_time):
    ts= int(unix_time)
    local_time = datetime.datetime.utcfromtimestamp(ts)
    # if you encounter a "year is out of range" error the timestamp
    # may be in milliseconds, try `ts /= 1000` in that case
    local_time_formatted =local_time.strftime('%H:%M:%S')
    return local_time_formatted