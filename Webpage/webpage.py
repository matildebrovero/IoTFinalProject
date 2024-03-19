from flask import Flask, render_template, request, jsonify
import requests
import json

app = Flask(__name__)

# Initial page
@app.route('/')
def index():
    # load the configuration file using a get request to 0.0.0.0:8080/configwebpage
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
    # TODO: cambiare questi dati leggendo dai dati passati da interfaccia grafica
    patientSelected = request.form['patientSelect']
    dataSelected = request.form['dataSelect']
    timeRange = request.form['timeRange']
    print(patientSelected, dataSelected, timeRange)

    # TODO: cambiare l'indirizzo in base al server che ospita il servizio - LEGGERE DA FILE JSON DI CONFIGURAZIONE
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
    new_patient_data = request.form.to_dict()
    # Salvare i dati del nuovo paziente o fare altro con essi
    print("New Patient Data:", new_patient_data)

    #TODO: cambiare l'indirizzo in base al server che ospita il servizio - LEGGERE DA FILE JSON DI CONFIGURAZIONE
    uri = f"http://localhost:8080/patient"
    print(uri)

    try:
        # salvo i pazienti nel server
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
