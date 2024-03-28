import json
import requests
from StatusPublisher import *
import time
import numpy as np
import copy
# Microservice: PatientStatus
# Description: 
# This microservice calculates the status of a patient based on the data collected from the sensors.
# The data are retrieved from the database via Restful communication. 
# The status is calculated using a fuzzy logic system. 
# The status is then published to the broker using MQTT.

class PatientStatus(object):
    def __init__(self):
        # load the configuration file
        self.conf=json.load(open("PatientStatus_config.json")) 
        ps_conf = copy.deepcopy(self.conf)
        # get the IP address of the registry system
        self.urlRegistrySystem = self.conf["RegistrySystem"] 
        # register the service to the catalog
        config = json.dumps(self.conf["information"])
        # post the configuration to the catalog
        config = requests.post(f"{self.urlRegistrySystem}{self.conf["information"]["uri_catalog"]["service"]}",json=config)
        ps_conf["information"][0] = config.json()
        # save the new configuration file 
        json.dump(ps_conf, open("PatientStatus_config.json", "w"), indent=4)
        print("Service registered to the catalog")
        # get the database information from the catalog
        DB = requests.get(f"{self.urlRegistrySystem}{self.conf["information"]["uri_catalog"]["DB"]}")
        self.Database = DB.json()["urlDB"]
        # get the mqtt information from the catalog
        b = requests.get(f"{self.urlRegistrySystem}{self.conf["information"]["uri_catalog"]["broker"]}")
        self.broker = b.json()
        self.clientID = self.conf["information"]["serviceName"]+str(self.conf["information"]["serviceID"])
        self.status_client = StatusManager(self.clientID, self.broker["IP"],self.broker["port"] )
        # start the mqtt publisher
        self.status_client.startSim()
    


    def get_status_and_publish(self):
        patientList = requests.get(f"{self.urlRegistrySystem}{self.conf["information"]["uri_catalog"]["patient"]}")
        patID = patientList.json()["patientID"]
        condition = patientList.json()["condition"]
        
        for pat in patID:
            range = 300
            # TODO ma questi come faccio a metterli nel config e non scriverli così?
            response_gluco = requests.get(f"{self.Database}{self.conf["information"]["uri_DB"]["gluco"]}/patient{pat}?range={range}")  
            response_bps = requests.get(f"{self.Database}{self.conf["information"]["uri_DB"]["bps"]}/patient{pat}?range={range}")
            response_oxim = requests.get(f"{self.Database}{self.conf["information"]["uri_DB"]["oxim"]}/patient{pat}?range={range}")
            response_ECG = requests.get(f"{self.Database}{self.conf["information"]["uri_DB"]["ecg"]}/patient{pat}?range={range}")
            response_termo = requests.get(f"{self.Database}{self.conf["information"]["uri_DB"]["temp"]}/patient{pat}?range={range}")
            response_RR = requests.get(f"{self.Database}{self.conf["information"]["uri_DB"]["RR"]}/patient{pat}?range={range}")
            # definition of the data dictionary containing the data of the patient 
            data = {"gluco": response_gluco.json()["e"][0]["v"], "bps": response_bps.json()["e"][0]["v"], "oxim": response_oxim.json()["e"][0]["v"], "ECG": response_ECG.json()["e"][0]["v"], "termo": response_termo.json()["e"][0]["v"],"termo": response_RR.json()["e"][0]["v"], "condition": condition[patID.index(pat)]}
            s = self.calculate_status(data)
            stat = {"patientID": pat, "status": s, "timestamp": time.time()}
            topic = self.broker["main_topic"]+"patient"+str(pat)+self.conf["information"]["pubish_topic"]
            self.status_client.publish(topic, stat) 

    def calculate_status(self, data):
        # compute of the mean value of the parameters
        gluco_mean = np.mean(data["gluco"])
        bps_mean = np.mean(data["bps"])
        oxim_mean = np.mean(data["oxim"])
        ECG_mean = np.mean(data["ECG"])  
        RR = data["RR"]
        # count the number of RR values that are too high or too low
        RR_count = 0
        for i in range(len(RR)):
            if RR[i] < 850 or RR[i] > 950:  
                RR_count += 1

        termo_mean = np.mean(data["termo"])
        condition = data["condition"]

        # Definition of the status vector, every element represents a different parameter
        # 0 -> gluco
        # 1 -> bps
        # 2 -> oxim
        # 3 -> ECG
        # 4 -> RR
        # 5 -> termo
        # the value of the element is the membership degree of the parameter to the status
        stat_vett = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        # Fuzzy rules
        if "d" in condition:
            stat_vett[0] = max(0, 1 - (gluco_mean - 70) / 130)  
        else:
            stat_vett[0] = max(0, 1 - abs(gluco_mean - 105) / 35)

        if condition == "n" or "c" in condition:
            stat_vett[1] = max(0, (bps_mean - 100) / 40) 
        else:
            stat_vett[1] = max(0, (bps_mean - 120) / 50)

        stat_vett[2] = max(0, (98 - oxim_mean) / 10)  

        stat_vett[3] = max(0, (ECG_mean - 80) / 20)  

        stat_vett[4] = max(0, 1 - RR_count / 20)  

        stat_vett[5] = max(0, 1 - abs(termo_mean - 36) / 2)  

        # Definition oh the weights for the aggregation
        weights = np.array([1.5, 2.0, 2.5, 2.0, 1.5, 1.0])  # oxim, bps, ECG, RR are more important

        # Aggregation of the information 
        weighted_aggregated_status = np.dot(stat_vett, weights) / np.sum(weights)

        # Definition of the status
        if weighted_aggregated_status >= 0.7:
            status = "very good"
        elif weighted_aggregated_status >= 0.4:
            status = "regular"
        else:
            status = "bad"
            
        return status

    
    def update_service(self):
        # update the service in the catalog
        config = json.dumps(self.conf["information"])
        config = requests.put(f"{self.urlRegistrySystem}{self.conf["information"]["uri_catalog"]["service"]}",json=config)
        self.conf["information"] = config.json()
        # save the new configuration file 
        json.dump(self.conf, open("PatientStatus_config.json", "w"), indent=4)
        print("Service updated in the catalog")
    
if __name__ == "__main__":
    status = PatientStatus()
    while True:
        status.get_status_and_publish()
        status.update_service()
        # every 5 minutes the status is calculated and published for every patient
        time.sleep(300) 

