import time
import json
import numpy as np
from MyMQTT import *
import neurokit2 as nk
import requests

sampling_rate=100

def generate_simulated_ecg(duration=60):
    
    """
    Function that simulates ECG data.
    """

    ecg_signal = nk.ecg_simulate(duration=duration,sampling_rate=sampling_rate, noise=0.1, heart_rate=70, heart_rate_std=5, method='ecgsyn')

    return ecg_signal.tolist()

class SensorPublisher:
    def __init__(self, clientID, broker, port, topic):
        self.topic = topic
        self.ClientPublisher = MyMQTT(clientID, broker, port, self)  
        self.last_timestamp = time.time()  # Store the timestamp of the last published data
        self.ClientPublisher.start()


    def publish(self):
        self.ecg_data = read_sensor_data()
        current_time = time.time()
        self.last_timestamp = current_time

        # Create a list to hold all ECG samples
        ecg_samples = []

        # https://datatracker.ietf.org/doc/html/rfc8428#section-4.5

        for index, ecg_value in enumerate(self.ecg_data):
            # Create a dictionary for each ECG sample
            ecg_sample = {
                "u": "mV",  # Assuming ECG data is in millivolts
                "t": index * 1/sampling_rate,
                "v": ecg_value
            }
            # Add the sample to the list
            ecg_samples.append(ecg_sample)

        # Create the output payload containing all ECG samples
        output = {
            "bn": self.topic,
            "bt": current_time,
            "e": ecg_samples
        }

        # Publish the payload
        self.ClientPublisher.myPublish(self.topic, output)
        print(f"Published new ECG data: {output}")
        print(self.topic)


    def StopPublish(self):
        self.ClientPublisher.stop()

def read_sensor_data():
    """
    Reads simulated ECG data.
    **Placeholder for actual ECG data retrieval:**
    This function should ideally retrieve real-time ECG data from a connected device
    or sensor. However, for simulation purposes, it currently fetches the
    pre-generated data from the `generate_simulated_ecg` function.
    """
    return generate_simulated_ecg()

if __name__ == "__main__":
    
    # Load configuration from the registry system
    conf = json.load(open("ECGAn_configuration.json"))
    RegistrySystem = conf["RegistrySystem"]
    request = requests.get(f"{RegistrySystem}/broker")
    MQTTinfo = json.loads(request.text)
    clientID = "ECG_Publisher"
    broker = MQTTinfo["IP"]
    port = MQTTinfo["port"]
    topic =  "SmartHospital308/Patient1/ECG"


    mySensor = SensorPublisher(clientID, broker, port, topic)
    print('Welcome to the ECG data publisher\n')

    try:
        while True:
            print("presleep")
            time.sleep(10)
            print("postsleep")
            mySensor.publish()
            print("Published")
              
    except KeyboardInterrupt:
        mySensor.StopPublish()