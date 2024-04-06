from MyMQTT import * #importing MyMQTT class from MyMQTT.py
import time
import json
import requests
from datacreator import * #importing the functions to fake the data from the sensors

""" 
    DeviceConnector - SmartHospital IoT platform. Version 1.0.1 
    This microservice is responsible for publishing the data coming from the sensors to the MQTT broker. Each patient has a unique ID and has its own device connector with temperature, blood pressure, oximeter, glucometer and ECG data.

    In this version the data are simulated by the functions in the datacreator.py file. The data are published in SenML format to the MQTT broker.
 
        Output:  
            - data from the sensors (temperature, blood pressure, oximeter, glucometer) in SenML format in the topic: SmartHospitalN/Monitoring/PatientN/sensorsData
            - ECG data in SenML format in the topic: SmartHospitalN/Monitoring/PatientN/ecgData

    -------------------------------------------------------------------------- 
    --------------         standard configuration          ------------------- 
    -------------------------------------------------------------------------- 
 
    Standard Configuration file provided: deviceconnector_config.json
    The parameters of the configuration file are: 
 
        - "RegistrySystem": URL of the Registry System 

        - "information":  
            - "serviceID": ID of the service, automatically assigned by the Registry System  
            - "serviceName": Name of the service = "DeviceConnector"
            - "measureType": Measurements that can be done by the sensors
            - "availableServices": List of communication protocols available in the device connector 
            - "publish_topic": Publish topic of the service, the main topic where the "analysis" will be published 
                        Example: SmartHospitalN/Monitoring/PatientN/**sensorsData** or **ecgData** 
            - "uri": List of URIs to ask for information to the Registry System
                - "add_deviceconn": URI to add the device connector to the Registry System
                - "broker_info": URI to get the information about the MQTT broker from the Registry System
            - "resources": List of sensors available in the device connector
        - "sensorsData": SenML format for the sensors data
        - "ECGdata": SenML format for the ECG data
    """ 


# Function to read the data from the sensors
def read_sensors_data():
    glucometer = read_glucometer()
    blood_pressure = read_blood_pressure()
    oximeter = read_oximeter()
    termometer = read_body_temperature()
    # Get the current time
    t = time.time()
    # SenML standard
    json_data = json.load(open('deviceconnector_config.json'))["sensorData"]
    for data in json_data["e"]:
        if data["n"] == "glucometer":
            data["v"] = glucometer
            data["t"] = t
        elif data["n"] == "bloodpressure":
            data["v"] = blood_pressure
            data["t"] = t
        elif data["n"] == "oximeter":
            data["v"] = oximeter
            data["t"] = t
        elif data["n"] == "termometer":
            data["v"] = termometer
            data["t"] = t
    return json.dumps(json_data, indent = 4)

# Function to read the ECG data
def read_ecg_data():
    ecgdata, ECG_fc = generate_simulated_ecg()
    #get the current time
    t = time.time()
    #SenML standard
    json_data = json.load(open('deviceconnector_config.json'))["ECGdata"]
    json_data["bt"] = t
    ecg_samples = []
    for index, ecg_value in enumerate(ecgdata):
        # Create a dictionary for each ECG sample
        ecg_sample = {
            "u": "mV",  
            "t": index * 1/ECG_fc,
            "v": ecg_value
        }
        # Add the sample to the list
        ecg_samples.append(ecg_sample)
    json_data["e"] = ecg_samples
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
        print(f"Sensors have published new data: on topic {self.topic}") #output not 
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
    config_file = json.load(open('deviceconnector_config.json'))
    # load the registry system
    urlCatalog = config_file["RegistrySystem"]

    ###########
    # LINES USED TO TEST
    ###########
    """RegistrySystem = json.load(open(config_file["RegistrySystem"]))
    urlCatalog = RegistrySystem["catalogURL"]"""
    print("\n\n\nPOST request to update the configuration file\n\n\n")
    # read information from the configuration file and POST the information to the catalog
    config = requests.post(f"{urlCatalog}/{config_file['information']['uri']['add_deviceconn']}", json=config_file["information"])
    if config.status_code == 200:
        config_file["information"] = config.json()
        print(f"\n\n\n{config_file['information']}")
        # save the new configuration file
        print("updated configuration file")
        json.dump(config_file, open("deviceconnector_config.json", "w"), indent = 4)
        print("configuration file saved")
    else:
        print(f"Error: {config.status_code} - {config.text}")

    # get the patientID which is equal to the deviceConnectorID (read from the configuration file)
    patientID = config_file["information"]["deviceConnectorID"]
    
    # get the information about the MQTT broker from the catalog using GET request
    MQTTinfo = json.loads(requests.get(f"{urlCatalog}/{config_file['information']['uri']['broker_info']}").text)
    broker = MQTTinfo["IP"]
    port = MQTTinfo["port"]
    topic_sensor = MQTTinfo["main_topic"] + config_file["information"]["publish_topic"]["base_topic"] + str(patientID) + config_file["information"]["publish_topic"]["sensors"]
    print(topic_sensor)
    topic_ecg = MQTTinfo["main_topic"] + config_file["information"]["publish_topic"]["base_topic"] + str(patientID) + config_file["information"]["publish_topic"]["ecg"]
    print(topic_ecg)
    clientID = config_file["information"]['serviceName'] + str(config_file["information"]['deviceConnectorID'])

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
        i = 0
        while True: 
            print(f"\n\n{i}th iteration")
            # Publish all the data every minute
            mySensors.publish_ecg(topic_ecg)
            mySensors.publish_sensorsdata(topic_sensor)

            #update the configuration file every 5 minutes by doing a PUT request to the catalog
            # get the current time
            current_time = time.time()
            # check if 5 minutes have passed
            if current_time - start_time > 5*60:
                print("\n\n\PUT request to update the configuration file\n\n\n")
                config_file = json.load(open('deviceconnector_config.json'))
                config = requests.put(f"{urlCatalog}/{config_file['information']['uri']['add_deviceconn']}", json=config_file["information"])
                if config.status_code == 200:
                    config_file["information"] = config.json()
                    print(config_file)
                    json.dump(config_file, open("deviceconnector_config.json", "w"), indent = 4)
                    # update the start time
                    start_time = current_time
                else:
                    print(f"Error: {config.status_code} - {config.text}")
            i += 1
            # wait for 60 seconds
            time.sleep(60)
    except KeyboardInterrupt:
        # stop the publisher
        mySensors.StopPublish()