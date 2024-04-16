# IoTFinalProject
Final Project for the exam "Programming for IoT applications". Academic Year 2023/2024.

Here is the description of the system implemented in **v1.0.1**

<p align="center">
    <img src="images/FinalProject.svg">
</p>

After pulling this version (**main** branch) the only thing needed is to execute the following command in the folder *IoTFinalProject*

```bash
docker compose up -d
```

In the branch **develop** you will find files to execute the services locally without docker.

The proposed IoT platform provides a service to hospitals, clinics or nursing
homes for continuous monitoring of patients. Data are collected through a **device** placed on each patient that has five sensors:
- An ECG sensor (single derivation);
- A blood pressure monitor;
- A pulse oximeter;
- A glucometer;
- A thermometer.
Collected data are processed, stored in a database and analyzed. The main feature of the service is to aggregate
the different data in order to offer a comprehensive health assessment of patients. In case of critical status, notifications are sent to the healthcare providers.
In addition to the notifications, healthcare providers can also access a web interface that show in detail the evolution of the
data over time.
The platform as a whole offers uniform interfaces (using both REST and MQTT)
and the data are stored in a database.
To summarize, the main features of this platform will be:

* Monitoring of vital parameters;
* Aggregating information to provide a patient’s status;
* Sending notification to the nurses in critical cases throug a Telegram Bot;
* Providing insights and graphical visualization of vital parameters trough a WebPage.

The microservices present in are the following:
* **RegistrySystem** that takes care of updating the Registry System and manage the requests from the other microservices;
* **DBwriter** and **DBreader** that compose the DB adaptor microservices which manages the data in the InfluxDB database;
* **ECG Analysis** that filter the raw ECG data and compute the Heart Rate Variability and the RR wave;
* **DeviceConnector** emulates the sensor linked to each device connector. Each patient has its own device connector with all the sensor mentioned above;
* **Webpage** is a GUI from which nurses and doctors can access to the patients data, can add a patient when a new one is registered to the hospital or delete if the patient is no longer hospitalized;
* **Patient Status** access the data from the database and computes the current health status of the patient (possible one are "very good", "regular" and "bad"). The status is computed taking into account not only the data but also the patient's comorbidities using fuzzy logic;
* **Telegram Bot** is a bot that the nurse must start to get an ALERT message when a patient is in a dangerous condition (status equal to "bad"). It can be found at https://t.me/smarthospital_examplebot;

Link to the proposal: https://drive.google.com/file/d/1I2hT3Znlvx2par_VTro0zsUHHKj5O8eV/view?usp=sharing
