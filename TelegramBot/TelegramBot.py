import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import requests
import time
from MyMQTT import *

"""
    TelegramBot - SmartHospital IoT platform. Version 1.0.1 
    This microservice is responsible for subscribing to the MQTT broker and sending alerts to the nurses when a patient is in danger.
     
        Input:  
            - Patient status received trough the MQTT broker from the PatientStatus microservice
        Output:
            - alert message sent to the nurse chat when a patient is in danger (Telegram Bot)
 
    -------------------------------------------------------------------------- 
    --------------         standard configuration          ------------------- 
    -------------------------------------------------------------------------- 
 
    Standard Configuration file provided: ECGAn_configuration.json 
    The parameters of the configuration file are: 
 
        - "RegistrySystem": URL of the Registry System 

        - "telegramToken": Token of the Telegram Bot
 
        - "information": 
            - "serviceID": ID of the service
            - "serviceName": Name of the service = "DB_adaptor" 
            - "availableServices": List of the communication protocol available for this service (MQTT, REST)
            - "subscribe_topic": Topic where the service will subscribe to read the data from the sensors
                    Example: "SmartHospitalN/Monitoring/patientN/status"
                    to get the status of each patient present the wildcard "+" is used
            - "uri":               
                - "get_nurseInfo": URI to get the information of a single nurse
                - "post_nurseInfo": URI to post the information of a single nurse
                - "get_patientInfo": URI to get the information of a single patient
                - "single_patient": URI to get the information of a single patient
                - "add_service": URI to add the service to the catalog
                - "broker_info": URI to get the information of the MQTT broker
"""

