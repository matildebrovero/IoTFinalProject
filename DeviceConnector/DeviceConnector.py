from MyMQTT import * #importing MyMQTT class from MyMQTT.py
import time
import json
import requests
from datacreator import * #importing the functions to fake the data from the sensors

# Function to read the data from the sensors
def read_sensors_data():
    glucometer = read_glucometer()
    blood_pressure = read_blood_pressure()
    oximeter = read_oximeter()
    termometer = read_body_temperature()
    # Get the current time
    time = time.time()
    # SenML standard
    json_data = json.load(open('deviceconnector_config.json'))["sensorData"]
    for data in json_data["e"]:
        if data["n"] == "glucometer":
            data["v"] = glucometer
            data["t"] = time
        elif data["n"] == "blood_pressure":
            data["v"] = blood_pressure
            data["t"] = time
        elif data["n"] == "oximeter":
            data["v"] = oximeter
            data["t"] = time
        elif data["n"] == "termometer":
            data["v"] = termometer
            data["t"] = time
    return json.dumps(json_data, indent = 4)

# Function to read the ECG data
def read_ecg_data():
    ecgdata = generate_simulated_ecg() #TODO: CHECK THIS ECG data is a list of values
    #get the current time
    time = time.time()
    #SenML standard
    json_data = json.load(open('deviceconnector_config.json'))["ECGdata"]
    json_data["e"][0]["v"] = ecgdata
    json_data["e"][0]["t"] = time
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
    urlCatalog = config_file["RegistrySystem"]

    ###########
    # LINES USED TO TEST
    ###########
    """RegistrySystem = json.load(open(config_file["RegistrySystem"]))
    urlCatalog = RegistrySystem["catalogURL"]"""

    # read information from the configuration file and POST the information to the catalog
    config = requests.post(f"{urlCatalog}/{config_file['uri']['add_deviceconn']}", data=config_file["information"])
    config_file["information"] = config.json()
    # save the new configuration file
    json.dump(config_file, open("deviceconnector.json", "w"), indent = 4)

    # get the patientID which is equal to the deviceConnectorID (read from the configuration file)
    patientID = config_file["information"]["deviceConnectorID"]
    
    # get the information about the MQTT broker from the catalog using GET request
    MQTTinfo = json.loads(requests.get(f"{urlCatalog}/{config_file['uri']['broker_info']}"))
    broker = MQTTinfo["IP"]
    port = MQTTinfo["port"]
    topic_sensor = MQTTinfo["main_topic"] + config_file["ServiceInformation"]["publish_topic"]["base_topic"] + patientID + config_file["ServiceInformation"]["publish_topic"]["sensorsData"]
    topic_ecg = MQTTinfo["main_topic"] + config_file["ServiceInformation"]["publish_topic"]["base_topic"] + patientID + config_file["ServiceInformation"]["publish_topic"]["ECG"]
    clientID = config_file['serviceName'] + config_file["ServiceInformation"]['serviceID']

    ###########
    # LINES USED TO TEST
    ###########
    """clientID = config_file["ServiceInformation"]['serviceName'] + config_file["ServiceInformation"]['serviceID']
    broker = RegistrySystem["broker"]["IP"]
    port = RegistrySystem["broker"]["port"]
    topic_sensor = RegistrySystem["broker"]["main_topic"] + config_file["ServiceInformation"]["publish_topic"]["base_topic"] + patientID + config_file["ServiceInformation"]["publish_topic"]["sensorsData"]
    topic_ecg = RegistrySystem["broker"]["main_topic"] + config_file["ServiceInformation"]["publish_topic"]["base_topic"] + patientID + config_file["ServiceInformation"]["publish_topic"]["ECG"]"""

    # create an instance of the publisher to publish the data coming from the sensors
    mySensors = SensorsPublisher(clientID, broker, port)
    mySensors.start()
    
    # get the start time
    start_time = time.time()

    try:
        while True: 
            # Publish all the data every minute
            mySensors.publish_ecg(topic_ecg)
            mySensors.publish_sensorsdata(topic_sensor)

            #update the configuration file every 5 minutes by doing a PUT request to the catalog
            # get the current time
            current_time = time.time()
            # check if 5 minutes have passed
            if current_time - start_time > 5*60:
                config_file = json.load(open('deviceconnector_config.json'))
                config = requests.put(f"{urlCatalog}/{config_file['uri']['add_deviceconn']}", json=config_file["information"])
                config_file["information"] = config.json()
                json.dump(config_file, open("deviceconnector_config.json", "w"), indent = 4)
                # update the start time
                start_time = current_time
            # wait for 60 seconds
            time.sleep(60)
    except KeyboardInterrupt:
        # stop the publisher
        mySensors.StopSim()