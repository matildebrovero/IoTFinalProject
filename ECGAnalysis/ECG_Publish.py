import time
import json
import numpy as np
from MyMQTT import *
import neurokit2 as nk

def generate_simulated_ecg(duration=60, sampling_rate=250, noise_level=0.5):
    
    """
    Function that simulates ECG data.
    """

    ecg_signal = nk.ecg_simulate(duration=duration,sampling_rate=sampling_rate, noise=0.01, heart_rate=80, heart_rate_std=30, method='ecgsyn')

    return ecg_signal.tolist()

class SensorPublisher:
    def __init__(self, clientID, broker, port, topic):
        self.topic = topic
        self.ClientPublisher = MyMQTT(clientID, broker, port, self)  
        self.last_timestamp = time.time()  # Store the timestamp of the last published data
        self.ClientPublisher.start()

#    def start(self):
#        self.ClientPublisher.start()
        

    def publish(self):

        self.ecg_data = read_sensor_data()
        current_time = time.time()
        elapsed_time = current_time - self.last_timestamp
        self.last_timestamp = current_time

        output = {
            "bn": self.topic,
            "e": [
                {
                    "n": "ecg",
                    "u": "mV",  # Assuming ECG data is in millivolts
                    "t": elapsed_time,
                    "v": [ecg_value for ecg_value in self.ecg_data],
                }
            ]
        }

        self.ClientPublisher.myPublish(self.topic, output)
        print(f"Published new ECG data: {output}")

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
    
    clientID = "SmartHospital308"
    broker = "test.mosquitto.org"  # Adjust broker address if needed
    port = 1883
    topic = "SmartHospital308/Patient1/ECG"

    mySensor = SensorPublisher(clientID, broker, port, topic)
    print('Welcome to the ECG data publisher\n')

    try:
        while True:
            time.sleep(10)  # Publish data every 5 minutes
            mySensor.publish()
    except KeyboardInterrupt:
        mySensor.StopPublish()