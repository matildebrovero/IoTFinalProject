import requests
import json

url = "http://localhost:8081/glucometer/patient47?range=5"
response_gluco = requests.get(url)
print(response_gluco)
response_gluco = json.loads(response_gluco.text)
print(response_gluco)
print(response_gluco["e"])
