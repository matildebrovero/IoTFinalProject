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
     
                - "pubish_topic": Topic where the status will be published 
 
                - "uri_catalog": URI for REST request to the catalog 
     
                - "uri_DB": URI for REST request to the Database Connector 
     
                - "params_DB": Parameters for REST request of the Database Connector 
     
                - "lastUpdated": Last time the service was updated 
 
""" 

class PatientStatus(object):
    def __init__(self):
        # load the configuration file
        self.conf=json.load(open("PatientStatus_config.json")) 
        ps_conf = copy.deepcopy(self.conf)
        # get the IP address of the registry system
        self.urlRegistrySystem = self.conf["RegistrySystem"] 

        # post the configuration to the catalog
        config = requests.post(f"{self.urlRegistrySystem}{self.conf['information']['uri_catalog']['service']}",json=self.conf["information"])
        # control on the response of the post request
        if config.status_code == 200:
            print("\n\n\nPOST REQUESTS\n")
            print(f"Service Information: {config}")
            ps_conf["information"] = config.json()
            # save the new configuration file 
            json.dump(ps_conf, open("PatientStatus_config.json", "w"), indent=4)
            print("\nService registered to the catalog")
        else:
            print(f"Error: {config.status_code} - {config.text}")
            exit()

        # get the database information from the catalog
        DB = requests.get(f"{self.urlRegistrySystem}{self.conf['information']['uri_catalog']['DB']}")
        # control on the response of the get request
        print("\n\n\nGET REQUESTS for DB and broker information\n")
        if DB.status_code == 200:
            self.Database = DB.json()["urlDB"]
            print(f"\nDatabase Information: {DB}")
        else:
            print(f"Error: {DB.status_code} - {DB.text}")
            exit()

        # get the mqtt information from the catalog 
        b = requests.get(f"{self.urlRegistrySystem}{self.conf['information']['uri_catalog']['broker']}")
        # control on the response of the get request
        if b.status_code == 200:
            print(f"\nBroker Information: {b}")
            self.broker = b.json()
            self.clientID = self.conf["information"]["serviceName"]+str(self.conf["information"]["serviceID"])
            self.status_client = StatusManager(self.clientID, self.broker["IP"],self.broker["port"] )
            # start the mqtt publisher
            print("\n\n\nStarting the mqtt client\n")
            self.status_client.startSim()
        else:
            print(f"Error: {b.status_code} - {b.text}")
            exit()
    


    def get_status_and_publish(self):
        print("\n\n\nSTARTING THE COMPUTATION OF THE STATUS\n")
        print("GETTING PATIENT LIST")
        # get the list of the patients from the catalog
        patientList = requests.get(f"{self.urlRegistrySystem}{self.conf['information']['uri_catalog']['patient']}")
        # control on the response of the get request
        if patientList.status_code != 200:
            print(f"Error in getting patient list: {patientList.status_code} - {patientList.text}")
            exit()
        print(f"\nPatient list: {patientList}")
        print(patientList.json(), pretty_print=True)
        patID = patientList.json()["patientID"]
        #patID = [48] # for testing purposes TODO: remove this line
        condition = patientList.json()["patientCondition"]
        
        for pat in patID:
            print(f"\n\nComputing status for patient {pat}")
            print(f"{self.Database}{self.conf['information']['uri_DB']['gluco']}{pat}?{self.conf['information']['params_DB']}")
            print("\nGET REQUESTS TO DATABASE\n")
            # get the data from the database

            #### GLUCOSE ####
            try:
                response_gluco = requests.get(f"{self.Database}{self.conf['information']['uri_DB']['gluco']}{pat}?{self.conf['information']['params_DB']}")
                print(f"\n\n\nGLUCOMETER\nGet request on: {self.Database}{self.conf['information']['uri_DB']['gluco']}{pat}?{self.conf['information']['params_DB']}") 
                # control on the response of the get request
                if response_gluco.status_code == 200:
                    response_gluco = json.loads(response_gluco.json(), indent=4)
                    print(response_gluco)
                else:
                    print(f"\nError in getting glucose data: {response_gluco.status_code} - {response_gluco.text}")  
                    
            except:
                print("\nError in getting glucose data")
                response_gluco = {"e": {"v": [100]}}

            #### BLOOD PRESSURE ####
            try:
                response_bps = requests.get(f"{self.Database}{self.conf['information']['uri_DB']['bps']}{pat}?{self.conf['information']['params_DB']}")
                print(f"\n\n\nBLOOD PRESSURE\nGet request on: {self.Database}{self.conf['information']['uri_DB']['bps']}{pat}?{self.conf['information']['params_DB']}")
                if response_bps.status_code == 200:  
                    response_bps = json.loads(response_bps.json(), indent=4)
                    print(response_bps)
                else:
                    print(f"\nError in getting blood pressure data {response_bps.status_code} - {response_bps.text}")
                    exit()
            except:
                print("\nError in getting blood pressure data")
                response_bps = {"e": {"v": [200]}}

            #### OXIMETER ####
            try:
                response_oxim = requests.get(f"{self.Database}{self.conf['information']['uri_DB']['oxim']}{pat}?{self.conf['information']['params_DB']}")
                print(f"\n\n\nOXIMETER\nGet request on:{self.Database}{self.conf['information']['uri_DB']['oxim']}{pat}?{self.conf['information']['params_DB']}")
                if response_oxim.status_code == 200:
                    response_oxim = json.loads(response_oxim.json(), indent=4)
                    print(response_oxim)
                else:
                    print(f"\nError in getting oximeter data {response_oxim.status_code} - {response_oxim.text}")
                    exit()
            except:
                print("\nError in getting oximeter data")    
                response_oxim = {"e": {"v": [96]}}

            #### HEART RATE ####
            try:
                response_HR = requests.get(f"{self.Database}{self.conf['information']['uri_DB']['HR']}{pat}?{self.conf['information']['params_DB']}")
                print(f"\n\n\nHEART RATE\nGet request on: {self.Database}{self.conf['information']['uri_DB']['HR']}{pat}?{self.conf['information']['params_DB']}")
                # control on the response of the get request
                if response_HR.status_code == 200:
                    response_HR = json.loads(response_HR.json(), indent=4)
                    print(response_HR)
                else: 
                    print(f"\nError in getting HR data {response_HR.status_code} - {response_HR.text}")
                    exit()
            except:
                print("\nError in getting HR data")    
                response_HR = {"e": {"v": [0]}}

            #### TEMPERATURE ####
            try:
                response_termo = requests.get(f"{self.Database}{self.conf['information']['uri_DB']['temp']}{pat}?{self.conf['information']['params_DB']}")
                print(f"\n\n\nTEMPERATURE\nGet request on: {self.Database}{self.conf['information']['uri_DB']['temp']}{pat}?{self.conf['information']['params_DB']}")
                # control on the response of the get request
                if response_termo.status_code == 200:
                    response_termo = json.loads(response_termo.json(), indent=4)
                    print(response_termo)
                else:
                    print(f"\nError in getting temperature data {response_termo.status_code} - {response_termo.text}") 
                    exit()
            except:
                print("\nError in getting temperature data")
                response_termo = {"e": {"v": [38]}}
            
            #### RR ####
            try:
                response_RR = requests.get(f"{self.Database}{self.conf['information']['uri_DB']['RR']}{pat}?{self.conf['information']['params_DB']}")
                print(f"\n\n\nRR\nGet request on: {self.Database}{self.conf['information']['uri_DB']['RR']}{pat}?{self.conf['information']['params_DB']}")
                # control on the response of the get request
                if response_oxim.status_code == 200:
                    response_RR = json.loads(response_RR.json(), indent=4)
                    print(response_RR)
                else: 
                    print(f"Error in getting RR data {response_RR.status_code} - {response_RR.text}")
                    exit()
            except:    
                response_RR = {"e": {"v": [1000]}}   

            # definition of the data dictionary containing the data of the patient 
            data = {"gluco": response_gluco["e"]["v"], 
                    "bps": response_bps["e"]["v"], 
                    "oxim": response_oxim["e"]["v"], 
                    "HR": response_HR["e"]["v"], 
                    "termo": response_termo["e"]["v"],
                    "RR": response_RR["e"]["v"], 
                    "condition": condition[patID.index(pat)]}
            
            # calculate the status of the patient 
            s = self.calculate_status(data) 

            # definition of the SenML message
            stat = {"bn": "Status", 
                    "e":[  
                        { 
                            "u": "status", 
                            "t": time.time(), 
                            "v": s 
                        }]} 
            
            # publish the status on the mqtt broker 
            topic = self.broker["main_topic"]+self.conf["information"]["pubish_topic"]["base_topic"]+str(pat)+self.conf["information"]["pubish_topic"]["status"] 
            print(f"\n\n\nPUBLISHING STATUS\nTOPIC: {topic}\nMESSAGE: {stat}")
            self.status_client.publish(topic, stat)  
 
    def calculate_status(self, data): 
        # compute of the mean value of the parameters 
        gluco_mean = np.mean(data["gluco"]) 
        bps_mean = np.mean(data["bps"]) 
        oxim_mean = np.mean(data["oxim"]) 
        HR_mean = np.mean(data["HR"])   
        RR = data["RR"] 

        # count the number of RR values that are too high or too low 
        RR_count = 0 
        for i in range(len(RR)): 
            if RR[i] < 0.85 or RR[i] > 0.95:    
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
        #### Glucose ####
        if "d" in condition: 
            stat_vett[0] = max(0, 1 - (gluco_mean - 70) / 130)   
        else: 
            stat_vett[0] = max(0, 1 - abs(gluco_mean - 105) / 35) 
 
        #### Blood Pressure ####
        if condition == "n" or "c" in condition: 
            stat_vett[1] = max(0, (bps_mean - 100) / 40)  
        else: 
            stat_vett[1] = max(0, (bps_mean - 120) / 50) 

        #### Oximeter ####
        stat_vett[2] = max(0, (98 - oxim_mean) / 10)   

        #### Heart Rate ####
        stat_vett[3] = max(0, (HR_mean - 80) / 20)   
 
        #### RR ####
        stat_vett[4] = max(0, 1 - abs(RR_count / 20))   
 
        #### Temperature ####
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
        print("\n\n\n\PUT REQUEST\n")
        ps_conf = copy.deepcopy(self.conf) 
        config = requests.put(f"{self.urlRegistrySystem}{self.conf['information']['uri_catalog']['service']}",json=self.conf["information"]) 
        # control on the response of the put request
        if config.status_code == 200:
            print(f"Update Service Information: {config}")
            ps_conf["information"] = config.json()
            # save the new configuration file 
            json.dump(ps_conf, open("PatientStatus_config.json", "w"), indent=4)
            print("Service updated in the catalog") 
        else:
            print(f"Error: {config.status_code} - {config.text}")
            exit()
    
if __name__ == "__main__": 
    status = PatientStatus() 
    while True: 
        status.get_status_and_publish() 
        status.update_service() 
        # every 5 minutes the status is calculated and published for every patient 
        time.sleep(300)  
 