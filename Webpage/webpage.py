from flask import Flask, render_template, request, jsonify
import requests
import json

app = Flask(__name__)

# Initial page
@app.route('/')
def index():
    # Load the configuration file using a get request to 0.0.0.0:8080/configwebpage
    # URI to ask configurqation file using data from the catalog
    """# load the configuration file of the Webpage
    conf = json.load(open("config_web.json"))
    # load the registry system
    urlCatalog = conf["RegistrySystem"]
    # read information from the configuration file and POST the information to the catalog
    config = conf["information"]
    config = requests.post(f"{urlCatalog}/service", data=config)
    conf["information"] = config.json()"""

    uri = "http://localhost:8080/configwebpage"
    try:
        response = requests.get(uri)
        print(response)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        data = response.json()
        print(data)
        return render_template('index.html', config=data)
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)})
    #return render_template('index.html')

# Function to get the data from the server (GET REQUEST)
@app.route('/getData', methods=['POST'])
def getData():
    patientSelected = request.form['patientSelect']
    dataSelected = request.form['dataSelect']
    timeRange = request.form['timeRange']
    print(patientSelected, dataSelected, timeRange)

    # URI to ask data from the database
    uri = f"http://localhost:8081/{dataSelected}/{patientSelected}?range={timeRange}"
    print(uri)

    try:
        response = requests.get(uri)
        print(response)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        data = response.json()
        print(data)
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)})

@app.route('/addPatient', methods=['POST'])
def add_patient():
    # Get the data from the form
    new_patient_data = request.form.to_dict()
    #print("New Patient Data:", new_patient_data)

    # URI to post data in the catalog
    uri = f"http://localhost:8080/patient"
    print(uri)

    try:
        # Save the new patient data in the catalog
        response = requests.post(uri, data=new_patient_data)
        print(response)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        data = response.json()
        print(data)
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
