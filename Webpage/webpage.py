from flask import Flask, render_template, request, jsonify
import requests
import json
from configreader import read_config, save_config


app = Flask(__name__)

# Initial page
@app.route('/')
def index():
    # Load the configuration file using a get request to 0.0.0.0:8080/configwebpage
    # URI to ask configurqation file using data from the catalog
    # load the configuration file of the Webpage and convert it from a dictionary to a JSON object
    conf = read_config()
    print(conf)
    # load the registry system
    urlCatalog = conf["RegistrySystem"]
    print(urlCatalog)
    # read information from the configuration file and POST the information to the catalog
    #config = conf["information"]
    #print(config)
    #config = requests.post(f"{urlCatalog}/service", data=config)
    #conf["information"] = config.json()
    #save_config(conf)
    
    uri = f"{urlCatalog}/configwebpage"
    print(uri)
    try:
        response = requests.get(uri)
        print(response)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        data = response.json()
        print(data)
        return render_template('index.html', config=data)
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)})
    

# Function to get the data from the server (GET REQUEST)
@app.route('/getData', methods=['POST'])
def getData():
    patientSelected = request.form['patientSelect']
    dataSelected = request.form['dataSelect']
    timeRange = request.form['timeRange']
    print(patientSelected, dataSelected, timeRange)

    conf = read_config()

    # URI to ask data from the database for a certain patient and time range
    uri = f"{conf['Database']}/{dataSelected}/{patientSelected}?range={timeRange}"
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
    conf = read_config()
    # URI to post data in the catalog
    uri = f"{conf['RegistrySystem']}/patient"
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

@app.route('/deletePatient', methods=['POST'])
def delete_patient():
    # Get the data from the form
    patient_id = request.form.to_dict()
    patient_id = patient_id['selectedpatient']
    #print("Patient ID:", patient_id)
    conf = read_config()
    # URI to delete data in the catalog
    uri = f"{conf['RegistrySystem']}/patient/{patient_id}"
    print(uri)

    try:
        # Delete the patient data in the catalog
        response = requests.delete(uri)
        print(response)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        data = response.json()
        print(data)
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':

    app.run(debug=True)

    
