import time
import json
from MyMQTT import *
import biosppy.signals.ecg as ecg
import requests
import numpy as np
import time
import scipy

class ECGAnalysis:

    """
    ECGAnalysis - SmartHospital IoT platform. Version 1.0.2
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
                        Example: SmartHospitalN/ *** publish_topic ***/PatientN / ***analysis_1***

            
            - "analysis": List of analysis to be performed. Those are the topics where the different
                           analysis will be published.

            - "sampling_frequency": Sampling frequency of the ECG signal, in Hz. 

            For the processed ECG data, after the RR wave detection we provide a snippet of it's morphology, with:

                - "target_frequency": Target frequency of the resampled ECG signal, in Hz.

                - "sample_duration": Duration of the sample to be taken from the resampled ECG signal, in seconds.

    """

    def __init__(self, clientID_sub, clientID_pub, broker, port, topic_sub, fc, servicepub, analysis, target_frequency, sample_duration):

        self.broker = broker
        self.port = port

        self.clientID_sub = clientID_sub
        self.clientID_pub = clientID_pub

        self.topic_sub = topic_sub
        self.servicepub = servicepub

        self.target_frequency = target_frequency
        self.sample_duration = sample_duration

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
        print(topic_parts)

        patient_id = topic_parts[2]
        base_topic = topic_parts[0]
        print(base_topic)

        topic_pub = f"{base_topic}/{self.servicepub}/{patient_id}"

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

        # Resample ECGdata to the desired frequency (e.g., 40Hz), to keep morphology and minimize data.
        resampled_ecg_data = scipy.signal.resample(filtered, int(len(filtered) * self.target_frequency / self.fc))

        # Take the first 10 seconds of the resampled signal
        snippet_length = min(len(resampled_ecg_data), self.sample_duration * self.target_frequency)
        snippet_ecg_data = resampled_ecg_data[:snippet_length]

        # Adjust timestamps for the snippet
        snippet_timestamps = np.linspace(0, self.sample_duration, len(snippet_ecg_data), endpoint=False)

        # ECG filtered output for the snippet
        filtered_data = []
        for i, value in enumerate(snippet_ecg_data):
            entry = {
                "u": "mV",
                "v": value,
                "t": snippet_timestamps[i]  # Adjust timestamp for each sample in the snippet
            }
            filtered_data.append(entry)
        filtered_output = {
            "bn": topic_pubs[0],
            "bt": basetime,
            "e": filtered_data
        }

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
            "e": rr_data
        }

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
        print(f"\nheart rate: {heart_rate} bpm\n")

        self.publish(rr_output, topic_pubs[1])
        print(f"\nRR wave: {rr_wave} ms\n")

        self.publish(filtered_output, topic_pubs[0])


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
    response = requests.post(f"{RegistrySystem}/{conf['information']['uri']['add_service']}", json=conf['information'])
    conf['information'] = response.json()

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Save the new configuration file
        with open("ECGAn_configuration.json", "w") as file:
            json.dump(conf, file, indent=4)
    else:
        print(f"Error: {response.status_code} - {response.text}")


    request = requests.get(f"{RegistrySystem}/{conf['information']['uri']['broker_info']}") #get the broker info
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

    fc = conf["information"]["sampling_frequency"] 
    target_frequency = conf["information"]["target_frequency"]
    sample_duration = conf["information"]["sample_duration"]
    # Create an instance of ECGAnalysis
    myECGAnalysis = ECGAnalysis(clientID_sub, clientID_pub, broker, port, topic_sub, fc, servicepub, analysis, target_frequency, sample_duration)
    myECGAnalysis.startSim()
    start_time = time.time()

    try:
        while True:
            current_time = time.time()
            if current_time - start_time > 5*60:
                config_file = json.load(open('ECGAn_configuration.json'))
                config = requests.put(f"{RegistrySystem}/{conf['information']['uri']['add_service']}", json=config_file["information"])
                if config.status_code == 200:
                    print(f"information: {config}")
                    config_file["information"] = config.json()
                    # print the updated information about the service
                    print(f"information: {config_file['information']}")
                    json.dump(config_file, open("ECGAn_configuration.json", "w"), indent = 4)
                    start_time = current_time
                else:
                    print(f"Error: {config.status_code} - {config.text}")
            else:
                pass
            time.sleep(2)
    except KeyboardInterrupt:
        myECGAnalysis.StopSim()
        