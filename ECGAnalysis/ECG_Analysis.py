import time
import json
from MyMQTT import *
import biosppy.signals.ecg as ecg
import requests
import cherrypy
import numpy as np
import time

class ECGAnalysis:

    def __init__(self, clientID_sub, clientID_pub, broker, port, topic_sub, topic_pub, fc):

        """
        This microservice has both subscriber and publisher capabilities. 
        
        """

        self.broker = broker
        self.port = port

        self.clientID_sub = clientID_sub
        self.clientID_pub = clientID_pub

        self.topic_sub = topic_sub
        self.topic_pub = topic_pub

        self.fc = fc

        # Subscriber Capabilities
        self.ClientSubscriber = MyMQTT(clientID_sub, broker, port, self)  
        self.ClientSubscriber.start()  # Start the MQTT client
        
        # Publish Capabilities
        self.ClientPublisher = MyMQTT(clientID_pub, broker, port, self)
        self.ClientPublisher.start()  # Start the MQTT client
        

    def notify(self, topic, payload):
        message_json = json.loads(payload)
        ecg_data = message_json["e"][0]["v"]
        #time_stamp = ecg_data[0]["t"]
        self.process_and_publish_ecg_signal(ecg_data)

    def process_and_publish_ecg_signal(self,ecg_data):
        # We analyze the ECG with Bioppsy
        out = ecg.ecg(signal=ecg_data, sampling_rate=self.fc, show=False)

        # We get the HR
        heart_rate = out["heart_rate"]
        heart_rate = int(np.mean(heart_rate))

        # Another look at HR, just to be sure I am working correctly with the HRV
        #hr_from_RR = int(60 / np.mean(np.diff(out["rpeaks"]) / self.fc))

        # We identify outlier peaks
        rr_wave = np.diff(out["rpeaks"])

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


        current_time = time.time() # è corretto???????

        output = {
            "bn": self.topic_pub,
            "e": [
                {
                    "n": "hr",
                    "u": "bpm",  
                    "t": current_time,
                    "v": heart_rate,
                },
                {
                    "n": "RR_wave",
                    "u": "ms",  
                    "v": rr_wave.tolist(),
                }
            ]
        }

        self.publish(output)

    def publish(self,output):

        self.ClientPublisher.myPublish(self.topic_pub, output)
        
        return print("published")
        

    def startSim(self):
        self.ClientSubscriber.mySubscribe(self.topic_sub)
    
    def StopSim(self):
        self.ClientSubscriber.unsubscribe()  # Automatic, no need to specify the topics
        self.ClientSubscriber.stop()



if __name__ == "__main__":

    # Load configuration from the registry system
    
    conf = json.load(open("ECGAn_configuration.json"))
    RegistrySystem = json.load(open(conf["RegistrySystem"]))
    urlCatalog = RegistrySystem["catalogURL"]
    #MQTTinfo = json.loads(requests.get(f"{urlCatalog}/broker"))
    
    clientID_sub = "SmartHospital308sub"  # Assuming a fixed client ID for simplicity
    clientID_pub = "SmartHospital308pub"
    broker = "test.mosquitto.org"#MQTTinfo["IP"]
    port = 1883 #MQTTinfo["port"]
    topic_sub =  "SmartHospital308/Patient1/ECG"#MQTTinfo["main_topic"] + conf["information"]["subscribe_topic"]
    topic_pub = "SmartHospital308/Patient1/ECG_analyzed"

    fc = conf["information"][0]["sampling_frequency"] #questo facciamo che lo prende dalla configurazione!

    # Create an instance of ECGAnalysis
    myECGAnalysis = ECGAnalysis(clientID_sub, clientID_pub, broker, port, topic_sub, topic_pub, fc)
    myECGAnalysis.startSim()

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        myECGAnalysis.StopSim()
        
