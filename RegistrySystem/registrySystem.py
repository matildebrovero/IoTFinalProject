import cherrypy
import json

class RegistrySystem(object):
    #If I don't specify the following line, the class will not be visible as a web service
    exposed=True 
    def __init__(self): #we said that we want __init__ to be called when the object is created
        self.catalog = json.load(open("catalog.json"))

    def GET(self,*uri,**params): #uri is with * and params is with **
        #"http://localhost:8080/broker"
        if uri[0]=="broker":
            #return the broker information
            print("ok sono dentro broker")
            response = self.catalog["broker"]
            print(json.dumps(response, indent = 4))
            return json.dumps(response, indent = 4)

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
                body["serviceID"] = ID
                self.catalog["serviceList"].append(body)
                with open("catalog.json", "w") as file:
                    json.dump(self.catalog, file, indent = 4)
                print("Catalog updated with service:", body)
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
                body["deviceConnectorID"] = ID
                self.catalog["deviceConnectorList"].append(body)
                with open("catalog.json", "w") as file:
                    json.dump(self.catalog, file, indent = 4)
                print("Catalog updated with Device connector:", body)
                return json.dumps(body, indent = 4) 
        else:
            return "Empty body"
            
    def PUT(self,*uri,**params):
        pass
    def DELETE(self,*uri,**params):
        pass
    
if __name__=="__main__":
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