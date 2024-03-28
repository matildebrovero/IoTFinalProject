import time
import json
from MyMQTT import *
import biosppy.signals.ecg as ecg
import requests
import numpy as np
import time

class ECGAnalysis:

    """
    ECGAnalysis - SmartHospital IoT platform. Version 1.0.1
    This microservice is responsible for analyzing the ECG data and publishing the results to the Database Connector.
    The results are published according to the SenML format.
    
        Input: 
            - ECG data from device connector.

        Output: 
            - Heart Rate
            - Filtered ECG signal
            - RR wave

    --------------------------------------------------------------------------
    --------------         standard configuration          -------------------
    --------------------------------------------------------------------------

    Standard Configuration file provided: ECGAn_configuration.json
    The parameters of the configuration file are:

        - "RegistrySystem": URL of the Registry System
        - "information": 
            - "serviceName": Name of the service

            - "serviceID": ID of the service, automatically assigned by the Registry System 

            - "subscribe_topic": Where the ECG data are expected to come in input. Data are taken in with a MQTT Wildcard +,
                        Example: SmartHospitalN/*** PatientN ***/ECG
                            The data are then re-published in the "publish_topic" topic, with the *** PatientN *** information
                            filled with the actual patient data. 

            - "publish_topic": Publish topic of the service, the main topic where the "analysis" will be published
                        Example: SmartHospitalN/PatientN/ *** publish_topic *** / ***analysis_1***

            
            - "analysis": List of analysis to be performed. Those are the topics where the different
                           analysis will be published.

            - "sampling_frequency": Sampling frequency of the ECG signal, in Hz. 

    """

    def __init__(self, clientID_sub, clientID_pub, broker, port, topic_sub, fc, servicepub, analysis):

        self.broker = broker
        self.port = port

        self.clientID_sub = clientID_sub
        self.clientID_pub = clientID_pub

        self.topic_sub = topic_sub
        self.servicepub = servicepub

        self.analysis = analysis

        self.fc = fc

        # Subscriber Capabilities
        self.ClientSubscriber = MyMQTT(clientID_sub, broker, port, self)  
        self.ClientSubscriber.start()  # Start the MQTT client
        
        # Publish Capabilities
        self.ClientPublisher = MyMQTT(clientID_pub, broker, port, self)
        self.ClientPublisher.start()  # Start the MQTT client
        

    def notify(self, topic, payload):

        topic_parts = topic.split("/")
        patient_id = topic_parts[1]
        base_topic = topic_parts[0]

        topic_pub = f"{base_topic}/{patient_id}/{self.servicepub}"

        message_json = json.loads(payload)
        data = message_json["e"]
        ecg_data = np.array([entry['v'] for entry in data])
        basetime = message_json["bt"]

        topic_pubs = [f"{topic_pub}/{self.analysis[0]}",f"{topic_pub}/{self.analysis[1]}",f"{topic_pub}/{self.analysis[2]}"]

        self.process_and_publish_ecg_signal(ecg_data, basetime, topic_pubs)


    def process_and_publish_ecg_signal(self,ecg_data,basetime,topic_pubs):

        # ECG analysis
        out = ecg.ecg(signal=ecg_data, sampling_rate=self.fc, show=False)
        heart_rate = out["heart_rate"]
        heart_rate = int(np.mean(heart_rate))
        filtered = out["filtered"]
        rr_wave = np.diff(out["rpeaks"]/fc)


        # ECG filtered output
        filtered_data = [] # Accumulate all entries here
        for i, value in enumerate(filtered):
            entry = {
                "u": "mV",
                "v": value,
                "t": i * 1 / self.fc   # Adjust timestamp for each sample according to the "basetime"
            }
            filtered_data.append(entry)
        filtered_output = {
            "bn": topic_pubs[0],
            "bt": basetime,
            "e": filtered_data
        }
        self.publish(filtered_output, topic_pubs[0])
    
        # RR wave output
        rr_data = []  # Accumulate all entries here
        for i, value in enumerate(rr_wave):
            entry = {
                "u": "ms",
                "v": value,
                "t": i * 1 / self.fc   # Adjust timestamp for each sample according to the "basetime"
            }
            rr_data.append(entry)
        rr_output = {
            "bn": topic_pubs[1],
            "bt": basetime,
            "e": filtered_data
        }
        self.publish(rr_output, topic_pubs[1])
    

        # Heart rate output
        heart_rate_output = {
            "bn": topic_pubs[2],
            "bt": basetime,
            "e": [
                {
                    "u": "bpm",
                    "v": heart_rate,
                    "t": 0
                }
            ]
        }   
        self.publish(heart_rate_output, topic_pubs[2])

    def publish(self, output, topic_pub):
        self.ClientPublisher.myPublish(topic_pub, output)
        return print("published")
        

    def startSim(self):
        self.ClientSubscriber.mySubscribe(self.topic_sub)
    
    def StopSim(self):
        self.ClientSubscriber.unsubscribe() 
        self.ClientSubscriber.stop()



if __name__ == "__main__":

    # Load the configuration file
    conf = json.load(open("ECGAn_configuration.json"))
    RegistrySystem = conf["RegistrySystem"]

    # Make POST request to the registry system
    response = requests.post(f"{RegistrySystem}/service", json=conf)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Save the new configuration file
        with open("ECGAn_configuration.json", "w") as file:
            json.dump(response.json(), file, indent=4)
    else:
        print(f"Error: {response.status_code} - {response.text}")


    request = requests.get(f"{RegistrySystem}/broker") #get the broker info
    MQTTinfo = json.loads(request.text) 

    # Define the topics and the MQTT clientID, with the new configuration got from the RegistrySystem
    
    servicepub = conf["information"]["publish_topic"]
    clientID_sub = conf["information"]["serviceName"] + str(conf["information"]["serviceID"]) + "_sub"
    clientID_pub = conf["information"]["serviceName"] + str(conf["information"]["serviceID"]) + "_pub"
    broker = MQTTinfo["IP"]
    port = MQTTinfo["port"]
    analysis = conf["information"]["analysis"]
    topic_sub =  MQTTinfo["main_topic"] + conf["information"]["subscribe_topic"]

    # The sampling frequency of the ECG is a project choice, so it is defined considering that all physical device will have the same frequency.

    fc = conf["information"]["sampling_frequency"] # TODO: check if I can hardcode the frequency into the configuration file, i think is doable since we can assume that every device is the same.
    # Create an instance of ECGAnalysis
    myECGAnalysis = ECGAnalysis(clientID_sub, clientID_pub, broker, port, topic_sub, fc, servicepub, analysis)
    myECGAnalysis.startSim()

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        myECGAnalysis.StopSim()
        
