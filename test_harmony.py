import harmony
import dumper

def get_hub():
    hub = harmony.harmonysock(host = '192.168.1.55',hubid = '14255516')
    return hub


class LogiHub:

    def __init__(self, ip = '192.168.1.55',rport = '14255516'):
        self.ip = ip
        self.rport = rport
        self.hub = harmony.harmonysock(host = self.ip, hubid=self.rport)

    def get_hub(self):
        self.hub = harmony.harmonysock(host=self.ip, hubid=self.rport)

def main():
    Great_Room = LogiHub()
    current = Great_Room.hub.currentactivity()
    print(current)
    #try turning volume down
    Great_Room.hub.sendkey(device = '60692019',key = 'VolumeDown')
    # Great_Room.get_hub()
    # print out configuration
    config = Great_Room.hub.getconfig()
    dumper.dump(config['activity'][4]["controlGroup"][1]['function'][1])




main()
