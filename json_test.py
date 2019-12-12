# Testing reading json config file and creating dictionary of sonos wallbox selections 0 - 199 from json file
from jsoncomment import JsonComment
import soco

json = JsonComment()
# allows use of python style comments in json file
# open json file
json_file = open("wallbox_pages.json","r")
# parse and load into python object (nested dictionary & list)
pages = json.load(json_file)

'''
#test
print(json_file)
print(pages)
print("************")
print(pages["0000"]["sections"][0]["type"])
print("************")

# loop through page sets
for page in pages:
    print(), print()
    print("----------------------------------")
    print("Next Pages Set")
    print("Page set RFID: ",page)
    print("Page set name: ",pages[page]["page_set_name"])
    # for info in pages[page]:
        #print(pages[page][info])
    total_selections = 0

    # loop through sections
    for section in range(len(pages[page]["sections"])):
        print()
        print("SECTION")
        # calculate number of wallbox selections in the section, adjust total for 0 starting (because python list indexing)
        num_selections = int(pages[page]["sections"][section]["end"]) - int(pages[page]["sections"][section]["start"]) +1
        print("Number of selections: ",num_selections)
        total_selections = total_selections + num_selections

        # loop through parameters in each section
        for parameter in pages[page]["sections"][section]:
            print(parameter,": ",pages[page]["sections"][section][parameter])

        print()
        print("Total number of selections: ", total_selections )
'''

# Test building dictionaries and list of items to play

# dictionary to hold info on each wallbox selection
page_set_item = {'title':'','song_title':'','artist':'','source':'','type':'',"ddl_item":''}
page_set_items = []
#get test soco unit
# sonos_unit = soco.discovery.by_name("Kitchen")
sonos_unit = soco.SoCo("192.168.1.35")
print("Sonos Unit: ",sonos_unit)

# get current page set from json file
json = JsonComment()
# allows use of python style comments in json file
# open json file
json_file = open("wallbox_pages.json","r")
# parse and load into python object (nested dictionary & list)
page_sets = json.load(json_file)
#get current page set as read from rfid tag, this is just a test, not real tag
rfid_tag ="0000"
page_set = page_sets[rfid_tag]
# initialize wallbox_selection number
page_set_item_number = 0
# print(page_set)
#loop through sections in page_set
for section in page_set['sections']:
    #calculate number of selections in section
    num_selections = int(section['end']) - int(section['start']) + 1
    type = section['type']
    page_set_item_number = int(section['start'])

    if type == "sonos_favorites" or type == 'sonos_playlists':
        start = int(section['start_list'])
        for selection in range(num_selections):
            track = sonos_unit.music_library.get_music_library_information(type)[start + selection]
            page_set_item_number += 1
            #print("wallbox selection: ",page_set_item_number, track.reference.title)
            if type == 'sonos_favorites':
                page_set_item = {'title':track.reference.title,"song_title":'','artist':'','source':track.reference.title,'type':type,
                                'ddl_item':track.reference}
            elif type == 'sonos_playlists':
                page_set_item = {'title': track.title, "song_title": '', 'artist': '',
                                 'source': track.title, 'type': type,
                                 'ddl_item': track,'playmode':section['play_mode']}
            # add to page_set_items list
            page_set_items.insert(page_set_item_number,page_set_item)

    elif type == "sonos_playlist_selections":
        for selection in range(num_selections):
            page_set_item_number += 1
            playlist = sonos_unit.music_library.get_music_library_information(
                'sonos_playlists',search_term = "J")
            print(playlist)
            track = playlist[selection]
            page_set_item = {'title':track.title}
            page_set_items.insert(page_set_item_number,page_set_item)

#test
for index, item in enumerate(page_set_items):
       print('Selection:',index," Type:",item['type'],item['title'],'             ', item['ddl_item'])