import cherrypy
import json
from datetime import datetime, timedelta

class RegistrySystem(object):
    exposed=True 
    
    def __init__(self):
        # We said that we want __init__ to be called when the object is created
        # Initialize the configuration for the web page
        self.catalog = json.load(open("catalog.json"))
        self.configWebPage = {
            "patientsID": [],
            "data": [],
            "deviceConnectors":[]
            }

    def GET(self,*uri,**params):
        # uri is with * and params is with **
        # "http://localhost:8080/broker"
        if uri[0]=="broker":
            # Return the broker information
            print("Received GET request for broker info.")
            response = self.catalog["broker"]
            return json.dumps(response, indent = 4)

        # "http://localhost:8080/DBadaptor"
        if uri[0]=="DBadaptor":
            for s in self.catalog["serviceList"]:
                if s["serviceName"] == "DB_reader":
                    return json.dumps({"urlDB" : "http://"+s["serviceHost"]+":"+str(s["servicePort"])})
        
        # "http://localhost:8080/configwebpage"
        if uri[0] == "configwebpage":  
            print("Received GET request for configwebpage.")
            pIDs = []
            dConnectors = []
            for patient in self.catalog["patientsList"]:
                pIDs.append(patient["patientID"])
            self.configWebPage["patientsID"] = pIDs
            print("\n\n\n")
            print(pIDs)
            for dC in self.catalog["deviceConnectorList"]:
                if dC["patientLinked"] == "no":
                    dConnectors.append("device" + str(dC["deviceConnectorID"]))
            self.configWebPage["deviceConnectors"] = dConnectors
            self.configWebPage["data"] = self.catalog["dataList"]
            return json.dumps(self.configWebPage, indent = 4)
        
        # "http://localhost:8080/patientInfo"
        if uri[0] == "patientInfo":  # TODO debug it
            if uri[1] == "All":
                print("Received GET request for all patient info.")
                pIDs = []
                pStatus = []
                for p in self.catalog["patientsList"]:
                    pIDs.append(p["patientID"])
                    pStatus.append(p["conditions"])
                return json.dumps({"patientID": pIDs, "patientCondition": pStatus}, indent = 4)
            if params:  # Perform only if there are parameters
                print(f"Received GET request for patient info with params: {params}")
                for p in self.catalog["patientsList"]:
                    if p["patientID"] == params["patientID"]:
                        return json.dumps(p, indent = 4)
                print(f"Patient {params['patientID']} not found")

        # "http://localhost:8080/NurseInfo"
        if uri[0] == "NurseInfo":
            if uri[1] == "all":
                print("Received GET request for all nurse info.")
                response = self.catalog["nursesList"]
                return json.dumps(response, indent = 4)
            
        # "http://localhost:8080/availableData"
        if uri[0] == "availableData":
            print("\n\n\n")
            print("Received GET request for available data.")
            response = self.catalog["dataList"]
            print(response)
            return json.dumps(response, indent = 4)

    def POST(self,*uri,**params):
        rawBody = cherrypy.request.body.read()
        print("Received POST request with body:", rawBody)
        if len(rawBody) > 0:
            try:
                body = json.loads(rawBody)
            except json.decoder.JSONDecodeError:
                raise cherrypy.HTTPError(400,"Bad Request. Body must be a valid JSON")
            except:
                raise cherrypy.HTTPError(500,"Internal Server Error")
            
            # "http://localhost:8080/service"
            if uri[0]=="service":
                print("Received POST request for service.")
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
            if uri[0] == "DeviceConnector":
                print("Received POST request for DeviceConnector.")
                ID = self.catalog["counter"]["deviceConnectorCounter"]
                self.catalog["counter"]["deviceConnectorCounter"] += 1
                body["deviceConnectorID"] = ID
                body["lastUpdate"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                self.catalog["deviceConnectorList"].append(body)
                with open("catalog.json", "w") as file:
                    json.dump(self.catalog, file, indent = 4)
                    print("Catalog updated with Device connector:", body)
                print("Catalog updated with Device connector:", body)
                return json.dumps(body, indent = 4)

            # "http://localhost:8080/patient"
            if uri[0] == "patient":
                print("Received POST request for patient.")
                body["patientID"] = int(body["deviceConnector"].split("e")[2])
                self.catalog["patientsList"].append(body)
                # Now the device connector is linked to a patient
                for dC in self.catalog["deviceConnectorList"]:
                    if dC["deviceConnectorID"] == int(body["deviceConnector"].split("e")[2]):
                        dC["patientLinked"] = "yes"
                        print(dC)
                print("\n\n\n")
                print(self.catalog["patientsList"])
                print("\n\n\n")
                print(body)
                print("\n\n\n")

                with open("catalog.json", "w") as file:
                    json.dump(self.catalog, file, indent = 4)
                print("Catalog updated with patient:", body)
                return json.dumps(body, indent = 4)
            
            # "http://localhost:8080/nurse"
            if uri[0] == "nurse":
                print("Received POST request for nurse.")
                #ID = self.catalog["counter"]["nurseCounter"]
                #body["nurseID"] = ID
                #self.catalog["nurseList"].append(body)
                # Assign every patient present in the lists to the nurse currently logged in the BOT so it can receive the alerts
                patients = []
                for p in self.catalog["patientsList"]:
                    patients.append(str(p["patientID"]))
                body["patients"] = patients
                for nurse in self.catalog["nursesList"]:
                    if nurse["nurseID"] == body["nurseID"]:
                        nurse["patients"] = body["patients"]
                        nurse["chatID"] = body["chatID"]
                with open("catalog.json", "w") as file:
                    json.dump(self.catalog, file, indent = 4)
                print("Catalog updated with nurse:", body)
                return json.dumps(body, indent = 4)                
        else:
            return "Empty body"
           
    def PUT(self,*uri,**params): 
        rawBody = cherrypy.request.body.read()
        print("Received PUT request with body:", rawBody)
        if len(rawBody) > 0:
            try:
                body = json.loads(rawBody)
            except json.decoder.JSONDecodeError:
                raise cherrypy.HTTPError(400,"Bad Request. Body must be a valid JSON")
            except:
                raise cherrypy.HTTPError(500,"Internal Server Error")
            
            #"http://localhost:8080/service"
            if uri[0]=="service":
                # Debugging statement to ensure entering service condition
                print("Inside Service Condition")
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
            if uri[0] == "DeviceConnector":
                # Debugging statement to ensure entering devconn condition
                print("Inside DeviceConnector Condition")
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
        else:
            return "Empty body"
        
    def DELETE(self,*uri,**params): #TODO debug it
        print(f"Received DELETE request with uri {uri} and params:{params}")
        print("\n\n\n")
        print("PARAMSSSSSSS")
        print(params["patientID"])
        print("\n\n\n")
        if uri[0] == "patient":
            print("Received DELETE request for patient.")
            for patient in self.catalog["patientsList"]:
                print("\n\n\n")
                print(patient)
                if patient["patientID"] == params["patientID"]:
                    # delete patient from the list
                    self.catalog["patientsList"].remove(patient)
                    print("\n\n\n")
                    print(self.catalog["patientsList"])
                    print("\n\n\n")
                    with open("catalog.json", "w") as file:
                        json.dump(self.catalog, file, indent = 4)
                    print("Catalog updated without patient:", patient)
                else:
                    return "Patient not found"
            for dc in self.catalog["deviceConnectorList"]:
                if dc["deviceConnectorID"] == params["patientID"]:
                    self.catalog["deviceConnectorList"].remove(dc)
                    print("\n\n\n")
                    print(self.catalog["deviceConnectorList"])
                    print("\n\n\n")
                    with open("catalog.json", "w") as file:
                        json.dump(self.catalog, file, indent = 4)
                    print("Catalog updated with Device connector:", dc)
        pass

    def checkLastUpdate(self, lastUpdate): #TODO debug it
        currentTimestr = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        #convert the string to datetime
        currentTime = datetime.strptime(currentTimestr, "%Y-%m-%dT%H:%M:%S")
        lastUpdateobj = datetime.strptime(lastUpdate, "%Y-%m-%dT%H:%M:%S")
        #check if the last update was more than 5 minutes ago
        print(f"Current time: {currentTime}")
        timeDiff = currentTime - lastUpdateobj
        print(f"Time difference: {timeDiff.total_seconds()}")
        if timeDiff > timedelta(minutes=5) or timeDiff.total_seconds() < 0:
            print("True")
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
    cherrypy.config.update({'server.socket_port': 8081})
    cherrypy.config.update({'server.socket_host':'0.0.0.0'})
    cherrypy.engine.start()


    print("Server started")

    # Alternativa di chat
    while True:
        print("Main loop")
        # Create a new list with services that need to be deleted
        services_to_delete = [service for service in catalog.get("serviceList", []) if App.checkLastUpdate(service.get("lastUpdate"))]
        
        # Remove the services from the catalog
        for service in services_to_delete:
            ID = service["serviceID"]
            print(f"Service {ID} is going to be deleted")
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

    # while True: #TODO debug it
    #     #print("Main loop")
    #     # Iterate over serviceList
    #     for service in catalog.get("serviceList", []):
    #         toDelete = App.checkLastUpdate(service.get("lastUpdate"))
    #         if toDelete:
    #             ID = service["serviceID"]
    #             #print(f"Service {ID} is going to be deleted")
    #             catalog["serviceList"].remove(service)
    #     # Iterate over deviceConnectorList
    #     for deviceConnector in catalog.get("deviceConnectorList", []):
    #         toDelete = App.checkLastUpdate(deviceConnector.get("lastUpdate"))
    #         if toDelete:
    #             ID = deviceConnector["deviceConnectorID"]
    #             #print(f"DeviceConnector {ID} is going to be deleted")
    #             catalog["deviceConnectorList"].remove(deviceConnector)
    #    with open("catalog.json", "w") as file:
    #    json.dump(catalog, file, indent = 4)
