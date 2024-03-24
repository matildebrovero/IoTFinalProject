import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import requests
import time
from MyMQTT import *
import cherrypy


class HospitalBot:
    def __init__(self, token, broker, port, topic, configuration):
        # Local token
        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)
        self.previousStatus = ""
        self.topic = topic
        self.configuration = configuration
        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()
        self.nurseInfo = requests.get(f"{self.configuration['RegistrySystem']}/{self.configuration['uri']['get_nurseInfo']}").json()

        # USED ONLY TO TEST THE BOT WITHOUT THE CATALOG
        #self.nurseInfo = json.load(open("nurseInfo.json"))
        
        # get the names of the nurses from the nurseInfo file
        self.Names = [nurse["nurseName"] for nurse in self.nurseInfo]
        print(self.Names)
    def on_chat_message(self, msg):      
        content_type, chat_type,self.chat_ID = telepot.glance(msg)

        print(content_type, chat_type, self.chat_ID)

        message = msg['text']
        # check wich message has been received from the bot
        if message == "/start":
            # create an instance of the MyMQTT class
            self.client = MyMQTT("telegramBotUniqueID", broker, port, self)
            self.client.start()
            # welcome message     
            self.bot.sendMessage(self.chat_ID, text="Welcome to the Hospital Bot. From now on the bot is turned on and you can receive updates about the patients.")
            self.bot.sendMessage(self.chat_ID, text="Insert your name and surname to start receiving updates about the patients.")
            # print the possible names of the nurses
            self.bot.sendMessage(self.chat_ID, text="The possible names are: " + str(self.Names))
            # subscribe to the topic
            self.client.mySubscribe(self.topic)   
        elif message in self.Names: 
            # if the message is the name of a nurse, send a message to the chat
            self.bot.sendMessage(self.chat_ID, text=f"Hello {message}. You are now registered to receive updates about the patients.")
            for nurse in self.nurseInfo:
                if nurse["nurseName"] == message:
                    nurseID = nurse["nurseID"]
                    # update chatID of the nurse in the nurseInfo file
                    nurse["chatID"] = self.chat_ID
                    print(nurse)
                    # register the chatID of the nurse in the catalog using a POST request, in this way the nurse can receive updates about the patients, also, assign patients to the nurse
                    nurse = requests.post(f"{self.configuration['RegistrySystem']}/{self.configuration['uri']['post_nurseInfo']}?name={nurse["nurseName"]}"
                    data=json.dumps(nurse))
                    patients = nurse["patients"]
            # send a message to the chat with the nurseID
            self.bot.sendMessage(self.chat_ID, text=f"Your ID is {nurseID} and you are in charge of the following patients: {patients}")
        elif message not in [self.Names, "/start", "/stop"]:
            self.bot.sendMessage(self.chat_ID, text="Please insert a valid name")
        # stop the bot
        elif message == "/stop":
            self.bot.sendMessage(self.chat_ID, text="The bot has been turned off")
            self.client.stop()
        else:
            self.bot.sendMessage(self.chat_ID, text="Command not supported")

    def notify(self, topic, msg):
        # convert the message in json format
        msg = json.loads(msg)
        ########################
        # print the message received from the topic
        ########################
        print("Received message from topic: %s" % topic)
        print("Message: %s" % msg)
        # get the patientID from the topic which is SmartHospital308/Monitoring/PatientID/status
        patientID = topic.split("/")[2] 
        onlyID = patientID.split("t")[2]
        # request patient name and surname via GET request to the catalog
        patientInfo = requests.get(f"{self.configuration['RegistrySystem']}/{self.configuration['uri']['get_patientInfo']}?{self.configuration['uri']['single_patient']}={onlyID}").json()
        patientName = patientInfo["firstName"]
        patientSurname = patientInfo["lastName"]

        # check the message received from the topic and send an alert message to the correct chat
        if msg["status"] == "bad":
            # check to which nurse the patient is assigned
            for nurse in self.nurseInfo:
                if onlyID in nurse["patients"]:
                    # send the message to the chat of the nurse
                    self.bot.sendMessage(nurse["chatID"], text=f"ALERT MESSAGE: {patientName} {patientSurname} with ID {onlyID} is in danger")
        """#if the status equal to regular and the previous status is also regular the patient may require attention, write a message to the chat
        elif msg["status"] == "regular" and self.previousStatus == "regular":
            # check to which nurse the patient is assigned
            for nurse in self.nurseInfo:
                if onlyID in nurse["patients"]:
                    # send the message to the chat of the nurse
                    self.bot.sendMessage(nurse["chatID"], text=f"{patientName} {patientSurname} with ID {onlyID} may be in a critical status. MAY REQUIRE ATTENTION")
        # if the status is regular and the previous status is bad the patient is now in a regular status, send a message to notify that
        elif msg["status"] == "regular" and self.previousStatus == "bad":
            # check to which nurse the patient is assigned
            for nurse in self.nurseInfo:
                if onlyID in nurse["patients"]:
                    # send the message to the chat of the nurse
                    self.bot.sendMessage(nurse["chatID"], text=f"{patientName} {patientSurname} with ID {onlyID} has now normal parameters. NO LONGER IN DANGER")
        else:
            pass"""
                # not used for now. TOOD: CHECK
        self.previousStatus = msg["status"]
        
if __name__ == "__main__":
    # load the configuration file of the TelegramBot
    conf = json.load(open("TB_configuration.json"))
    token = conf["telegramToken"]
    # read the url of the Registry System from the configuration file
    urlCatalog = conf["RegistrySystem"]
    
    # FOLLOWING LINE WAS USED TO TEST THE BOT WITHOUT THE CATALOG
    #RegistrySystem = json.load(open("..\RegistrySystem\catalog.json"))

    # read information from the configuration file
    config = conf["information"]
    # POST the configuration file to the catalog and get back the information (the Registry System will add the ID to the service information)
    config = requests.post(f"{urlCatalog}/{conf['uri']['add_service']}", data=config)
    conf["information"] = config.json()
    # save the new configuration file
    json.dump(conf, open("TB_configuration.json", "w"), indent = 4)
    # GET the information about the MQTT broker from the Registry System using get requests
    MQTTinfo = json.loads(requests.get(f"{urlCatalog}/{conf['uri']['broker_info']}"))
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
    SmartHospitalBot = HospitalBot(token, broker, port, topic, conf)

while True:
    time.sleep(0.5)
    pass