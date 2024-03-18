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
        print(f"Received new status: {self.sensorData}")
        print(f"Topic: {self.topic}")
        
        # Read the ECG and other sensors' data from the topic and write it to the InfluxDB
        if self.topic.split('/')[3] == "ECG":
            print("ECG data received")
            patientID = self.topic.split('/')[2]
            # Read the bucket from the DB adaptor config file
            buckets = json.load(open('DBadaptor_config.json'))["InfluxInformation"]["buckets"]
            for buck in buckets:
                if buck["data"] == self.topic.split('/')[3]:
                    print(buck["token"])
                    bucket = buck["token"]
            # Read the bucket from the DB adaptor config file 
            time = self.sensorData['e'][0]['t']
            value = self.sensorData['e'][0]['v']
            unit = self.sensorData['e'][0]['u']
            print(f'{self.topic} measured a value of {value} {unit} at the time {time}') 
            # Write to InfluxDB  
            point = (Point(self.topic.split('/')[3]).measurement(patientID).tag("unit", unit).field(self.topic.split('/')[3],value))
            print("Writing to InfluxDB")
            InfluxDBwrite(bucket,point)
        
        # Read the sensors' data from the topic and write it to the InfluxDB
        elif self.topic.split('/')[3] == "sensorsData":
            sensorList = self.sensorData['e']
            patientID = self.topic.split('/')[2]
            # Read the bucket from the DB adaptor config file
            bucketList = json.load(open('DBadaptor_config.json'))["InfluxInformation"]["buckets"]
            for sensor in sensorList:
                for bucket in bucketList:
                    if sensor['n'] == bucket['data']:
                        time = sensor['t']
                        value = sensor['v']
                        unit = sensor['u']
                        print(f'{sensor["n"]} measured a value of {value} {unit} at the time {time}') 
                        # Write to InfluxDB  
                        point = (Point(sensor["n"]).measurement(patientID).tag("unit", unit).field(sensor['n'], value))
                        InfluxDBwrite(bucket['token'],point)

        # Read the status from the topic and write it to the InfluxDB        
        elif self.topic.split('/')[3] == "status":
            patientID = self.topic.split('/')[2]
            status = self.sensorData['status']
            print(f'Patient {patientID} has a new status: {status}')
            # Read the bucket from the DB adaptor config file
            buckets = json.load(open('DBadaptor_config.json'))["InfluxInformation"]["buckets"]
            for buck in buckets:
                if buck["data"] == self.topic.split('/')[3]:
                    print(buck["token"])
                    bucket = buck["token"]
            # Write to InfluxDB
            point = (Point(self.topic.split('/')[3]).measurement(patientID).tag("unit", unit).field(self.topic.split('/')[3],value))
            print("Writing to InfluxDB")
            InfluxDBwrite(bucket,point)   
        
        elif self.topic.split('/')[3] == "RR":
            patientID = self.topic.split('/')[2]
            RR = self.sensorData['RR']
            print(f'Patient {patientID} has an RR interval equal to: {RR}')
            # Read the bucket from the DB adaptor config file
            buckets = json.load(open('DBadaptor_config.json'))["InfluxInformation"]["buckets"]
            for buck in buckets:
                if buck["data"] == self.topic.split('/')[3]:
                    print(buck["token"])
                    bucket = buck["token"]
            # Write to InfluxDB
            point = (Point(self.topic.split('/')[3]).measurement(patientID).tag("unit", unit).field(self.topic.split('/')[3],value))
            print("Writing to InfluxDB")
            InfluxDBwrite(bucket,point)   
        else:
            pass

    def startSim(self, topic):
        self.topic = topic
        self.ClientSubscriber.mySubscribe(self.topic)
    
    def StopSim(self):
        self.ClientSubscriber.unsubscribe() #automatic, no need to specify the topics
        self.ClientSubscriber.stop()

# INFLUXDB CLIENT TO WRITE DATA
def InfluxDBwrite(bucket,record):
    # read bucket from a config file
    write_api = client.write_api(write_options=SYNCHRONOUS)   
    write_api.write(bucket=bucket, org="SPHYNX", record=record)
    time.sleep(1) # separate points by 1 second
    print("Data written to InfluxDB")