class HospitalBot:
    def __init__(self, token, broker, port, clientID, topic, configuration):
        # Local token
        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)
        self.topic = topic
        self.configuration = configuration
        self.broker = broker
        self.port = port
        self.clientID = clientID
        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()
        self.nurseInfo = requests.get(f"{self.configuration['RegistrySystem']}/{self.configuration['information']['uri']['get_nurseInfo']}").json()
        print("\n\n\n")
        print(self.nurseInfo)

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
            self.client = MyMQTT(self.clientID, self.broker, self.port, self)
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
                    print(f"{self.configuration['RegistrySystem']}/{self.configuration['information']['uri']['post_nurseInfo']}")
                    # register the chatID of the nurse in the catalog using a POST request, in this way the nurse can receive updates about the patients, also, assign patients to the nurse
                    nurse = requests.post(f"{self.configuration['RegistrySystem']}/{self.configuration['information']['uri']['post_nurseInfo']}", json=nurse)
                    print("\n\n\nNURSE")
                    print(nurse.json())
                    nurse = nurse.json()
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
        self.nurseInfo = requests.get(f"{self.configuration['RegistrySystem']}/{self.configuration['information']['uri']['get_nurseInfo']}").json()
        print("\n\n\n")
        print(self.nurseInfo)
        # convert the message in json format
        print("\n\n\n")
        print(msg)
        msg = json.loads(msg)
        ########################
        # print the message received from the topic
        ########################
        print("Received message from topic: %s" % topic)
        print("Message: %s" % msg)
        # get the patientID from the topic which is SmartHospital308/Monitoring/PatientID/status
        patientID = topic.split("/")[2] 
        print("\n\n\n")
        print("Patient ID: %s" % patientID)

        onlyID = patientID.split("t")[2]
        
        print("\n\n\n")
        print("Patient ID: %s" % onlyID)

        # request patient name and surname via GET request to the catalog
        """print(f"{self.configuration['RegistrySystem']}/{self.configuration['information']['uri']['get_patientInfo']}?{self.configuration['information']['uri']['single_patient']}={onlyID}")
        patientInfo = requests.get(f"{self.configuration['RegistrySystem']}/{self.configuration['information']['uri']['get_patientInfo']}?{self.configuration['information']['uri']['single_patient']}={onlyID}").json()
        try:
            if patientInfo["firstName"] != "" and patientInfo["lastName"] != "":
                patientName = patientInfo["firstName"]
                patientSurname = patientInfo["lastName"]
            else:
                patientName = "Unknown"
                patientSurname = "Unknown"
        except:
            patientName = "Unknown"
            patientSurname = "Unknown"""
        # check the message received from the topic and send an alert message to the correct chat
        if msg["e"][0]["v"] == "bad":
            print("ALERT MESSAGE MUST BE SENT")
            print(self.nurseInfo)
            for nurse in self.nurseInfo:
                print(nurse["patients"])
                print(nurse["chatID"])
                print(type(onlyID))
                if nurse["patients"] != [] and nurse["chatID"] != "":
                    print("INSIDE")
                    print(onlyID)
                    print(nurse["patients"])
                    print(onlyID in nurse["patients"])
                    if onlyID in nurse["patients"]:
                        print(nurse["chatID"])
                        # send the message to the chat of the nurse
                        self.bot.sendMessage(nurse["chatID"], text=f"ALERT MESSAGE: patient  with ID {onlyID} is in danger")

        # NOT USED IN THIS VERSION. JUST THE MESSAGE ALERT WILL BE SENT
        ########### CODE ONLY USED TO DEUG 
        #if the status equal to regular and the previous status is also regular the patient may require attention, write a message to the chat
        elif msg["e"][0]["v"] == "fair":
            for nurse in self.nurseInfo:
                print(nurse["patients"])
                print(nurse["chatID"])
                print(type(onlyID))
                if nurse["patients"] != [] and nurse["chatID"] != "":
                    print("INSIDE")
                    print(onlyID)
                    print(nurse["patients"])
                    print(onlyID in nurse["patients"])
                    if onlyID in nurse["patients"]:
                        self.bot.sendMessage(nurse["chatID"], text=f" with ID {onlyID} is in a REGULAR status. MAY REQUIRE ATTENTION")
        # if the status is regular and the previous status is bad the patient is now in a regular status, send a message to notify that
        elif msg["e"][0]["v"] == "good" :
            # check to which nurse the patient is assigned
            for nurse in self.nurseInfo:
                print(nurse["patients"])
                print(nurse["chatID"])
                print(type(onlyID))
                if nurse["patients"] != [] and nurse["chatID"] != "":
                    print("INSIDE")
                    print(onlyID)
                    print(nurse["patients"])
                    print(onlyID in nurse["patients"])
                    if onlyID in nurse["patients"]:
                        # send the message to the chat of the nurse
                        self.bot.sendMessage(nurse["chatID"], text=f" with ID {onlyID} has normal parameters.")
        else:
            pass
                
        
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
    config = requests.post(f"{urlCatalog}/{conf['information']['uri']['add_service']}", json=config)
    if config.status_code == 200:
        conf["information"] = config.json()
        # save the new configuration file
        json.dump(conf, open("TB_configuration.json", "w"), indent = 4)
    else:
        print("Error in adding the service to the catalog")
    # GET the information about the MQTT broker from the Registry System using get requests
    MQTTinfo = json.loads(requests.get(f"{urlCatalog}/{conf['information']['uri']['broker_info']}").text)
    broker = MQTTinfo["IP"]
    port = MQTTinfo["port"]
    topic = MQTTinfo["main_topic"] + conf["information"]["subscribe_topic"]
    clientID = conf['information']['serviceName'] + str(conf["information"]["serviceID"])

    ###################################################
    ## The following code is used to test the bot without the catalog
    ###################################################
    """broker = RegistrySystem["broker"]["IP"]
    port = RegistrySystem["broker"]["port"]
    topic = RegistrySystem["broker"]["main_topic"] + conf["information"]["subscribe_topic"]"""
    ###################################################  
    
    print(topic)
    # create an instance of the HospitalBot
    SmartHospitalBot = HospitalBot(token, broker, port, clientID, topic, conf)
    
    # get the start time
    start_time = time.time()

while True:
    #update the configuration file every 5 minutes by doing a PUT request to the catalog
    # get the current time
    current_time = time.time()
    # check if 5 minutes have passed
    if current_time - start_time > 5*60:
        config_file = json.load(open('TB_configuration.json'))
        config = requests.put(f"{urlCatalog}/{config_file['information']['uri']['add_service']}", json=config_file["information"])
        if config.status_code == 200:
            config_file["information"] = config
            json.dump(config_file, open("TB_configuration.json", "w"), indent = 4)
            # update the start time
            start_time = current_time
        else:
            print(f"Error: {config.status_code} - {config.text}")
    time.sleep(0.5)