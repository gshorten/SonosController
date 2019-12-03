import json

json_file = open("wallbox_pages.json","r")
pages = json.load(json_file)

print(pages[0]['playlist'])
