import cherrypy
import json
from datetime import datetime, timedelta
import time

""" 
    RegistrySystem - SmartHospital IoT platform. Version 1.0.1 
    This microservice exposes REST API to read and write information about the services, patients, nurses, and device connectors in the Smart Hospital.
    It keeps track of them and provides the information to the other services when requested.
    It is also responsible for deleting the services and device connectors that have not been updated for more than 5 minutes.

    All the information is stored in a JSON file called catalog.json. 

    --------------------------------------------------------------------------
    
        Input:
            - GET requests from the services that want to read the information about the services, patients, nurses, and device connectors
            - POST requests from the services that want to add a new service, patient, nurse, or device connector
            - PUT requests from the services that want to update the information about the services, patients, nurses, or device connectors
            - DELETE requests from the services that want to delete a patient or device connector

        Output:  
            - Information about the services, patients, nurses, and device connectors in the Smart Hospital
            - Confirmation of the addition, update, or deletion of a service, patient, nurse, or device connector

    -------------------------------------------------------------------------- 
    --------------         standard configuration          ------------------- 
    -------------------------------------------------------------------------- 
 
    Its configuration file is integrated in the the catalog.json
 
""" 

class RegistrySystem(object):
    exposed=True 
    
    def __init__(self):
        # We said that we want __init__ to be called when the object is created
        # Initialize the configuration for the web page
        self.catalog = json.load(open("catalog.json"))
        self.configWebPage = {
            "patientsID": [],
            "nurseID": [],
            "data": [],
            "deviceConnectors":[]
            }

    def GET(self,*uri,**params):
        # uri is with * and params is with **
        if len(uri) > 0:
            # "http://localhost:8080/broker"
            if uri[0]=="broker":
                # Return the broker information
                print("\nReceived GET request for broker info.")
                response = self.catalog["broker"]
                return json.dumps(response, indent = 4)

            # "http://localhost:8080/DBadaptor"
            elif uri[0]=="DBadaptor":
                print("\nReceived GET request for DB adaptor (DB reader) info.")
                for s in self.catalog["serviceList"]:
                    if s["serviceName"] == "DB_reader":
                        return json.dumps({"urlDB" : "http://"+s["serviceHost_docker"]+":"+str(s["servicePort"])})
            
            # "http://localhost:8080/configwebpage"
            elif uri[0] == "configwebpage":  
                print("\nReceived GET request for configwebpage.")
                pIDs = []
                dConnectors = []
                nIDs = []
                for patient in self.catalog["patientsList"]:
                    pIDs.append(patient["patientID"])

                for dC in self.catalog["deviceConnectorList"]:
                    if dC["patientLinked"] == "no":
                        dConnectors.append("device" + str(dC["deviceConnectorID"]))

                for n in self.catalog["nursesList"]:   #aggiunto questo
                    nIDs.append(n["nurseID"])

                self.configWebPage["patientsID"] = pIDs
                self.configWebPage["nurseID"] = nIDs
                self.configWebPage["deviceConnectors"] = dConnectors
                self.configWebPage["data"] = self.catalog["dataList"]
                return json.dumps(self.configWebPage, indent = 4)
            
            # "http://localhost:8080/patientInfo"
            elif uri[0] == "patientInfo":  
                if len(uri) == 2:
                    # "http://localhost:8080/patientInfo/All"
                    if uri[1] == "All":
                        print("\nReceived GET request for all patient info.")
                        pIDs = []
                        pStatus = []
                        for p in self.catalog["patientsList"]:
                            pIDs.append(p["patientID"])
                            pStatus.append(p["conditions"])
                        return json.dumps({"patientID": pIDs, "patientCondition": pStatus}, indent = 4)
                else:
                    # "http://localhost:8080/patientInfo?patientID=N"
                    if len(params) != 0:  # Perform only if there are parameters
                        print(f"\nReceived GET request for patient info with params: {params}")
                        for p in self.catalog["patientsList"]:
                            if p["patientID"] == int(params["patientID"]):
                                return json.dumps(p, indent = 4)

            # "http://localhost:8080/NurseInfo"
            elif uri[0] == "NurseInfo":
                if uri[1] == "all":
                    print("\nReceived GET request for all nurse info.")
                    response = self.catalog["nursesList"]
                    return json.dumps(response, indent = 4)
                
            # "http://localhost:8080/availableData"
            elif uri[0] == "availableData":
                print("\nReceived GET request for available data.")
                response = self.catalog["dataList"]
                print(response)
                return json.dumps(response, indent = 4)

            else:
                raise cherrypy.HTTPError(404, "Page doesn't exist")
        else:
            raise cherrypy.HTTPError(400, "You have to insert a uri")

    def POST(self,*uri,**params):
        rawBody = cherrypy.request.body.read()
        print("\nReceived POST request with body:", rawBody)
        if len(rawBody) > 0:
            try:
                body = json.loads(rawBody)
            except json.decoder.JSONDecodeError:
                raise cherrypy.HTTPError(400,"Bad Request. Body must be a valid JSON")
            except:
                raise cherrypy.HTTPError(500,"Internal Server Error")
            
            if len(uri) > 0:
                # "http://localhost:8080/service"
                if uri[0]=="service":
                    print("\nReceived POST request for service.")
                    ID = self.catalog["counter"]["serviceCounter"]
                    self.catalog["counter"]["serviceCounter"] += 1
                    body["serviceID"] = ID
                    body["lastUpdate"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    self.catalog["serviceList"].append(body)
                    with open("catalog.json", "w") as file:
                        json.dump(self.catalog, file, indent = 4)
                    print("Catalog updated with service:", body)
                    return json.dumps(body, indent = 4)
                
                # "http://localhost:8080/DeviceConnector"
                elif uri[0] == "DeviceConnector":
                    print("\nReceived POST request for DeviceConnector.")
                    ID = self.catalog["counter"]["deviceConnectorCounter"]
                    self.catalog["counter"]["deviceConnectorCounter"] += 1
                    body["deviceConnectorID"] = ID
                    body["lastUpdate"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    self.catalog["deviceConnectorList"].append(body)
                    with open("catalog.json", "w") as file:
                        json.dump(self.catalog, file, indent = 4)
                    print("Catalog updated with Device connector:", body)
                    return json.dumps(body, indent = 4)

                # "http://localhost:8080/patient"
                elif uri[0] == "patient":
                    print("\nReceived POST request for patient.")
                    body["patientID"] = int(body["deviceConnector"].split("e")[2])
                    self.catalog["patientsList"].append(body)
                    # Now the device connector is linked to a patient
                    for dC in self.catalog["deviceConnectorList"]:
                        if dC["deviceConnectorID"] == int(body["deviceConnector"].split("e")[2]):
                            dC["patientLinked"] = "yes"
                            print(dC)
                    body["deviceConnector"] = int(body["deviceConnector"].split("e")[2])
                    
                    print("\n\n\n")
                    print(self.catalog["patientsList"])
                    print("\n\n\n")
                    print(body)
                    print("\n\n\n")
                    with open("catalog.json", "w") as file:
                        json.dump(self.catalog, file, indent = 4)
                    print("Catalog updated with patient:", body)
                    return json.dumps(body, indent = 4)
                
                # "http://localhost:8080/addNurse"    
                elif uri[0] == "addNurse":
                    print("\nReceived POST request for nurse.")
                    ID = self.catalog["counter"]["nurseCounter"]
                    self.catalog["counter"]["nurseCounter"] += 1
                    body["nurseID"] = ID
                    self.catalog["nursesList"].append(body)
                    with open("catalog.json", "w") as file:
                        json.dump(self.catalog, file, indent = 4)
                    print("Catalog updated with nurse:", body)
                    return json.dumps(body, indent = 4)
                else:
                    raise cherrypy.HTTPError(404, "Page doesn't exist") 
            else:
                raise cherrypy.HTTPError(400, "You have to insert a command as uri")      
        else:
            return "Empty body"
           
    def PUT(self,*uri,**params): 
        rawBody = cherrypy.request.body.read()
        print("\nReceived PUT request with body:", rawBody)
        if len(rawBody) > 0:
            try:
                body = json.loads(rawBody)
            except json.decoder.JSONDecodeError:
                raise cherrypy.HTTPError(400,"Bad Request. Body must be a valid JSON")
            except:
                raise cherrypy.HTTPError(500,"Internal Server Error")
            
            if len(uri) > 0:
                #"http://localhost:8080/service"
                if uri[0]=="service":
                    print("\nReceived PUT request for service.")
                    #retrieve the unique ID from the request
                    ID = body["serviceID"]
                    print("ID:", ID)
                    for service in self.catalog["serviceList"]:
                        if service["serviceID"] == ID:
                            service["lastUpdate"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            with open("catalog.json", "w") as file:
                                json.dump(self.catalog, file, indent = 4)
                                body = service
                            print("Catalog updated with service:",body)
                            return json.dumps(body, indent = 4)
                    return "Service not found"
                
                #"http://localhost:8080/DeviceConnector"
                elif uri[0] == "DeviceConnector":
                    # Debugging statement to ensure entering devconn condition
                    #print("Inside DeviceConnector Condition")
                    print("\nReceived PUT request for DeviceConnector.")
                    #retrieve the unique ID from the catalog
                    ID = body["deviceConnectorID"]
                    print("ID:", ID)
                    for deviceConnector in self.catalog["deviceConnectorList"]:
                        if deviceConnector["deviceConnectorID"] == ID:
                            deviceConnector["lastUpdate"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            with open("catalog.json", "w") as file:
                                json.dump(self.catalog, file, indent = 4)
                                body = deviceConnector
                            print("Catalog updated with Device connector:", body)
                            return json.dumps(body, indent = 4)
                    return "DeviceConnector not found"
                
                #"http://localhost:8080/nurse"
                elif uri[0] == "nurse":
                    if len(uri) == 1:
                        print("\nReceived PUT request for nurse.")
                        # Assign every patient present in the lists if there is no patient assigned yet
                        if body["patients"] == []:
                            patients = []
                            for p in self.catalog["patientsList"]:
                                patients.append(str(p["patientID"]))
                            body["patients"] = patients
                            for nurse in self.catalog["nursesList"]:
                                if nurse["nurseID"] == int(body["nurseID"]):
                                    nurse["patients"] = body["patients"]
                                    nurse["chatID"] = body["chatID"]
                            with open("catalog.json", "w") as file:
                                json.dump(self.catalog, file, indent = 4)
                            print("Catalog updated with nurse:", body)
                            return json.dumps(body, indent = 4)
                        else:
                            print("Nurse already assigned to patients") 
                            for nurse in self.catalog["nursesList"]:
                                if nurse["nurseID"] == int(body["nurseID"]):
                                    nurse["chatID"] = body["chatID"]
                            with open("catalog.json", "w") as file:
                                json.dump(self.catalog, file, indent = 4)
                            print("Catalog updated with nurse:", body)
                    elif len(uri) == 2:
                        #"http://localhost:8080/nurse/modifypatient"
                        if uri[1] == "modifypatient":
                            print("\nReceived PUT request for nurse to modify patient.")
                            for nurse in self.catalog["nursesList"]:
                                if nurse["nurseID"] == int(body["nurseID"]):
                                    nurse["patients"] = body["patients"]
                            with open("catalog.json", "w") as file:
                                json.dump(self.catalog, file, indent = 4)
                            print("Catalog updated with nurse:", body)
                            return json.dumps(body, indent = 4)
                        else:
                            raise cherrypy.HTTPError(404, "Page doesn't exist") 
                else:
                    raise cherrypy.HTTPError(404, "Page doesn't exist") 
            else:
                raise cherrypy.HTTPError(400, "You have to insert a command as uri")
        else:
            return "Empty body"
        
    def DELETE(self,*uri,**params):
        print(f"\nReceived DELETE request with uri {uri} and params:{params}")
        if len(uri) > 0:
            if uri[0] == "patient":
                print("Received DELETE request for patient.")
                for patient in self.catalog["patientsList"]:
                    print("\n\n\n")
                    print(patient)
                    if patient["patientID"] == int(params["patientID"]):
                        # delete patient from the list
                        self.catalog["patientsList"].remove(patient)
                        print("\n\n\n")
                        print(self.catalog["patientsList"])
                        with open("catalog.json", "w") as file:
                            json.dump(self.catalog, file, indent = 4)
                        print("Catalog updated without patient:", patient)
                   
                for dc in self.catalog["deviceConnectorList"]:
                    if dc["deviceConnectorID"] == int(params["patientID"]):
                        self.catalog["deviceConnectorList"].remove(dc)
                        print("\n\n\n")
                        print(self.catalog["deviceConnectorList"])
                        with open("catalog.json", "w") as file:
                            json.dump(self.catalog, file, indent = 4)
                        print("Catalog updated without Device connector:", dc)
            if uri[0] == "nurse":   #aggiunto questo
                print("Received DELETE request for nurse.")
                for nurse in self.catalog["nursesList"]:
                    print(int(params["nurseID"]))
                    print(nurse["nurseID"])
                    if nurse["nurseID"] == int(params["nurseID"]):
                        # delete nurse from the list
                        self.catalog["nursesList"].remove(nurse)
                        with open("catalog.json", "w") as file:
                            json.dump(self.catalog, file, indent = 4)
                        print("Catalog updated without nurse:", nurse)
                    
            else:
                raise cherrypy.HTTPError(404, "Page doesn't exist") 
        else:
            raise cherrypy.HTTPError(400, "You have to insert a command as uri")
        pass

    def checkLastUpdate(self, lastUpdate):
        currentTimestr = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        #convert the string to datetime
        currentTime = datetime.strptime(currentTimestr, "%Y-%m-%dT%H:%M:%S")
        lastUpdateobj = datetime.strptime(lastUpdate, "%Y-%m-%dT%H:%M:%S")
        #check if the last update was more than 6 minutes ago
        timeDiff = currentTime - lastUpdateobj
        if timeDiff > timedelta(minutes=6) or timeDiff.total_seconds() < 0:
            return True
        return False
    
if __name__=="__main__":

    App = RegistrySystem()
    catalog = App.catalog
    print("Catalog loaded")

    config = json.load(open("catalog.json"))

    #Standard configuration to serve the url "localhost:8080"
    conf={
        '/':{
        'request.dispatch':cherrypy.dispatch.MethodDispatcher(), 
        # this line must be here
        'tools.sessions.on':True
        }
    }
    cherrypy.tree.mount(RegistrySystem(),'/',conf) 
    cherrypy.config.update({'server.socket_port': config["RegistrySysteminfo"]["port"]})
    cherrypy.config.update({'server.socket_host': config["RegistrySysteminfo"]["host"]})
    cherrypy.engine.start()

    print("Server started")


    while True:
        print("\nMain loop to check if any service was down for more than 5 min")
        catalog = json.load(open("catalog.json"))

        # Create a new list with services that need to be deleted
        services_to_delete = [service for service in catalog.get("serviceList", []) if App.checkLastUpdate(service.get("lastUpdate"))]
        
        # Remove the services from the catalog
        for service in services_to_delete:
            ID = service["serviceID"]
            name = service["serviceName"]
            print(f"Service {ID} {name} is going to be deleted")
            catalog["serviceList"].remove(service)

        # Create a new list with device connectors that need to be deleted
        connectors_to_delete = [connector for connector in catalog.get("deviceConnectorList", []) if App.checkLastUpdate(connector.get("lastUpdate"))]
        
        # Remove the device connectors from the catalog
        for connector in connectors_to_delete:
            ID = connector["deviceConnectorID"]
            print(f"DeviceConnector {ID} is going to be deleted")
            catalog["deviceConnectorList"].remove(connector)

        # Write the updated catalog to the file
        with open("catalog.json", "w") as file:
            json.dump(catalog, file, indent=4)
        
        # Sleep for 1 minute
        time.sleep(60)


