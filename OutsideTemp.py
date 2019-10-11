import requests
import json

def get_outside_temp(city_key = "5913490", api_key="1b2c8e00bfa16ce7a48f76c3570fd3a2"):

    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = base_url +"appid=" + api_key + "id=" + city_key
    response = requests.get(complete_url)
    x = response.json()
    print(x)
    # y = x["main"]
    # current_temperature = y["temp"]
    # print("Current Temperature is:", str(current_temperature))
    # return(str(current_temperature))

# temp = get_outside_temp()
# print("Temperature is:", temp)
get_outside_temp()