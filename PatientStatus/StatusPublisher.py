from MyMQTT import *
import time

class StatusManager:
	def __init__(self, clientID, broker, port):
		self.client=MyMQTT(clientID,broker,port,None)
		self.statusToBool={"good":True,"bad":False}


	def startSim (self):
		self.client.start()

	def stopSim (self):
		self.client.stop()

	def publish(self,topic,value):
		message=value
		self.client.myPublish(topic,message)
		print(f"Publisher on topic {topic}")
		print(f"published Message: \n {message}")