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
                if s["serviceName"] == "DB_adaptor":
                    return json.dumps({"urlDB" : "http://"+s["serviceHost"]+":"+str(s["servicePort"])})
        
        # "http://localhost:8080/configwebpage"
        if uri[0] == "configwebpage":  
            print("Received GET request for configwebpage.")
            pIDs = []
            dConnectors = []
            for patient in self.catalog["patientsList"]:
                pIDs.append("patient"+ str(patient["patientID"]))
                self.configWebPage["patientsID"] = pIDs
            for dC in self.catalog["deviceConnectorList"]:
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
                ID = self.catalog["counter"]["deviceConnectorCounter"]
                body["patientID"] = ID
                self.catalog["patientsList"].append(body)
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
                body["patients"] = ["1", "2", "37"]
                for nurse in self.catalog["nursesList"]:
                    if nurse["nurseID"] == body["nurseID"]:
                        nurse["patients"] = body["patients"]
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
        if uri[0] == "patient":
            for patient in self.catalog["patientsList"]:
                if patient["patientID"] == params["patientID"]:
                    self.catalog["patientsList"].remove(patient)
                else:
                    return "Patient not found"
            for dc in self.catalog["deviceConnectorList"]:
                if dc["deviceConnectorID"] == params["patientID"]:
                    self.catalog["deviceConnectorList"].remove(dc)
                    with open("catalog.json", "w") as file:
                        json.dump(self.catalog, file, indent = 4)
                    return json.dumps(patient, indent = 4)
        pass

    def checkLastUpdate(self, lastUpdate): #TODO debug it
        currentTime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        #convert the string to datetime
        datetime.strptime(lastUpdate, "%Y-%m-%dT%H:%M:%S")
        #check if the last update was more than 5 minutes ago
        if (currentTime - lastUpdate).total_seconds() > 300:
            return True
        return False
    
if __name__=="__main__":

    App = RegistrySystem()
    catalog = App.catalog

    #Standard configuration to serve the url "localhost:8080"
    conf={
        '/':{
        'request.dispatch':cherrypy.dispatch.MethodDispatcher(), 
        # this line must be here
        'tools.sessions.on':True
        }
    }
    cherrypy.tree.mount(RegistrySystem(),'/',conf) 
    cherrypy.config.update({'server.socket_port': 8080})
    cherrypy.config.update({'server.socket_host':'0.0.0.0'})
    cherrypy.engine.start()
    cherrypy.engine.block()

    while True: #TODO debug it
        try:
            # Iterate over serviceList
            for service in catalog.get("serviceList", []):
                toDelete = App.checkLastUpdate(service.get("lastUpdate"))
                if toDelete:
                    print(f"\n\n Found service toDelete {service}\n\n") #Fra trying to debugit
                    ID = service["serviceID"]
                    print(f"Service {ID} is going to be deleted")
                    catalog["serviceList"].remove(service)
                    with open("catalog.json", "w") as file:
                        json.dump(catalog, file, indent = 4)
            # Iterate over deviceConnectorList
            for deviceConnector in catalog.get("deviceConnectorList", []):
                toDelete = App.checkLastUpdate(deviceConnector.get("lastUpdate"))
                if toDelete:
                    ID = deviceConnector["deviceConnectorID"]
                    print(f"DeviceConnector {ID} is going to be deleted")
                    catalog["deviceConnectorList"].remove(deviceConnector)
                    with open("catalog.json", "w") as file:
                        json.dump(catalog, file, indent = 4)
        except:
            print("Error in the main loop")

# Alternativa di chat
# while True:
#     try:
#         # Create a new list with services that need to be deleted
#         services_to_delete = [service for service in catalog.get("serviceList", []) if App.checkLastUpdate(service.get("lastUpdate"))]
        
#         # Remove the services from the catalog
#         for service in services_to_delete:
#             ID = service["serviceID"]
#             print(f"Service {ID} is going to be deleted")
#             catalog["serviceList"].remove(service)

#         # Create a new list with device connectors that need to be deleted
#         connectors_to_delete = [connector for connector in catalog.get("deviceConnectorList", []) if App.checkLastUpdate(connector.get("lastUpdate"))]
        
#         # Remove the device connectors from the catalog
#         for connector in connectors_to_delete:
#             ID = connector["deviceConnectorID"]
#             print(f"DeviceConnector {ID} is going to be deleted")
#             catalog["deviceConnectorList"].remove(connector)

#         # Write the updated catalog to the file
#         with open("catalog.json", "w") as file:
#             json.dump(catalog, file, indent=4)

#     except KeyError as e:
#         print(f"Error: Key not found - {e}")

#     except Exception as e:
#         print(f"Error in the main loop: {e}")