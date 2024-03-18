import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import requests
import time
from MyMQTT import *
import cherrypy


class HospitalBot:
    def __init__(self, token, broker, port, topic):
        # Local token
        self.tokenBot = token
        self.chatIDs = []
        self.bot = telepot.Bot(self.tokenBot)

        self.topic = topic
        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()

    def on_chat_message(self, msg):      
        content_type, chat_type, self.chat_ID = telepot.glance(msg)
        message = msg['text']
        # check wich message has been received from the bot
        if message == "/start":
            # create an instance of the MyMQTT class
            self.client = MyMQTT("telegramBotUniqueID", broker, port, self)
            self.client.start()
            # welcome message      
            self.bot.sendMessage(self.chat_ID, text="Welcome to the Hospital Bot. From now on the bot is turned on and you can receive updates about the patients.")
            # subscribe to the topic
            self.client.mySubscribe(self.topic)    
        # stop the bot
        elif message == "/stop":
            self.bot.sendMessage(self.chat_ID, text="The bot has been turned off")
            self.client.stop()
        else:
            self.bot.sendMessage(self.chat_ID, text="Command not supported")

    def notify(self, topic, msg):
        # convert the message in json format
        msg = json.loads(msg)
        # print the message received from the topic
        print("Received message from topic: %s" % topic)
        print("Message: %s" % msg)
        # get the patientID from the topic which is SmartHospital308/Monitoring/PatientID/status
        patientID = topic.split("/")[2] 
        # check the message received from the topic and send an alert message to the chat
        if msg["status"] == "alert":
            self.bot.sendMessage(self.chat_ID, text="ALERT MESSAGE: Patient " + patientID + " is in danger")
        
if __name__ == "__main__":
    # load the configuration file of the TelegramBot
    conf = json.load(open("TB_configuration.json"))
    token = conf["telegramToken"]
    # load the registry system
    urlCatalog = conf["RegistrySystem"]
    # read information from the configuration file and POST the information to the catalog
    config = conf["information"]
    config = requests.post(f"{urlCatalog}/service", data=config)
    conf["information"] = config.json()
    # save the new configuration file
    json.dump(conf, open("TB_configuration.json", "w"), indent = 4)
    # get the information about the MQTT broker from the catalog using get requests
    MQTTinfo = json.loads(requests.get(f"{urlCatalog}/broker"))
    broker = MQTTinfo["IP"]
    port = MQTTinfo["port"]
    topic = MQTTinfo["main_topic"] + conf["information"]["subscribe_topic"]
    ###################################################
    ## The following code is used to test the bot without the catalog
    ###################################################
    """broker = RegistrySystem["broker"]["IP"]
    port = RegistrySystem["broker"]["port"]
    topic = RegistrySystem["broker"]["main_topic"] + conf["information"]["subscribe_topic"]"""
    ###################################################  
    print(topic)
    # create an instance of the HospitalBot
    SmartHospitalBot = HospitalBot(token, broker, port, topic)

while True:
    time.sleep(0.5)
    pass