import json 
import requests 
from StatusPublisher import * 
import time 
import numpy as np 
import copy 
""" PatientStatus -  SmartHospital IoT platform. Version 1.0.1 
    This microservice is responsible for analyzing the data of the patients and publishing the results to the Database Connector. 
    The results are published according to the SenML format. 
 
    Input:  
        - Data from the Database Connector: 
            - Glucose 
            - Blood Pressure 
            - Oximeter 
            - ECG 
            - Temperature 
            - Respiration Rate 
     
    Output: 
        - Status of the patient 
     
    -------------------------------------------------------------------------- 
    --------------         standard configuration          ------------------- 
    -------------------------------------------------------------------------- 
 
    Standard Configuration file provided: PatientStatus_config.json 
    The parameters of the configuration file are: 
     
            - "RegistrySystem": URL of the Registry System 
            - "information":  
                - "serviceName": Name of the service 
     
                - "serviceID": ID of the service, automatically assigned by the Registry System 
 
                - "serviceType": supported services (REST, MQTT)  
     
                - "uri_catalog": URI of the catalog 
 
                - "pubish_topic": Topic where the status will be published 
 
                - "uri_catalog": URI for REST request to the catalog 
     
                - "uri_DB": URI for REST request to the Database Connector 
     
                - "params_DB": Parameters for REST request of the Database Connector 
     
                - "lastUpdated": Last time the service was updated 
 
""" 
 
class PatientStatus(object): 
    def __init__(self): 
        # load the configuration file 
        ps_conf=json.load(open("PatientStatus_config.json"))  
        # get the IP address of the registry system 
        self.urlRegistrySystem = ps_conf["RegistrySystem"]  
        # register the service to the catalog 
        config = json.dumps(ps_conf["information"]) 
        # post the configuration to the catalog 
        config = requests.post(f"{self.urlRegistrySystem}{ps_conf["information"]["uri_catalog"]["service"]}",json=config) 
        ps_conf["information"] = config.json() 
        # save the new configuration file  
        json.dump(ps_conf, open("PatientStatus_config.json", "w"), indent=4) 
        self.conf = ps_conf 
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
            # get the data from the database 
            response_gluco = requests.get(f"{self.Database}{self.conf["information"]["uri_DB"]["gluco"]}{pat}?{self.conf["information"]["params_DB"]}{range}")   
            response_bps = requests.get(f"{self.Database}{self.conf["information"]["uri_DB"]["bps"]}{pat}?{self.conf["information"]["params_DB"]}{range}") 
            response_oxim = requests.get(f"{self.Database}{self.conf["information"]["uri_DB"]["oxim"]}{pat}?{self.conf["information"]["params_DB"]}{range}") 
            response_ECG = requests.get(f"{self.Database}{self.conf["information"]["uri_DB"]["ecg"]}{pat}?{self.conf["information"]["params_DB"]}{range}") 
            response_termo = requests.get(f"{self.Database}{self.conf["information"]["uri_DB"]["temp"]}{pat}?{self.conf["information"]["params_DB"]}{range}") 
            response_RR = requests.get(f"{self.Database}{self.conf["information"]["uri_DB"]["RR"]}{pat}?{self.conf["information"]["params_DB"]}{range}") 
            
            # definition of the data dictionary containing the data of the patient  
            data = {"gluco": response_gluco.json()["e"][0]["v"],  
                    "bps": response_bps.json()["e"][0]["v"],  
                    "oxim": response_oxim.json()["e"][0]["v"],  
                    "ECG": response_ECG.json()["e"][0]["v"],  
                    "termo": response_termo.json()["e"][0]["v"], 
                    "RR": response_RR.json()["e"][0]["v"],  
                    "condition": condition[patID.index(pat)]} 
             
            s = self.calculate_status(data) 
 
            stat = {"bn": "Status", 
                    "e":[  
                        { 
                            "u": "status", 
                            "t": time.time(), 
                            "v": s 
                        }]} 
            topic = self.broker["main_topic"]+self.conf["information"]["pubish_topic"]["base_topic"]+str(pat)+self.conf["information"]["pubish_topic"]["status"] 
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
        ps_conf = copy.deepcopy(self.conf) 
        ps_conf["information"] = config.json() 
        # save the new configuration file  
        json.dump(ps_conf, open("PatientStatus_config.json", "w"), indent=4) 
        print("Service updated in the catalog") 
     
if __name__ == "__main__": 
    status = PatientStatus() 
    while True: 
        status.get_status_and_publish() 
        status.update_service() 
        # every 5 minutes the status is calculated and published for every patient 
        time.sleep(300)  
 


