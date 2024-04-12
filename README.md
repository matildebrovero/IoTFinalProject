# IoTFinalProject
Final Project for the exam "Programming for IoT applications". Academic Year 2023/2024.

Here is the description of the system implemented in **v1.0.1**

<p align="center">
    <img src="images/FinalProject.svg">
</p>

To install all the packages needed in python you can simple run in *IoTFinalProject* folder the following line:
```bash
pip install requirements.txt
```

The proposed IoT platform provides a service to hospitals, clinics or nursing
homes for continuous monitoring of patients. Data are provided from five sensors
for each patient: an ECG sensor, a blood pressure monitor, a pulse oximeter, a
glucometer and a thermometer. Data are processed and analyzed and then stored in a database. The main feature of the service is to aggregate
the different data in order to provide an overall status of the patient’s health and
in case it becomes critical the service sends a notification to the healthcare
provider. Hence, the healthcare providers can see in detail the evolution of the
data over time through a web page.
The platform as a whole offers uniform interfaces (using both REST and MQTT)
and the data are stored in a database.
To summarize, the main features of this platform will be:

* Monitoring of vital parameters
* Aggregating information to provide a patient’s status
* Sending notification to the nurses in critical cases throug a Telegram Bot
* Providing insights and graphical visualization of vital parameters trough a WebPage

The microservices present in are the following:
* **RegistrySystem** that takes care of updating the Registry System and manage the requests from the other microservices
* **DBwriter** and **DBreader** that compose the DB adaptor microservices which manages the data in the InfluxDB database
* **ECG Analysis** which computes analysis on the raw ecg data to get RR intervals, Heart Rate variability and filters the ECG signal to get a clearer signal
* **DeviceConnector** emulates the sensor linked to each device connector. Each patient has its own device connector with all the sensor mentioned above.
* **Webpage** is a GUI from which nurses and doctors can access to the patients data, can add a patient when a new one is registered to the hospital or delete if the patient is no longer hospitalized.
* **Patient Status** gets all the data from the database as long as information about the patient like its comorbidities and computer trough fuzzy logic rules the current status of the patient (possible one are "very good", "regular" and "bad")
* **Telegram Bot** is a bot that the nurse must start to get an ALERT message when a patient is in a dangerous condition (status equal to "bad"). It can be found at https://t.me/smarthospital_examplebot 

Link to the proposal: https://drive.google.com/file/d/1I2hT3Znlvx2par_VTro0zsUHHKj5O8eV/view?usp=sharing
