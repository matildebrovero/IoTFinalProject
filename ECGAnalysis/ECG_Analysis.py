import time
import json
from MyMQTT import *
import biosppy.signals.ecg as ecg
import requests
import numpy as np
import time

class ECGAnalysis:

    """
    ECGAnalysis - SmartHospital IoT platform. Version 1.0.0
    This microservice is responsible for analyzing the ECG data and publishing the results to the Database Connector.
    The results are published according to the SenML format.
    
        Input: 
            - ECG data from device connector.

        Output: 
            - Heart Rate
            - Filtered ECG signal
            - RR wave

    Standard Configuration file provided: ECGAn_configuration.json
    """

    def __init__(self, clientID_sub, clientID_pub, broker, port, topic_sub, fc):

        self.broker = broker
        self.port = port

        self.clientID_sub = clientID_sub
        self.clientID_pub = clientID_pub

        self.topic_sub = topic_sub

        self.fc = fc

        # Subscriber Capabilities
        self.ClientSubscriber = MyMQTT(clientID_sub, broker, port, self)  
        self.ClientSubscriber.start()  # Start the MQTT client
        
        # Publish Capabilities
        self.ClientPublisher = MyMQTT(clientID_pub, broker, port, self)
        self.ClientPublisher.start()  # Start the MQTT client
        

    def notify(self, topic, payload):

        topic = topic.split("/")            
        patient_id = topic[1]
        basetopic = topic[0]
        topic_pub = f"{basetopic}/{patient_id}/ECG_Analysis"

        message_json = json.loads(payload)
        ecg_data = message_json["e"][0]["v"]
        time_stamp = message_json["e"][0]["t"]
        self.process_and_publish_ecg_signal(ecg_data, time_stamp, topic_pub)

    def process_and_publish_ecg_signal(self,ecg_data,time_stamp,topic_pub):

        # We analyze the ECG with Bioppsy
        out = ecg.ecg(signal=ecg_data, sampling_rate=self.fc, show=False)

        # We get the HR and average it
        heart_rate = out["heart_rate"]
        heart_rate = int(np.mean(heart_rate))

        # We get the filtered ECG
        filtered = out["filtered"]

        # We get the RR wave
        rr_wave = np.diff(out["rpeaks"]/fc)

        print(heart_rate)
        print(int(60/np.mean(rr_wave)))

# ADAPT TO SENML FORMAT! 
        output = {
            "bn": topic_pub,
            "e": [
                {
                    "n": "ECG_filtered",
                    "u": "mV",  # Assuming ECG data is in millivolts
                    "t": time_stamp,
                    "v": filtered.tolist(),
                },
                {
                    "n": "HR",
                    "u": "bpm",  
                    "t": time_stamp,
                    "v": heart_rate,
                },
                {
                    "n": "RR_wave",
                    "u": "ms",  
                    "t": time_stamp,
                    "v": rr_wave.tolist(),
                }
            ]
        }
        print(output)
        print(topic_pub)
        self.publish(output, topic_pub)

    """
        # Send individual samples of filtered ECG
        for i, value in enumerate(filtered):
            filtered_entry = {
                "bn": topic_pub,
                "e": [
                    {
                        "n": f"ECG_filtered_{i}",  # Unique name for each filtered ECG sample
                        "u": "mV",
                        "t": time_stamp + i * self.time_interval,  # Adjust timestamp for each sample
                        "v": value,
                    }
                ]
            }
            self.publish(filtered_entry, topic_pub)

        # Send heart rate
        output_heart_rate = {
            "bn": topic_pub,
            "e": [
                {
                    "n": "HR",
                    "u": "bpm",
                    "t": time_stamp,
                    "v": heart_rate,
                }
            ]
        }
        self.publish(output_heart_rate, topic_pub)

        # Send RR wave samples individually
        for i, rr_sample in enumerate(rr_wave):
            rr_wave_entry = {
                "bn": topic_pub,
                "e": [
                    {
                        "n": f"RR_wave_{i}",  # Unique name for each RR wave sample
                        "u": "ms",
                        "t": time_stamp + i * self.time_interval,  # Adjust timestamp for each sample
                        "v": rr_sample,
                    }
                ]
            }
            self.publish(rr_wave_entry, topic_pub)

    """

    def publish(self, output, topic_pub):
        self.ClientPublisher.myPublish(topic_pub, output)
        return print("published")
        

    def startSim(self):
        self.ClientSubscriber.mySubscribe(self.topic_sub)
    
    def StopSim(self):
        self.ClientSubscriber.unsubscribe()  # Automatic, no need to specify the topics
        self.ClientSubscriber.stop()



if __name__ == "__main__":

    # Load the configuration file
    conf = json.load(open("ECGAn_configuration.json"))
    RegistrySystem = conf["RegistrySystem"]

    # Make POST request to the registry system
    response = requests.post(f"{RegistrySystem}/service", json=conf)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:

        # Print the response text
        print("Response from the server:")
        print(response.text)

        # Save the new configuration file
        with open("ECGAn_configuration.json", "w") as file:
            json.dump(response.json(), file, indent=4)
        

    else:
        print(f"Error: {response.status_code} - {response.text}")


    request = requests.get(f"{RegistrySystem}/broker") #get the broker info
    MQTTinfo = json.loads(request.text) 

    # Define the topics and the MQTT clientID, with the new configuration got from the RegistrySystem
    
    clientID_sub = conf["information"][0]["serviceName"] + str(conf["information"][0]["serviceID"]) + "_sub"
    clientID_pub = conf["information"][0]["serviceName"] + str(conf["information"][0]["serviceID"]) + "_pub"
    broker = MQTTinfo["IP"]
    port = MQTTinfo["port"]

    topic_sub =  MQTTinfo["main_topic"] + conf["information"][0]["subscribe_topic"]
    print(topic_sub)
    print(broker)

    fc = conf["information"][0]["sampling_frequency"] #questo facciamo che lo prende dalla configurazione!




    # Create an instance of ECGAnalysis
    myECGAnalysis = ECGAnalysis(clientID_sub, clientID_pub, broker, port, topic_sub, fc)
    myECGAnalysis.startSim()

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        myECGAnalysis.StopSim()
        
