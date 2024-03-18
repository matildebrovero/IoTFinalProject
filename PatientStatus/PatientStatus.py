# pip install numpy
# pip install fuzzylogic

import json
import requests
from StatusPublisher import *
import time
import numpy as np
import copy

# TODO mettere aggiornamento automatico del 'ci sono esisto' nel catalogo

class PatientStatus(object):
    def __init__(self):
        # load the configuration file
        self.conf=json.load(open("PatientStatus_config.json")) 
        ps_conf = copy.deepcopy(self.conf)
        self.urlRegistrySystem = self.conf["RegistrySystem"] # get the IP address of the registry system
        # register the service to the catalog
        config = json.dumps(self.conf["information"][0])
        # post the configuration to the catalog
        config = requests.post(f"{self.urlRegistrySystem}/service",data=config)
        ps_conf["information"][0] = config.json()
        # save the new configuration file 
        json.dump(ps_conf, open("PatientStatus_config.json", "w"), indent=4)
        print("Service registered to the catalog")
        
        response = requests.get(f"{self.urlRegistrySystem}/catalog") # get the catalog
        self.Catalog = response.json()
        # print(f"Service ID: {self.conf['information']['serviceID']}")
        # get the database information (IP perchè devo fare delle rest request sempre) from the catalog
        DB = requests.get(f"{self.urlRegistrySystem}/DBadapter")
        self.Database = DB.json()["urlDB"]
        # get the mqtt information from the catalog
        self.broker = self.Catalog["broker"]
        self.clientID = self.conf["information"][0]["serviceName"]+str(self.conf["information"][0]["serviceID"])
        self.status_client = StatusManager(self.clientID, self.broker["IP"],self.broker["port"] )
        # start the mqtt publisher
        self.status_client.startSim()

    def get_status_and_publish(self):
        # ipotizzo di dover calcolare lo status di tutti i pazienti
        # quindi devo ottenere la lista di tutti i pazienti
        # è giusto che la prenda dal catalog? secondo me si
        devID = []
        patID = []
        condition = []
        for p in self.Catalog["patientsList"]:
            patID.append(p["patientID"])
            condition.append(p["patientcondition"])
            devID.append(p["deviceConnectorID"])
        
        for pat in patID:
            range = 300
            response_gluco = requests.get(f"{self.Database}/glucometer/patient{pat}?range={range}")  
            response_bps = requests.get(f"{self.Database}/blood_pressure/patient{pat}?range={range}")
            response_oxim = requests.get(f"{self.Database}/oximeter/patient{pat}?range={range}")
            response_ECG = requests.get(f"{self.Database}/ECG/patient{pat}?range={range}")
            response_termo = requests.get(f"{self.Database}/temperature/patient{pat}?range={range}")
            data = {"gluco": response_gluco.json()["measure"], "bps": response_bps.json()["measure"], "oxim": response_oxim.json()["measure"], "ECG": response_ECG.json()["measure"], "termo": response_termo.json()["measure"], "condition": condition[patID.index(pat)]}
            s = self.calculate_status(data)
            s = "good" # da togliere
            stat = {"patientID": pat, "status": s, "timestamp": time.time()}
            topic = self.broker["main_topic"]+"patient"+str(pat)+self.conf["information"][0]["pubish_topic"]
            self.status_client.publish(topic, stat) 

    def calculate_status(self, data):
        gluco_mean = np.mean(data["gluco"])
        bps_mean = np.mean(data["bps"])
        oxim_mean = np.mean(data["oxim"])
        ECG_mean = np.mean(data["ECG"]) #per ECG
        RR = data["RR"] 
        RR_count = 0
        for i in range(len(RR)):
            if RR[i] < 20 or RR[i] > 100: #TODO mettere la soglia giusta
                RR_count =+1
        
        termo_mean = np.mean(data["termo"])
        condition = data["condition"]
        condition = "n"

        #vector of status each posizion represent a measure,
        # 0 -> gluco
        # 1 -> bps
        # 2 -> oxim
        # 3 -> ECG
        # 4 -> RR
        # 5 -> termo
        # the value is the condition,
        # 0 -> good
        # 1 -> bad

        # possiamo implementare le categorie di pazienti
        # n = no patologies
        # d = diabetic 
        # h = hypertention
        # c = cardiatic desease

        stat_vett = np.array([0, 0, 0, 0, 0]) 
        # Rules
        if condition == "d":
            if gluco_mean < 70 or gluco_mean > 200:
                stat_vett[0] = 1
        else:
            if gluco_mean < 70 or gluco_mean > 140:
                stat_vett[0] = 1

        if condition == "n" or condition == "c":
            if bps_mean > 100:
                stat_vett[1] = 1
        else:
            if bps_mean > 140:
                stat_vett[1] = 1

        if oxim_mean < 97: # in percentuale
            stat_vett[2] = 1
        
        if ECG_mean > 100: #TODO mettere la soglia giusta e capire se cambia per le patologie
            stat_vett[3] = 1

        if RR_count > 2:
            stat_vett[4] = 1
        
        if termo_mean < 35 or termo_mean > 37:
            stat_vett[5] = 1
        
        status = "good"

        # se ho i battiti alti o se ho l'ossigeno basso o entrambi sono bad oppure se più di due condizioni superano il limite.
        if stat_vett[0] == 1 or stat_vett[2] == 1 or  np.sum(stat_vett) > 3:  
            status = "bad"

        return status
    

    
if __name__ == "__main__":
    status = PatientStatus()
    while True:
        status.get_status_and_publish()
        time.sleep(300) # ogni 5 minuti calcolo lo status e lo pubblico