# INFLUXDB CLIENT TO READ DATA
def InfluxDBread(query):
    print("Reading data from InfluxDB")
    query_api = client.query_api()
    tables = query_api.query(org="SPHYNX", query=query)
    results = {
            "bn": "InfluxDBdata", 
            "patientID": "",
            "e":{
                "n": "",
                "u": "",
                "t": "",
                "v": []
            }
        }
    for table in tables:
        for record in table.records:
            #results.append((record.get_measurement(), record.get_field(), record.get_value(), record.get_time()))
            results["e"]["v"].append(record.get_value())
            results["e"]["n"] = record.get_field()
            results["e"]["t"] = time.time()
            results["e"]["u"] = record.values.get("unit")
            results["patientID"] = record.get_measurement()
    
    return json.dumps(results)
    

# REST API
class rest_API(object):
    exposed = True
    def __init__(self):
        print("REST API created")
    def GET(self, *uri, **params):
        print("GET request received")
        buckets = json.load(open('DBadaptor_config.json'))["InfluxInformation"]["buckets"]
        for current_bucket in buckets:
            if current_bucket["data"] == uri[0]:
                bucket = current_bucket["token"]
        # Read data from InfluxDB and return them as a JSON
        if uri[0] in ["ECG", "glucometer", "temperature", "blood_pressure", "pulse", "oximeter", "RR", "status"]:
            patientID = uri[1]
            range = params["range"]
            query = f"""from(bucket: "{bucket}")
            |> range(start: -{range}m)
            |> filter(fn: (r) => r._measurement == "{str(patientID)}")"""
            print(query)
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
    # load the registry system
    ### LINES USED TO TEST THE CODE WITHOUT THE CATALOG
    """RegistrySystem = json.load(open(config_file["RegistrySystem"]))
    urlCatalog = RegistrySystem["catalogURL"]"""
    urlCatalog = config_file["RegistrySystem"]

    # read information from the configuration file and POST the information to the catalog
    #config = config_file["ServiceInformation"]
    config = requests.post(f"{urlCatalog}/service", data=config)
    config_file["ServiceInformation"] = config.json()
    # save the new configuration file
    json.dump(config_file, open("DBadaptor_config.json", "w"), indent = 4)

    # Read InfluxDB configuration from the configuration file
    token = config_file["InfluxInformation"]["INFLUXDB_TOKEN"]
    url = config_file["InfluxInformation"]["INFLUXDB_URL"]
    org = config_file["InfluxInformation"]["INFLUXDB_ORG"]
    # Create an instance of the InfluxDB client
    client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

    # get the information about the MQTT broker from the catalog using get requests
    MQTTinfo = json.loads(requests.get(f"{urlCatalog}/broker"))
    broker = MQTTinfo["IP"]
    port = MQTTinfo["port"]
    topics = MQTTinfo["main_topic"] + config_file["ServiceInformation"]["subscribe_topic"]
    clientID = config_file['serviceName'] + config_file["ServiceInformation"]['serviceID']
    ### LINES USED TO TEST THE CODE WITHOUT THE CATALOG
    """clientID = config_file["ServiceInformation"]['serviceName'] + config_file["ServiceInformation"]['serviceID']
    broker = RegistrySystem["broker"]["IP"]
    port = RegistrySystem["broker"]["port"]
    topics =  ["Monitoring/+/ECG", "Monitoring/+/sensorsData", "Monitoring/+/status"]"""

    # Create an instance of the SensorSubscriber
    subscriber = SensorSubscriber(clientID, broker, port)
    for topic in topics:
        final_topic = MQTTinfo["main_topic"] + topic
        subscriber.startSim(final_topic)
    
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
            time.sleep(0.5)
            #update the configuration file every 5 minutes (PUT REQUEST TO THE CATALOG)
            current_time = time.time()
            if current_time - start_time > 5*60:
                config_file = json.load(open('DBadaptor_config.json'))
                #config = requests.put(f"{urlCatalog}/service", data=config_file["ServiceInformation"])
                config_file["ServiceInformation"] = config.json()
                json.dump(config_file, open("DBadaptor_config.json", "w"), indent = 4)
                start_time = current_time
            else:
                pass
    except KeyboardInterrupt:
        subscriber.StopSim()
        cherrypy.engine.stop()


