from flask import Flask, render_template, request, jsonify
import requests
import json
from configreader import read_config, save_config
from apscheduler.schedulers.background import BackgroundScheduler
import time

""" 
    Webpage - SmartHospital IoT platform. Version 1.0.1 
    This microservice is responsible for displaying the data from the sensors in the Smart Hospital.
    It also allows the user to add new patients and delete existing patients from the system.
    It is also possible to add new nurses, modify the patient a nurse is taking care of and delete existing nurses from the system.
     
        Input:  
            - Data from the Database and the Registry System
        Output:
            - Visualization of the data in the Webpage
            - Adding and deleting patients from the Registry System
            - Adding, modifying and deleting nurses from the Registry System
 
    -------------------------------------------------------------------------- 
    --------------         standard configuration          ------------------- 
    -------------------------------------------------------------------------- 
 
    Standard Configuration file provided: webpage_configuration.json
    The parameters of the configuration file are: 
 
        - "RegistrySystem": URL of the Registry System 
 
        - "information": 
            - "serviceID": ID of the service
            - "serviceName": Name of the service = "DB_writer" 
            - "availableServices": List of the communication protocol available for this service (MQTT)
            - "uri": 
                - "add_service": URI to add the service to the Registry System
                - "get_configurations": URI to get the configuration file from the Registry System
                - "patient": URI to delete a patient from the Registry System  
                - "delete_patient": params to delete a patient from the Registry System  
                - "nurse": URI to delete a nurse from the Registry System
                - "delete_nurse": params to delete a nurse from the Registry System
                - "add_nurse": URI to add a nurse to the Registry System
                - "modify_patients": URI to modify the patients of a nurse in the Registry System
                - "DB_adaptor": URI to get the information about the DB adaptor from the Registry System
            - "port": Port of the service exposed to show the Webpage
            - "host": Host of the service = "localhost"
            - "lastUpdate": Last time the configuration file was updated

 
    """ 


app = Flask(__name__)

# Function to update the configuration file of the Webpage every 5 minutes by doing a PUT request to the registry system
def update_config():
    # load the configuration file of the Webpage and convert it from a dictionary to a JSON object
    conf = read_config()
    print(conf)
    # load the registry system
    urlCatalog = conf["RegistrySystem"]
    print(urlCatalog)
    # read information from the configuration file and PUT the information to the catalog
    config = conf["information"]

    print("\n\nPUT REQUEST")
    print(config)
    config = requests.put(f"{urlCatalog}/{conf['information']['uri']['add_service']}", json=config)
    conf["information"] = config.json()
    # save the configuration file
    save_config(conf)
    

# Function to initialize the configuration file of the Webpage by doing a POST request to the registry system
@app.before_first_request
def initialize():
    # load the configuration file of the Webpage and convert it from a dictionary to a JSON object
    conf = read_config()
    print(conf)
    # load the registry system
    urlCatalog = conf["RegistrySystem"]
    print(urlCatalog)
    # read information from the configuration file and POST the information to the catalog
    config = conf["information"]

    print("\n\nPOST REQUEST")
    print(config)
    config = requests.post(f"{urlCatalog}/{conf['information']['uri']['add_service']}", json=config)
    conf["information"] = config.json()
    # save the configuration file
    save_config(conf)


# Initial page of the Webpage
@app.route('/')
def index():
    # load the configuration file of the Webpage and convert it from a dictionary to a JSON object
    conf = read_config()
    print(conf)
    # load the registry system
    urlCatalog = conf["RegistrySystem"]
    # Load the configuration file using a get request to 0.0.0.0:8080/configwebpage
    # URI to ask to the registry system configuration file containing patients, nurses and data available 
    uri = f"{urlCatalog}/{conf['information']['uri']['get_configurations']}"

    print(f"\n\nRequesting configuration file from {uri}")
    try:
        response = requests.get(uri)
        print(response)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        data = response.json()
        print(data)
        return render_template('index.html', config=data)
    except requests.exceptions.RequestException as e:
        print(f"\n\nERROR {e}")
        return jsonify({'error': str(e)})
        

# Function to get the data from the registry system (GET REQUEST) and display it in the Webpage
@app.route('/getData', methods=['POST'])
def getData():
    patientSelected = request.form['patientSelect']
    dataSelected = request.form['dataSelect']
    timeRange = request.form['timeRange']
    print(patientSelected, dataSelected, timeRange)

    conf = read_config()

    # URI to get the DB adaptor information from the registry system
    DBuri = f"{conf['RegistrySystem']}/{conf['information']['uri']['DB_adaptor']}"
    print(f"\n\nGET requesto to get DB adaptor information from {DBuri}")

    DB = requests.get(DBuri)
    if DB.status_code == 200:
        Database = DB.json()["urlDB"]
        print(f"Database Information: {DB}")
    else:
        print(f"Error: {DB.status_code} - {DB.text}")

    # URI to ask data from the database for a certain patient and time range
    uri = f"{Database}/{dataSelected}/patient{patientSelected}?range={timeRange}"

    print(f"\nRequesting data from {Database} for patient {patientSelected} and data {dataSelected} in the last {timeRange} minutes")

    try:
        response = requests.get(uri)
        print(response)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        data = response.json()
        print(data)
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        print(f"\n\nERROR {e}")
        return jsonify({'error': str(e)})

