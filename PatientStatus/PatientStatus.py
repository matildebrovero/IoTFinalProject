# pip install numpy
# pip install fuzzylogic

import json
import requests
from StatusPublisher import *
import time
import numpy as np
import copy


class PatientStatus(object):
    def __init__(self):
        # load the configuration file
        self.conf=json.load(open("PatientStatus_config.json")) 
        ps_conf = copy.deepcopy(self.conf)
        self.urlRegistrySystem = self.conf["RegistrySystem"] # get the IP address of the registry system
        # register the service to the catalog
        config = json.dumps(self.conf["information"][0])
        # post the configuration to the catalog
        config = requests.post(f"{self.urlRegistrySystem}/service",json=config)
        ps_conf["information"][0] = config.json()
        # save the new configuration file 
        json.dump(ps_conf, open("PatientStatus_config.json", "w"), indent=4)
        print("Service registered to the catalog")
        # get the database information from the catalog
        DB = requests.get(f"{self.urlRegistrySystem}/DBadaptor")
        self.Database = DB.json()["urlDB"]
        # get the mqtt information from the catalog
        b = requests.get(f"{self.urlRegistrySystem}/broker")
        self.broker = b.json()
        self.clientID = self.conf["information"][0]["serviceName"]+str(self.conf["information"][0]["serviceID"])
        self.status_client = StatusManager(self.clientID, self.broker["IP"],self.broker["port"] )
        # start the mqtt publisher
        self.status_client.startSim()

    def get_status_and_publish(self):

        patientList = requests.get(f"{self.urlRegistrySystem}/patientAndCondition")
        patID = patientList.json()["patientID"]
        condition = patientList.json()["condition"]
        
        for pat in patID:
            range = 300
            response_gluco = requests.get(f"{self.Database}/glucometer/patient{pat}?range={range}")  
            response_bps = requests.get(f"{self.Database}/blood_pressure/patient{pat}?range={range}")
            response_oxim = requests.get(f"{self.Database}/oximeter/patient{pat}?range={range}")
            response_ECG = requests.get(f"{self.Database}/ECG/patient{pat}?range={range}")
            response_termo = requests.get(f"{self.Database}/temperature/patient{pat}?range={range}")
            data = {"gluco": response_gluco.json()["e"][0]["v"], "bps": response_bps.json()["e"][0]["v"], "oxim": response_oxim.json()["e"][0]["v"], "ECG": response_ECG.json()["e"][0]["v"], "termo": response_termo.json()["e"][0]["v"], "condition": condition[patID.index(pat)]}
            s = self.calculate_status(data)
            s = "good" # da togliere
            stat = {"patientID": pat, "status": s, "timestamp": time.time()}
            topic = self.broker["main_topic"]+"patient"+str(pat)+self.conf["information"][0]["pubish_topic"]
            self.status_client.publish(topic, stat) 

    def calculate_status(self, data):
        gluco_mean = np.mean(data["gluco"])
        bps_mean = np.mean(data["bps"])
        oxim_mean = np.mean(data["oxim"])
        ECG_mean = np.mean(data["ECG"])  # per ECG
        RR = data["RR"]
        RR_count = 0
        for i in range(len(RR)):
            if RR[i] < 20 or RR[i] > 100:  # TODO mettere la soglia giusta
                RR_count += 1

        termo_mean = np.mean(data["termo"])
        condition = data["condition"]

        # vettore di status, ogni posizione rappresenta una misurazione
        # 0 -> gluco
        # 1 -> bps
        # 2 -> oxim
        # 3 -> ECG
        # 4 -> RR
        # 5 -> termo
        # il valore rappresenta il grado di appartenenza alla condizione good/bad
        stat_vett = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        # Regole fuzzy
        if condition == "d":
            stat_vett[0] = max(0, 1 - (gluco_mean - 70) / 130)  # fuzzification per la glicemia
        else:
            stat_vett[0] = max(0, 1 - abs(gluco_mean - 105) / 35)

        if condition == "n" or condition == "c":
            stat_vett[1] = max(0, (bps_mean - 100) / 40)  # fuzzification per la pressione sanguigna
        else:
            stat_vett[1] = max(0, (bps_mean - 120) / 50)

        stat_vett[2] = max(0, (97 - oxim_mean) / 10)  # fuzzification per la saturazione di ossigeno

        stat_vett[3] = max(0, (ECG_mean - 80) / 20)  # fuzzification per l'ECG

        stat_vett[4] = max(0, 1 - RR_count / 10)  # fuzzification per la frequenza respiratoria

        stat_vett[5] = max(0, 1 - abs(termo_mean - 36) / 2)  # fuzzification per la temperatura

        # Definizione dei pesi per le diverse misurazioni
        weights = np.array([1.5, 2.0, 2.5, 2.0, 1.5, 1.0])  # Maggiore peso per oxim, bps, ECG, RR

        # Aggregazione pesata delle condizioni
        weighted_aggregated_status = np.dot(stat_vett, weights) / np.sum(weights)

        # Definizione dello stato in base al grado di appartenenza aggregato pesato
        if weighted_aggregated_status >= 0.7:
            status = "good"
        elif weighted_aggregated_status >= 0.4:
            status = "fair"
        else:
            status = "bad"

        return status

    
    def update_service(self):
        # update the service in the catalog
        config = json.dumps(self.conf["information"][0])
        config = requests.put(f"{self.urlRegistrySystem}/service",json=config)
        self.conf["information"][0] = config.json()
        # save the new configuration file 
        json.dump(self.conf, open("PatientStatus_config.json", "w"), indent=4)
        print("Service updated in the catalog")
    
if __name__ == "__main__":
    status = PatientStatus()
    while True:
        status.get_status_and_publish()
        status.update_service()
        time.sleep(300) # ogni 5 minuti calcolo lo status e lo pubblico

