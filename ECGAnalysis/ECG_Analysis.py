import time
import json
from MyMQTT import *
import biosppy.signals.ecg as ecg
import requests
import numpy as np
import time

class ECGAnalysis:

    """
    Microservice for the SmartHospital IoT platform.
    This microservice is responsible for analyzing the ECG data and publishing the results.

    Standard Configuration file: ECGAn_configuration.json

    """

    def __init__(self, clientID_sub, clientID_pub, broker, port, topic_sub, fc):

        """
        This microservice has both subscriber and publisher capabilities. 
        It subscribes to the ECG data and publishes the analyzed ECG data.
        """

        self.broker = broker
        self.port = port

        self.clientID_sub = clientID_sub
        self.clientID_pub = clientID_pub

        self.topic_sub = topic_sub
        print(topic_sub)

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
        time.sleep(2)

        """
        print(len(rr_wave))
        q1 = np.percentile(rr_wave, 25)
        q3 = np.percentile(rr_wave, 75)
        iqr = q3 - q1
        
        # Define outlier thresholds
        lower_threshold = q1 - 1.5*iqr
        upper_threshold = q3 + 1.5*iqr
        
        # Identify outliers
        outliers = [rr for rr in rr_wave if rr < lower_threshold or rr > upper_threshold]
        """

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
                    "v": rr_wave.tolist(),
                }
            ]
        }
        print(output)
        print(topic_pub)
        self.publish(output, topic_pub)

    def publish(self,output, topic_pub):

        self.ClientPublisher.myPublish(topic_pub, output)
        
        return print("published")
        

    def startSim(self):
        self.ClientSubscriber.mySubscribe(self.topic_sub)
    
    def StopSim(self):
        self.ClientSubscriber.unsubscribe()  # Automatic, no need to specify the topics
        self.ClientSubscriber.stop()



if __name__ == "__main__":


    conf = json.load(open("ECGAn_configuration.json"))
    RegistrySystem = conf["RegistrySystem"]

    # Make POST request
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


    request = requests.get(f"{RegistrySystem}/broker")
    MQTTinfo = json.loads(request.text)
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
        