# Function to add a new patient to the registry system (POST REQUEST) by linking the patient to an existing device connector
@app.route('/addPatient', methods=['POST'])
def add_patient():
    # Get the data from the form
    new_patient_data = request.form.to_dict()

    print("\n\nNew Patient Data:", new_patient_data)
    # Load the configuration file of the Webpage to get the URI of the Registry System
    conf = read_config()
    # URI to post data in the catalog
    uri = f"{conf['RegistrySystem']}/{conf['information']['uri']['patient']}"
    print(f"\n\nAdding new patient to registry system to {uri}")
    try:
        # Save the new patient data in the catalog
        response = requests.post(uri, json=new_patient_data)
        print(response)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        data = response.json()
        print(data)
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        print(f"\n\nERROR {e}")
        return jsonify({'error': str(e)})
    
# Function to add a new Nurse to the registry system (POST REQUEST) 
@app.route('/addNurse', methods=['POST'])
def add_nurse():
    # Get the data from the form
    new_nurse_data = request.form.to_dict()

    name = new_nurse_data['firstName']
    surname = new_nurse_data['lastName']
    birthdate = new_nurse_data['birthdate']
    #print(birthdate)
    patients = []
    for patient in new_nurse_data['patients']:
        if patient != ',':
            patients.append(patient)
    new_nurse_data = {'nurseName': name + ' ' + surname, 'nurseBirthDate': birthdate, 'patients': patients}

    print("\n\nNew Nurse Data:", new_nurse_data)

    # Load the configuration file of the Webpage to get the URI of the Registry System
    conf = read_config()
    # URI to post data in the catalog
    uri = f"{conf['RegistrySystem']}/{conf['information']['uri']['add_nurse']}"

    print(f"\n\nAdding new nurse to registry system to {uri}")
    try:
        # Save the new nurse data in the catalog
        response = requests.post(uri, json=new_nurse_data)
        print(response)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        data = response.json()
        print(data)
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        print(f"\n\nERROR {e}")
        return jsonify({'error': str(e)})

# Function to modify a nurse from the registry system (PUT REQUEST)
@app.route('/modifyNurse', methods=['POST'])
def modify_nurse():
    # Get the data from the form
    nurse_data = request.form.to_dict()
    ID = nurse_data['nurseID']
    patients = []
    for patient in nurse_data['patients']:
        if patient != ',':
            patients.append(patient)
    
    nurse_data = {'nurseID': ID, 'patients': patients}
    #print("\n\nModified nurse data:", nurse_data)
    # Load the configuration file of the Webpage to get the URI of the Registry System
    conf = read_config()
    # URI to delete data in the catalog
    uri = f"{conf['RegistrySystem']}/{conf['information']['uri']['nurse']}/{conf['information']['uri']['modify_patients']}"

    print(f"\n\nUPDATING NURSE {nurse_data} by doing POST request to {uri}")

    try:
        # Delete the patient data in the catalog
        response = requests.put(uri, json=nurse_data)
        print(response)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        data = response.json()
        print(data)
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        print(f"\n\nERROR {e}")
        return jsonify({'error': str(e)})

# Function to delete a patient (and its device connector) from the registry system (DELETE REQUEST)
@app.route('/deletePatient', methods=['POST'])
def delete_patient():
    # Get the data from the form
    patient_id = request.form.to_dict()
    patient_id = patient_id['selectedpatient']
    #print("Patient ID:", patient_id)
    conf = read_config()
    # URI to delete data in the catalog
    uri = f"{conf['RegistrySystem']}/{conf['information']['uri']['patient']}?{conf['information']['uri']['delete_patient']}={patient_id}"

    print(f"\n\nDELETING PATIENT {patient_id} by doing DELETE request to {uri}")

    try:
        # Delete the patient data in the catalog
        response = requests.delete(uri)
        print(response)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        data = response.json()
        print(data)
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        print(f"\n\nERROR {e}")
        return jsonify({'error': str(e)})
    
# Function to delete a nurse from the registry system (DELETE REQUEST)
@app.route('/deleteNurse', methods=['POST'])
def delete_nurse():
    # Get the data from the form
    nurse_id = request.form.to_dict()
    nurse_id = nurse_id['selectednurse']
    #print("nurse ID:", nurse_id)
    conf = read_config()
    # URI to delete data in the catalog
    uri = f"{conf['RegistrySystem']}/{conf['information']['uri']['nurse']}?{conf['information']['uri']['delete_nurse']}={nurse_id}"

    print(f"\n\nDELETING NURSE {nurse_id} by doing DELETE request to {uri}")

    try:
        # Delete the patient data in the catalog
        response = requests.delete(uri)
        print(response)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        data = response.json()
        print(data)
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        print(f"\n\nERROR {e}")
        return jsonify({'error': str(e)})
    


if __name__ == '__main__':
    # Define the scheduler to update the configuration file every 5 minutes by doing a PUT request to the registry system
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_config, trigger="interval", seconds=300)
    scheduler.start()
    # Read the configuration file and run the Webpage
    config = read_config()
    app.run(debug=True, port=config["information"]["port"])

    
