# IoTFinalProject
Final Project for the exam "Programming for IoT applications". Academic Year 2023/2024.

Here is the description of the system implemented in **v1.0.1**

<p align="center">
    <img src="images/FinalProject.svg">
</p>

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


Link to the proposal: https://drive.google.com/file/d/1I2hT3Znlvx2par_VTro0zsUHHKj5O8eV/view?usp=sharing
