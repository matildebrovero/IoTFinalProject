from MyMQTT import * #importing MyMQTT class from MyMQTT.py
import time
import json
import random
import requests

def read_sensors_data():
    #TODO: change the values to the real values read from the sensors
    glucometer = random.randint(80, 120)
    blood_pressure = random.randint(80, 120)
    oximeter = random.randint(80, 120)
    pulse = random.randint(80, 120)
    bps = random.randint(80, 120)
    termometer = random.randint(80, 120)
    #get the current time
    time = time.time()
    #SenML standard
    json_data = {
        "bn": "SensorsData",
        "e": [
            {
                "n": "glucometer",
                "u": "mg/dL",
                "t": time,
                "v": glucometer
            },
            {
                "n": "blood_pressure",
                "u": "mmHg",
                "t": time,
                "v": blood_pressure
            },
            {
                "n": "oximeter",
                "u": "%",
                "t": time,
                "v": oximeter
            },
            {
                "n": "pulse",
                "u": "bpm",
                "t": time,
                "v": pulse
            },
            {
                "n": "termometer",
                "u": "°C",
                "t": time,
                "v": termometer
            }
        ]
    }
    return json.dumps(json_data, indent = 4)

def read_ecg_data():
    #TODO: change the values to the real values read from the sensors
    ecgdata = random.randint(80, 120)
    #get the current time
    time = time.time()
    #SenML standard
    json_data = {
        "bn": "ECGdata",
        "e": [
            {
                "n": "ECG",
                "u": "mV",
                "t": time,
                "v": ecgdata
            }
        ]
    }
    return json.dumps(json_data, indent = 4)

class SensorsPublisher:
    def __init__(self, clientID, broker, port):
        #create and start MQTT Publisher
        self.ClientPublisher = MyMQTT(clientID, broker, port, None) #None because we don't need a notify function since we are the publisher

    def start(self):
        self.ClientPublisher.start()

    def publish_ecg(self, topic):
        self.topic = topic
        self.message = read_ecg_data()
        output = json.loads(self.message)
        self.ClientPublisher.myPublish(self.topic, output)
        print(f"Sensors have published new data: {output} on topic {self.topic}")
        return json.dumps(output, indent = 4)
    
    def publish_sensorsdata(self, topic):
        self.topic = topic
        self.message = read_sensors_data()
        output = json.loads(self.message)
        self.ClientPublisher.myPublish(self.topic, output)
        print(f"Sensors have published new data: {output} on topic {self.topic}")
        return json.dumps(output, indent = 4)
    
    def StopPublish(self):
        self.ClientPublisher.stop()

if __name__ == "__main__":
    # Open configuration file to read InfluxDB token, org and url and MQTT clientID, broker, port and base topic
    config_file = json.load(open('deviceconnector.json'))
    # load the registry system
    #urlCatalog = config_file["RegistrySystem"]
    # TODO: use the PREVIOUS line instead of the FOLLOWING one
    RegistrySystem = json.load(open(config_file["RegistrySystem"]))
    urlCatalog = RegistrySystem["catalogURL"]

    # read information from the configuration file and POST the information to the catalog
    information = config_file["information"]
    # TODO: use the following line instead of the previous one
    """ config = requests.post(f"{urlCatalog}/deviceConnectorList", data=config)"""
    """config_file["information"] = config.json()"""
    # save the new configuration file
    json.dump(config_file, open("deviceconnector.json", "w"), indent = 4)

    # get the patientID from the configuration file
    patientID = config_file["information"]["deviceConnectorID"]

    # get the information about the MQTT broker from the catalog using get requests
    """MQTTinfo = json.loads(requests.get(f"{urlCatalog}/broker"))
    broker = MQTTinfo["IP"]
    port = MQTTinfo["port"]
    topic_sensor = MQTTinfo["main_topic"] + config_file["ServiceInformation"]["publish_topic"]["base_topic"] + patientID + config_file["ServiceInformation"]["publish_topic"]["sensorsData"]
    topic_ecg = MQTTinfo["main_topic"] + config_file["ServiceInformation"]["publish_topic"]["base_topic"] + patientID + config_file["ServiceInformation"]["publish_topic"]["ECG"]
    clientID = config_file['serviceName'] + config_file["ServiceInformation"]['serviceID']"""
    # TODO: use the PREVIOUS lines instead of the FOLLOWING ones
    clientID = config_file["ServiceInformation"]['serviceName'] + config_file["ServiceInformation"]['serviceID']
    broker = RegistrySystem["broker"]["IP"]
    port = RegistrySystem["broker"]["port"]
    topic_sensor = RegistrySystem["broker"]["main_topic"] + config_file["ServiceInformation"]["publish_topic"]["base_topic"] + patientID + config_file["ServiceInformation"]["publish_topic"]["sensorsData"]
    topic_ecg = RegistrySystem["broker"]["main_topic"] + config_file["ServiceInformation"]["publish_topic"]["base_topic"] + patientID + config_file["ServiceInformation"]["publish_topic"]["ECG"]

    # create an instance of the publisher
    mySensors = SensorsPublisher(clientID, broker, port)
    mySensors.start()
    
    time_sensors = True
    counter = 0
    try:
        while True: 
            #sleep for 200 ms and then publish a new message for the heartbeat and sleep for 1 s and then publish information about the sensors
            # start a publisher for each topic
            if time_sensors == True:
                mySensors.publish(topic_sensor)
                mySensors.publish(topic_ecg)
                time_sensors = False
                counter = 0
            else:
                mySensors.publish(topic_ecg)
                if counter == 5:
                    time_sensors = True
                counter += 1
            time.sleep(0.2)
    except KeyboardInterrupt:
        mySensors.StopSim()