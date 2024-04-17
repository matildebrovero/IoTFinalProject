# DB READER
# pip install influxdb-client

# Import libraries
import influxdb_client, os, time
import json
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from MyMQTT import * #importing MyMQTT class from MyMQTT.py
import cherrypy
import requests
import time

""" 
    DB_reader - SmartHospital IoT platform. Version 1.0.1 
    This microservice is responsible for reading the data from influxDB if data are asked trough REST request.
     
        Input:  
            - GET requests from the services that want to read the data from the InfluxDB
        Output:
            - Data read from the InfluxDB and returned as a JSON to the services that requested them following the SenML standard
 
    -------------------------------------------------------------------------- 
    --------------         standard configuration          ------------------- 
    -------------------------------------------------------------------------- 
 
    Standard Configuration file provided: DB_reader_config.json
    The parameters of the configuration file are: 
 
        - "RegistrySystem": URL of the Registry System 

        - "InfluxInformation": 
            - "INFLUXDB_TOKEN": Token of the InfluxDB database
            - "INFLUXDB_ORG": Organization of the InfluxDB database
            - "INFLUXDB_URL": URL of the InfluxDB database
            - "bucket": Bucket of the InfluxDB database where the data will be written
            - "results": SenML format to return the data read from the InfluxDB as a JSON
 
        - "SensorsAvailable": List of the sensors available in the Smart Hospital

        - "ServiceInformation": 
            - "serviceID": ID of the service
            - "availableServices": List of the communication protocol available for this service (MQTT, REST)
            - "serviceName": Name of the service = "DB_adaptor" 
            - "serviceHost": Host of the service = "localhost"
            - "servicePort": Port of the service exposed to make get request to retrieve data
            - "uri": 
                - "add_service": URI to add the service to the Registry System
                - "broker_info": URI to get the information about the MQTT broker from the Registry System           
            - "lastUpdate": Last time the configuration file was updated
    """ 

# INFLUXDB CLIENT TO READ DATA
def InfluxDBread(query):
    query_api = client.query_api()
    tables = query_api.query(org="SPHYNX", query=query)
    results = json.load(open('DB_reader_config.json'))["InfluxInformation"]["results"]
    for table in tables:
        for record in table.records:
            results["e"]["v"].append(record.get_value())
            results["e"]["n"] = record.get_field()
            results["e"]["t"].append(record.get_time().isoformat()) #convert object datetime to isoformat which is "YYYY-MM-DDTHH:MM:SS.ffffff+00:00"
            results["e"]["u"] = record.values.get("unit")
            results["patientID"] = record.get_measurement()
    print(f"Data read from InfluxDB {json.dumps(results, indent=4)}")
    return json.dumps(results)
    

# REST API
class rest_API(object):
    exposed = True
    def __init__(self):
        print("REST API created")
    def GET(self, *uri, **params):
        print("GET request received")
        bucket = json.load(open('DB_reader_config.json'))["InfluxInformation"]["bucket"]
        availableSensor = requests.get(f"{urlCatalog}/availableData")
        print("\n\n\n\n")
        print(f"Available sensors: {availableSensor.text}")
        # Read data from InfluxDB and return them as a JSON
        # print(uri)
        # print(params)
        # print(availableSensor.json())
        if len(uri) == 2:
            if uri[0] in availableSensor.json():
                print(f"Reading {uri[0]} data from InfluxDB")
                patientID = uri[1]
                range = params["range"]
                query = f"""from(bucket: "{bucket}")
                |> range(start: -{range}m)
                |> filter(fn: (r) => r._measurement == "{str(patientID)}")
                |> filter(fn: (r) => r._field == "{uri[0]}")"""
                print(query)
                print(f"Reading {uri[0]} data for patient {patientID} from InfluxDB")
                return json.dumps(InfluxDBread(query))
            else:
                raise(cherrypy.HTTPError(404, "Resource not found. URI not valid"))
        else:
            raise(cherrypy.HTTPError(500, "Internal server error. You have to insert an URI with the format /sensorID/patientID?range=minutes"))
    def POST(self, *uri, **params):
        pass
    def PUT(self, *uri, **params):
        pass
    def DELETE(self, *uri, **params):
        pass


