import fauxmo
import time
import json
import paho.mqtt.client as mqtt


class devicesClass():
    def __init__(self, client, alexaName, mqttSet):
        self.client = client
        self.alexaName = alexaName
        self.mqttSet = mqttSet

        self.lastEcho = time.time()
        self.DEBOUNCE_SECONDS = 0.3

    def actionHandler(self, client_address, state, name):
        self.client.publish(self.mqttSet, int(state))

        return True

    def on(self, client_address, name):
        if self.debounce():
            return True
        return self.actionHandler(client_address, True, name)

    def off(self, client_address, name):
        if self.debounce():
            return True
        return self.actionHandler(client_address, False, name)

    def debounce(self):
        """If multiple Echos are present, the one most likely to respond first
           is the one that can best hear the speaker... which is the closest one.
           Adding a refractory period to handlers keeps us from worrying about
           one Echo overhearing a command meant for another one.
        """
        if (time.time() - self.lastEcho) < self.DEBOUNCE_SECONDS:
            return True

        self.lastEcho = time.time()
        return False


# read config json
with open("config.json", 'r') as f:
    configs = json.load(f)

""" mqtt """
def on_disconnect(client, userdata, rc):
    client.reconnect()

def on_message(client, userdata, message):
    pass


client = mqtt.Client()
client.username_pw_set(configs["mqttUser"], configs["mqttPass"])
client.on_disconnect = on_disconnect
client.on_message = on_message
client.connect(configs["mqttAdress"], port=1883, keepalive=60)



# Startup the fauxmo server
#fauxmo.DEBUG = True
poller = fauxmo.poller()
responder = fauxmo.upnp_broadcast_responder()
responder.init_socket()
poller.add(responder)


devices = []


for config in configs["configs"]:
    device = devicesClass(client, config["alexaName"], config["mqttSet"])

    fauxmo.fauxmo(config["alexaName"], responder, poller, None, config["port"], device)

    devices.append(device)



# Loop and poll for incoming Echo requests
while True:
    poller.poll(100)
    client.loop()

