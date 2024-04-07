import requests
import json

url = "http://localhost:8081/glucometer/patient47?range=5"
response = requests.get(url)
print(response)
response_gluco = json.loads(response.json())
print(response_gluco)
if "e" in response_gluco:
    print(response_gluco["e"]["v"])
else:
    print("Key 'e' not found in the response.")