if __name__ == "__main__":
    start_time = time.time()
    # Open configuration file to read InfluxDB token, org and url and MQTT clientID, broker, port and base topic
    config_file = json.load(open('DB_reader_config.json'))

    # load the url of the registry system from the configuration file
    urlCatalog = config_file["RegistrySystem"]

    ########################
    ### LINES USED TO TEST THE CODE WITHOUT THE CATALOG
    ########################
    """RegistrySystem = json.load(open("../RegistrySystem/catalog.json"))
    urlCatalog = config_file["RegistrySystem"]"""

    # read information from the configuration file and POST the information to the catalog
    config = config_file["ServiceInformation"]
    config = requests.post(f"{urlCatalog}/{config_file['ServiceInformation']['uri']['add_service']}", json=config_file["ServiceInformation"])
    if config.status_code == 200:
        print(f"Service Information: {config}")
        config_file["ServiceInformation"] = config.json()
        # print the updated information about the service
        print(f"Service Information: {config_file['ServiceInformation']}")
        # save the new configuration file
        json.dump(config_file, open("DB_reader_config.json", "w"), indent = 4)
    else:
        print(f"Error: {config.status_code} - {config.text}")
    
    # Read InfluxDB configuration from the configuration file
    token = config_file["InfluxInformation"]["INFLUX_TOKEN"]
    url = config_file["InfluxInformation"]["INFLUXDB_URL"]
    org = config_file["InfluxInformation"]["INFLUXDB_ORG"]
    # Create an instance of the InfluxDB client
    client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

    ###############
    ### LINES USED TO TEST THE CODE WITHOUT THE CATALOG
    ###############
    """clientID = config_file["ServiceInformation"]['serviceName'] + config_file["ServiceInformation"]['serviceID']
    broker = RegistrySystem["broker"]["IP"]
    port = RegistrySystem["broker"]["port"]
    topics =  ["SmartHospital308/Monitoring/+/ECG", "SmartHospital308/Monitoring/+/RR", "SmartHospital308/Monitoring/+/sensorsData", "SmartHospital308/Monitoring/+/status"]"""


    # Start the REST API
    #get the information about host and port from the configuration file
    host = config_file["ServiceInformation"]["serviceHost"]
    port = config_file["ServiceInformation"]["servicePort"]
    conf={
        '/':{
        'request.dispatch':cherrypy.dispatch.MethodDispatcher(), #this line must be here
        'tools.sessions.on':True
        }
    }
    cherrypy.tree.mount(rest_API(), '/', conf)
    #http://{host}:{port} 
    cherrypy.config.update({'server.socket_host': host})
    cherrypy.config.update({'server.socket_port': port})
    cherrypy.engine.start()
   
    try:
        while True:
            #update the configuration file every 5 minutes (PUT REQUEST TO THE CATALOG)
            current_time = time.time()
            if current_time - start_time > 5*60:
                config_file = json.load(open('DB_reader_config.json'))
                config = requests.put(f"{urlCatalog}/{config_file['ServiceInformation']['uri']['add_service']}", json=config_file["ServiceInformation"])
                if config.status_code == 200:
                    print(f"Service Information: {config}")
                    config_file["ServiceInformation"] = config.json()
                    # print the updated information about the service
                    print(f"Service Information: {config_file['ServiceInformation']}")
                    json.dump(config_file, open("DB_reader_config.json", "w"), indent = 4)
                    start_time = current_time
                else:
                    print(f"Error: {config.status_code} - {config.text}")
            else:
                pass
            time.sleep(10)
    except KeyboardInterrupt:
        print("DB_reader is stopped")
        cherrypy.engine.stop()



