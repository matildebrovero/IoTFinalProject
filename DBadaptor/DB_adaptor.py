# COMMAND TO INSTALL INFLUXDB CLIENT
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
    DB_adaptor - SmartHospital IoT platform. Version 1.0.1 
    This microservice is responsible for reading the data from the sensors and writing them to the InfluxDB and for getting the data from the InfluxDB and returning them as a JSON to the services that request them. 
     
        Input:  
            - Data from all the sensors and from the ECG Analysis service
            - GET requests from the services that want to read the data from the InfluxDB
        Output:
            - Data written to the InfluxDB
            - Data read from the InfluxDB and returned as a JSON to the services that requested them following the SenML standard
 
    -------------------------------------------------------------------------- 
    --------------         standard configuration          ------------------- 
    -------------------------------------------------------------------------- 
 
    Standard Configuration file provided: ECGAn_configuration.json 
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
            - "subscribe_topic": Topic where the service will subscribe to read the data from the sensors
                    Example: "SmartHospitalN/Monitoring/patientN/ECG"
                    to get the data from every patient present the wildcard "+" is used
            - "publish_topic": Topic where the service will publish the data to the sensors
            - "uri": 
                - "add_service": URI to add the service to the Registry System
                - "broker_info": URI to get the information about the MQTT broker from the Registry System           
 
    """ 

# MQTT SUBSCRIBER
class SensorSubscriber:
    def __init__(self, clientID, broker, port):
        self.SensorData = None
        self.topic = None
        self.ClientSubscriber = MyMQTT(clientID, broker, port, self)
        self.ClientSubscriber.start()

    def notify(self, topic, payload):
        self.topic = topic
        self.sensorData = json.loads(payload)
        #print(f"Received new status: {self.sensorData}")
        print(f"Topic: {self.topic}")

        # Read the HR data from the topic and write it to the InfluxDB
        if self.topic.split('/')[3] == "HR":
            print(f"{self.topic.split('/')[3]} Data received")
            patientID = self.topic.split('/')[2]
            # Read the bucket from the DB adaptor config file
            bucket = json.load(open('DBadaptor_config.json'))["InfluxInformation"]["bucket"]
            # Read the bucket from the DB adaptor config file 
            basetime = self.sensorData['bt'] * 1000000000 # convert to nanoseconds
            time = basetime + self.sensorData['e'][0]['t'] * 1000000000 # convert to nanoseconds
            print(f"basetime: {basetime}")
            value = self.sensorData['e'][0]['v']
            unit = self.sensorData['e'][0]['u']
            print(f'{self.topic} measured a value of {value} {unit} at the time {time}') 
            # Write to InfluxDB  
            point = (Point(self.topic.split('/')[3]).measurement(patientID).tag("unit", unit).field(self.topic.split('/')[3],value).time(int(time)))
            # Print the data that is written to the InfluxDB
            print(f"Writing to InfluxDB {point.to_line_protocol()}")
            InfluxDBwrite(bucket,point)
        
        # Read the ECG, RR signals from the topic and write it to the InfluxDB
        if self.topic.split('/')[3] in ["RR", "ECG"]:
            #print(f"{self.topic.split('/')[3]} Data received")
            patientID = self.topic.split('/')[2]
            # Read the bucket from the DB adaptor config file
            bucket = json.load(open('DBadaptor_config.json'))["InfluxInformation"]["bucket"]
            # Read the bucket from the DB adaptor config file 
            basetime = self.sensorData['bt'] * 1000000000 # convert to nanoseconds
            #print(f"basetime: {basetime}")
            print(len(self.sensorData['e']))
            for i in range(len(self.sensorData['e'])):
                time = basetime + self.sensorData['e'][i]['t'] * 1000000000 # convert to nanoseconds
                value = self.sensorData['e'][i]['v']
                unit = self.sensorData['e'][i]['u']
                #print(f'{self.topic} measured a value of {value} {unit} at the time {time}') 
                # Write to InfluxDB  
                point = (Point(self.topic.split('/')[3]).measurement(patientID).tag("unit", unit).field(self.topic.split('/')[3],value).time(int(time)))
                # Print the data that is written to the InfluxDB
                #print(f"Writing to InfluxDB {point.to_line_protocol()}")
                InfluxDBwrite(bucket,point)
        
        # Read the sensors' data from the topic and write it to the InfluxDB
        if self.topic.split('/')[3] == "sensorsData":
            print(f"{self.topic.split('/')[3]} Data received")
            sensorList = self.sensorData['e']
            print(sensorList)
            patientID = self.topic.split('/')[2]
            # Read the bucket from the DB adaptor config file
            bucket = json.load(open('DBadaptor_config.json'))["InfluxInformation"]["bucket"]
            for sensor in sensorList:
                print(sensor)
                time = sensor['t'] * 1000000000 # convert to nanoseconds
                value = sensor['v']
                unit = sensor['u']
                print(f'{sensor["n"]} measured a value of {value} {unit} at the time {time}') 
                # Write to InfluxDB  
                point = (Point(sensor["n"]).measurement(patientID).tag("unit", unit).field(sensor['n'], value).time(int(time)))
                # Print the data that is written to the InfluxDB
                print(f"Writing {sensor} to InfluxDB {point.to_line_protocol()}")
                InfluxDBwrite(bucket,point)

        # Read the status from the topic and write it to the InfluxDB        
        if self.topic.split('/')[3] == "status":
            print(f"{self.topic.split('/')[3]} Data received")
            patientID = self.topic.split('/')[2]
            # Read the bucket from the DB adaptor config file
            bucket = json.load(open('DBadaptor_config.json'))["InfluxInformation"]["bucket"]
            # Read the bucket from the DB adaptor config file 
            time = self.sensorData['e'][0]['t'] * 1000000000 # convert to nanoseconds
            value = self.sensorData['e'][0]['v']
            unit = self.sensorData['e'][0]['u']
            point = (Point(self.topic.split('/')[3]).measurement(patientID).tag("unit", unit).field(self.topic.split('/')[3],value).time(time))
            # Print the data that is written to the InfluxDB
            print(f"Writing to InfluxDB {point.to_line_protocol()}")
            InfluxDBwrite(bucket,point)   
        
        else:
            pass

    def startSim(self, topic):
        self.topic = topic
        self.ClientSubscriber.mySubscribe(self.topic)
    
    def StopSim(self):
        self.ClientSubscriber.unsubscribe() 
        self.ClientSubscriber.stop()

# INFLUXDB CLIENT TO WRITE DATA
def InfluxDBwrite(bucket,record):
    # read bucket from a config file
    write_api = client.write_api(write_options=SYNCHRONOUS)   
    write_api.write(bucket=bucket, org="SPHYNX", record=record)
    #time.sleep(1) # separate points by 1 second
    #print("Data written to InfluxDB")

# INFLUXDB CLIENT TO READ DATA
def InfluxDBread(query):
    query_api = client.query_api()
    tables = query_api.query(org="SPHYNX", query=query)
    results = json.load(open('DBadaptor_config.json'))["InfluxInformation"]["results"]
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
        bucket = json.load(open('DBadaptor_config.json'))["InfluxInformation"]["bucket"]
        availableSensor = requests.get(f"{urlCatalog}/availableData")
        print("\n\n\n\n")
        print(f"Available sensors: {availableSensor.text}")
        # Read data from InfluxDB and return them as a JSON
        if uri[0] in availableSensor:
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
            raise(cherrypy.HTTPError(404, "Resource not found"))
    def POST(self, *uri, **params):
        pass
    def PUT(self, *uri, **params):
        pass
    def DELETE(self, *uri, **params):
        pass


if __name__ == "__main__":
    start_time = time.time()
    # Open configuration file to read InfluxDB token, org and url and MQTT clientID, broker, port and base topic
    config_file = json.load(open('DBadaptor_config.json'))

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
        json.dump(config_file, open("DBadaptor_config.json", "w"), indent = 4)
    else:
        print(f"Error: {config.status_code} - {config.text}")
    
    # Read InfluxDB configuration from the configuration file
    token = config_file["InfluxInformation"]["INFLUX_TOKEN"]
    url = config_file["InfluxInformation"]["INFLUXDB_URL"]
    org = config_file["InfluxInformation"]["INFLUXDB_ORG"]
    # Create an instance of the InfluxDB client
    client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)


    # get the information about the MQTT broker from the catalog using get requests
    MQTTinfo = json.loads(requests.get(f"{urlCatalog}/{config_file['ServiceInformation']['uri']['broker_info']}").text)
    broker = MQTTinfo["IP"]
    port = MQTTinfo["port"]
    print(config_file["ServiceInformation"]["subscribe_topic"])
    topics = []
    for topic in config_file["ServiceInformation"]["subscribe_topic"]:
        topics.append(MQTTinfo["main_topic"] + topic)
    clientID = config_file["ServiceInformation"]['serviceName'] + str(config_file["ServiceInformation"]['serviceID'])

    ###############
    ### LINES USED TO TEST THE CODE WITHOUT THE CATALOG
    ###############
    """clientID = config_file["ServiceInformation"]['serviceName'] + config_file["ServiceInformation"]['serviceID']
    broker = RegistrySystem["broker"]["IP"]
    port = RegistrySystem["broker"]["port"]
    topics =  ["SmartHospital308/Monitoring/+/ECG", "SmartHospital308/Monitoring/+/RR", "SmartHospital308/Monitoring/+/sensorsData", "SmartHospital308/Monitoring/+/status"]"""

    # Create an instance of the SensorSubscriber
    subscriber = SensorSubscriber(clientID, broker, port)
    for topic in topics:
        #final_topic = MQTTinfo["main_topic"] + topic  
        #final_topic = topic
        subscriber.startSim(topic)
    
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
    cherrypy.engine.block()
    try:
        while True:
            #update the configuration file every 5 minutes (PUT REQUEST TO THE CATALOG)
            current_time = time.time()
            if current_time - start_time > 5*60:
                config_file = json.load(open('DBadaptor_config.json'))
                config = requests.put(f"{urlCatalog}/{config_file['uri']['broker_info']}", json=config_file["ServiceInformation"])
                if config.status_code == 200:
                    print(f"Service Information: {config}")
                    config_file["ServiceInformation"] = config.json()
                    # print the updated information about the service
                    print(f"Service Information: {config_file['ServiceInformation']}")
                    json.dump(config_file, open("DBadaptor_config.json", "w"), indent = 4)
                    start_time = current_time
                else:
                    print(f"Error: {config.status_code} - {config.text}")
            else:
                pass
            #time.sleep(0.001)
    except KeyboardInterrupt:
        subscriber.StopSim()
        cherrypy.engine.stop()


