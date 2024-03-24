import cherrypy
import json
from datetime import datetime 

class RegistrySystem(object):
    #If I don't specify the following line, the class will not be visible as a web service
    exposed=True 
    def __init__(self): #we said that we want __init__ to be called when the object is created
        self.catalog = json.load(open("catalog.json"))
        #initialize the configuration for the web page
        self.configWebPage = {
            "patientsID": [],
            "data": [],
            "deviceConnectors":[]
            } #TODO capire con mati se è giusto inizializzarlo qui o farlo ogni volta che arriva la richiesta, perchè qui una volta che lo modifico che le modifiche rimnagono e non vorrei che poi ad una successiva richiesta mi ritorni un json con valori che non sono più validi ha in memoria quelle vecchie

    def GET(self,*uri,**params): #uri is with * and params is with **
        #"http://localhost:8080/broker"
        if uri[0]=="broker":
            #return the broker information
            print("ok sono dentro broker")
            response = self.catalog["broker"]
            print(json.dumps(response, indent = 4))
            return json.dumps(response, indent = 4)
        
        #"http://localhost:8080/DBadaptor"
        if uri[0] == "DBadaptor":
            for s in self.catalog["serviceList"]:
                if s["serviceName"] == "DB_adaptor":
                    return json.dumps({"urlDB" : "http://"+s["serviceHost"]+":"+str(s["servicePort"])})
        
        #"http://localhost:8080/configwebpage"
        if uri[0] == "configwebpage": #TODO debug it
            pIDs = []
            data = []
            dConnectors = []
            for patient in self.catalog["patientsList"]:
                pIDs.append(patient["patientID"])
                self.configWebPage["patientsID"] = "patient"+pIDs[patient]
            for dC in self.catalog["deviceConnectorList"]:
                dConnectors.append(dC["deviceConnectorID"])
                self.configWebPage["deviceConnectors"] = "device"+dConnectors[dC]
                data.append(dC["measureType"])
                self.configWebPage["data"] = data
                #aggiungere hardcoded HR RR e status a data
            return json.dumps(self.configWebPage, indent = 4)
        
        if uri[0] == "patientInfo": #TODO debug it
            if uri[1] == "All":
                pIDs = []
                pStatus = []
                for p in self.catalog["patientsList"]:
                    pIDs.append(p["patientID"])
                    pStatus.append(p["patientCondition"])
                return json.dumps({"patientID": pIDs, "patientCondition": pStatus}, indent = 4)
            #TODO capire se mati li passa come parametri o come uri

    def POST(self,*uri,**params):
        rawBody = cherrypy.request.body.read()
        print("Raw Body:", rawBody)
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
                #retrieve the unique ID from the catalog
                ID = self.catalog["counter"]["serviceCounter"]
                print("ID:", ID)
                self.catalog["counter"]["serviceCounter"] += 1
                body["information"]["serviceID"] = ID
                body["information"]["lastUpdate"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                self.catalog["serviceList"].append(body["information"])
                with open("catalog.json", "w") as file:
                    json.dump(self.catalog, file, indent = 4)
                print("Catalog updated with service:", body["information"])
                return json.dumps(body, indent = 4)
            
            #"http://localhost:8080/DeviceConnector"
            if uri[0] == "DeviceConnector":
                # Debugging statement to ensure entering devconn condition
                print("Inside DeviceConnector Condition")
                #add the new deviceConnector to the catalog
                #retrieve the unique ID from the catalog
                ID = self.catalog["counter"]["deviceConnectorCounter"]
                print("ID:", ID)
                self.catalog["counter"]["deviceConnectorCounter"] += 1
                body["information"]["deviceConnectorID"] = ID
                body["information"]["lastUpdate"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                self.catalog["deviceConnectorList"].append(body["information"])
                with open("catalog.json", "w") as file:
                    json.dump(self.catalog, file, indent = 4)
                print("Catalog updated with Device connector:", body["information"])
                return json.dumps(body, indent = 4)

            #"http://localhost:8080/patient"
            if uri[0] == "patient":
                # Debugging statement to ensure entering patient condition
                print("Inside Patient Condition")
                #add the new patient to the catalog
                #retrieve the unique ID from the catalog
                #Each patient has the same ID as the deviceConnector
                ID = self.catalog["counter"]["deviceConnectorCounter"]
                print("ID:", ID)
                body["patientID"] = ID
                self.catalog["patientsList"].append(body)
                with open("catalog.json", "w") as file:
                    json.dump(self.catalog, file, indent = 4)
                print("Catalog updated with patient:", body)
                return json.dumps(body, indent = 4)
        else:
            return "Empty body"
            
    def PUT(self,*uri,**params): 
        rawBody = cherrypy.request.body.read()
        print("Raw Body:", rawBody)
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
                ID = body["information"]["serviceID"]
                print("ID:", ID)
                for service in self.catalog["serviceList"]:
                    if service["serviceID"] == ID:
                        service["lastUpdate"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        service.update(body["information"])
                        with open("catalog.json", "w") as file:
                            json.dump(self.catalog, file, indent = 4)
                        print("Catalog updated with service:", body["information"])
                        return json.dumps(body, indent = 4)
                return "Service not found"
            
            #"http://localhost:8080/DeviceConnector"
            if uri[0] == "DeviceConnector":
                # Debugging statement to ensure entering devconn condition
                print("Inside DeviceConnector Condition")
                #retrieve the unique ID from the catalog
                ID = body["information"]["deviceConnectorID"]
                print("ID:", ID)
                for deviceConnector in self.catalog["deviceConnectorList"]:
                    if deviceConnector["deviceConnectorID"] == ID:
                        deviceConnector["lastUpdate"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        deviceConnector.update(body["information"])
                        with open("catalog.json", "w") as file:
                            json.dump(self.catalog, file, indent = 4)
                        print("Catalog updated with Device connector:", body["information"])
                        return json.dumps(body, indent = 4)
                return "DeviceConnector not found"
        else:
            return "Empty body"
        
    def DELETE(self,*uri,**params):
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